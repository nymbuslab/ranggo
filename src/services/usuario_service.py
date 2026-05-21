"""Service de gestão de usuários do sistema.

Camada de regras de negócio sobre :class:`Usuario`, orquestrando o
:class:`UsuarioRepository`, o :class:`PerfilRepository` e o
:class:`AuthService`. Centraliza tudo que o repository (burro) não pode
decidir sozinho:

* Validação de login único antes de criar.
* Hash de senha via :class:`AuthService` — repository não conhece bcrypt.
* Validação de ``perfil_id`` (FK existe).
* **Soft delete**: desativar é ``ativo=False``, não ``DELETE``.
* Proteção do **último Admin ativo**: não permite deixar o sistema sem
  ninguém capaz de administrar.
* Proteção de **auto-desativação**: o usuário logado não pode desativar
  a própria conta (precisa de outro Admin).

Service **não** conhece Flet/UI e **não** comita: a :class:`Session` é
injetada pelo caller, que também é responsável por ``commit``/``rollback``
(normalmente via ``with get_session() as session``).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.database.models.perfil import Perfil
from src.database.models.usuario import Usuario
from src.repositories.perfil_repository import PerfilRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services import sessao
from src.services.auth_service import AuthService
from src.utils.exceptions import (
    NomeDuplicadoError,
    PermissaoNegadaError,
)


# Nome do perfil "Admin" — usado nas guardas de último admin ativo.
# Em string literal porque o seed (Passo 5) também usa essa string.
# Quando virar enum/constante centralizada (Fase 2+), substituir.
_PERFIL_ADMIN: str = "Admin"


class UsuarioService:
    """Service para gestão de usuários do sistema.

    Orquestra :class:`UsuarioRepository`, :class:`PerfilRepository` e
    :class:`AuthService`. Service **não** conhece Flet/UI. Service
    **não** comita — o caller (UI) é responsável.
    """

    def __init__(self, session: Session) -> None:
        """Recebe a :class:`Session` usada por todas as operações.

        Args:
            session: Sessão SQLAlchemy ativa, gerenciada pelo caller.
        """
        self._session = session
        self._repo_usuario = UsuarioRepository(session)
        self._repo_perfil = PerfilRepository(session)
        self._auth = AuthService(session)

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def listar(self, incluir_inativos: bool = False) -> list[Usuario]:
        """Lista usuários com ``perfil`` eager-loaded.

        Args:
            incluir_inativos: Se ``True``, retorna inclusive os com
                ``ativo=False``. Default ``False`` (lista normal de
                operação — a tela de Usuários esconde inativos por padrão).

        Returns:
            Lista de :class:`Usuario` com ``perfil`` já carregado, segura
            para uso fora da :class:`Session` (sem ``DetachedInstanceError``
            quando a UI exibir ``usuario.perfil.nome``).
        """
        stmt = select(Usuario).options(joinedload(Usuario.perfil))
        if not incluir_inativos:
            stmt = stmt.where(Usuario.ativo.is_(True))
        return list(self._session.execute(stmt).scalars().all())

    def buscar_por_id(self, usuario_id: int) -> Usuario | None:
        """Busca usuário por id com ``perfil`` eager-loaded.

        Args:
            usuario_id: Identificador do usuário.

        Returns:
            :class:`Usuario` com ``perfil`` carregado, ou ``None`` se não
            existir.
        """
        stmt = (
            select(Usuario)
            .options(joinedload(Usuario.perfil))
            .where(Usuario.id == usuario_id)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    # ------------------------------------------------------------------
    # Criação
    # ------------------------------------------------------------------

    def criar(
        self,
        nome: str,
        login: str,
        senha: str,
        perfil_id: int,
    ) -> Usuario:
        """Cria novo usuário com senha hasheada.

        Validações (na ordem):
            1. Login único (não pode duplicar).
            2. Perfil existe.
            3. Senha atende à política mínima (≥ 6 chars — via
               :meth:`AuthService.criar_hash`).

        Args:
            nome: Nome completo do usuário.
            login: Identificador de login (único, case-sensitive).
            senha: Senha em texto plano (será hasheada com bcrypt).
            perfil_id: Id do perfil (Admin/Gerente/Caixa).

        Returns:
            :class:`Usuario` criado, com ``id`` e ``criado_em`` populados.

        Raises:
            NomeDuplicadoError: Se ``login`` já existe.
            ValueError: Se ``perfil_id`` não existe. Roteiro futuro:
                substituir por ``ReferenciaInvalidaError`` quando ela
                for criada (ver ``src/utils/exceptions.py``).
            SenhaFracaError: Se ``senha`` tem menos de 6 caracteres
                (propagada de :meth:`AuthService.criar_hash`).
        """
        if self._repo_usuario.buscar_por_login(login) is not None:
            raise NomeDuplicadoError(
                f"Ja existe usuario com login '{login}'."
            )

        if self._repo_perfil.buscar_por_id(perfil_id) is None:
            raise ValueError(f"Perfil id={perfil_id} nao encontrado.")

        senha_hash = self._auth.criar_hash(senha)

        return self._repo_usuario.criar(
            {
                "nome": nome,
                "login": login,
                "senha_hash": senha_hash,
                "perfil_id": perfil_id,
                "ativo": True,
            }
        )

    # ------------------------------------------------------------------
    # Atualização
    # ------------------------------------------------------------------

    def atualizar(
        self,
        usuario_id: int,
        nome: str,
        perfil_id: int,
        ativo: bool,
    ) -> Usuario:
        """Atualiza dados do usuário.

        **Não** atualiza ``login`` (chave histórica) nem ``senha`` (use
        :meth:`trocar_senha`).

        Guardas ao desativar (``ativo=False``):
            * **Auto-desativação**: se ``usuario_id`` é o usuário logado
              em :mod:`src.services.sessao`, levanta
              :class:`PermissaoNegadaError`. Outro Admin deve fazer.
            * **Último Admin ativo**: se o usuário sendo desativado tem
              perfil Admin e é o último Admin ativo do sistema, levanta
              :class:`PermissaoNegadaError`. Garante que nunca sobre o
              sistema sem ninguém capaz de administrar.

        Args:
            usuario_id: Id do usuário a atualizar.
            nome: Novo nome.
            perfil_id: Novo perfil.
            ativo: Novo status.

        Returns:
            :class:`Usuario` atualizado.

        Raises:
            ValueError: ``usuario_id`` ou ``perfil_id`` inválido.
            PermissaoNegadaError: Auto-desativação ou desativação do
                último Admin ativo.
        """
        usuario = self.buscar_por_id(usuario_id)
        if usuario is None:
            raise ValueError(f"Usuario id={usuario_id} nao encontrado.")

        if self._repo_perfil.buscar_por_id(perfil_id) is None:
            raise ValueError(f"Perfil id={perfil_id} nao encontrado.")

        # Guardas só disparam ao desativar.
        if not ativo:
            atual = sessao.usuario_atual()
            if atual is not None and atual.id == usuario_id:
                raise PermissaoNegadaError(
                    "Voce nao pode desativar a propria conta. "
                    "Peca a outro Admin."
                )

            # Último Admin: verificar pelo perfil ATUAL do usuário
            # (antes da edição), porque a guarda existe para impedir que
            # o sistema fique sem Admin — se ele JÁ é Admin e está sendo
            # desativado, precisa contar quantos sobram.
            if usuario.perfil.nome == _PERFIL_ADMIN:
                stmt = (
                    select(func.count(Usuario.id))
                    .join(Usuario.perfil)
                    .where(Perfil.nome == _PERFIL_ADMIN)
                    .where(Usuario.ativo.is_(True))
                    .where(Usuario.id != usuario_id)
                )
                admins_restantes = self._session.execute(stmt).scalar() or 0
                if admins_restantes == 0:
                    raise PermissaoNegadaError(
                        "Nao eh possivel desativar o ultimo Admin ativo "
                        "do sistema."
                    )

        return self._repo_usuario.atualizar(
            usuario_id,
            {
                "nome": nome,
                "perfil_id": perfil_id,
                "ativo": ativo,
            },
        )

    def trocar_senha(self, usuario_id: int, nova_senha: str) -> None:
        """Troca senha do usuário (Admin pode trocar qualquer senha).

        Valida senha mínima (≥ 6 chars) via :meth:`AuthService.criar_hash`.

        Args:
            usuario_id: Id do usuário.
            nova_senha: Nova senha em texto plano (será hasheada).

        Raises:
            ValueError: ``usuario_id`` não existe.
            SenhaFracaError: Senha não atende à política mínima
                (propagada de :meth:`AuthService.criar_hash`).
        """
        usuario = self._repo_usuario.buscar_por_id(usuario_id)
        if usuario is None:
            raise ValueError(f"Usuario id={usuario_id} nao encontrado.")

        # Alteração em objeto persistente já dentro da session — o flush
        # detecta automaticamente e gera o UPDATE no commit. Não precisa
        # chamar repository.atualizar.
        usuario.senha_hash = self._auth.criar_hash(nova_senha)
        self._session.flush()

    def desativar(self, usuario_id: int) -> None:
        """Soft delete: marca ``ativo=False`` preservando nome e perfil.

        Atalho para o botão "Excluir" da listagem de Usuários — desativa
        sem trazer o formulário completo. Aplica as mesmas guardas de
        :meth:`atualizar` (auto-desativação e último Admin).

        Args:
            usuario_id: Id do usuário a desativar.

        Raises:
            ValueError: ``usuario_id`` não existe.
            PermissaoNegadaError: Auto-desativação ou último Admin
                (propagada de :meth:`atualizar`).
        """
        usuario = self._repo_usuario.buscar_por_id(usuario_id)
        if usuario is None:
            raise ValueError(f"Usuario id={usuario_id} nao encontrado.")
        self.atualizar(usuario_id, usuario.nome, usuario.perfil_id, False)
