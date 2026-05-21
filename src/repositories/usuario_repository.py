"""Repositório de :class:`Usuario` — CRUD puro sobre a tabela ``usuarios``.

Camada "burra" de acesso a dados: não valida regras de negócio, não
faz hash de senha (responsabilidade do ``AuthService``, Passo 3) e não
conhece UI. A :class:`Session` é injetada pelo caller via construtor.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.database.models.usuario import Usuario


class UsuarioRepository:
    """Acesso a dados da entidade :class:`Usuario`."""

    def __init__(self, session: Session) -> None:
        """Recebe a :class:`Session` que será usada por todas as operações.

        Args:
            session: Sessão SQLAlchemy ativa, gerenciada pelo caller.
        """
        self._session = session

    def listar(self) -> list[Usuario]:
        """Retorna todos os usuários cadastrados (ativos e inativos)."""
        stmt = select(Usuario)
        return list(self._session.execute(stmt).scalars().all())

    def listar_ativos(self) -> list[Usuario]:
        """Lista apenas usuários com ``ativo=True``.

        Útil para a tela de listagem (Passo 9), que esconde inativos por
        padrão. Inativos continuam acessíveis via :meth:`listar` quando
        for necessário exibir o histórico completo.

        Returns:
            Lista de :class:`Usuario` com ``ativo=True``.
        """
        stmt = select(Usuario).where(Usuario.ativo.is_(True))
        return list(self._session.execute(stmt).scalars().all())

    def buscar_por_id(self, id: int) -> Usuario | None:
        """Busca um usuário pelo id (retorna ``None`` se não existir)."""
        return self._session.get(Usuario, id)

    def buscar_por_login(self, login: str) -> Usuario | None:
        """Busca usuário pelo login (case-sensitive).

        Método-chave da autenticação: é a primeira query executada pelo
        :class:`AuthService` (Passo 3) no fluxo de login. ``None`` quando
        o login não existe — o service decide a mensagem ("usuário ou
        senha incorretos") sem distinguir login inválido de senha errada.

        Carrega ``perfil`` via ``joinedload`` para que a UI possa exibir
        ``usuario.perfil.nome`` depois que a :class:`Session` do login já
        foi fechada — sem isso, qualquer acesso ao relationship dispara
        ``DetachedInstanceError`` (a UI do shell autenticado lê o usuário
        da :mod:`src.services.sessao`, que mantém o objeto vivo mas sem
        sessão anexada).

        Args:
            login: Login exato (case-sensitive) do usuário.

        Returns:
            O :class:`Usuario` correspondente (com ``perfil`` já carregado)
            ou ``None`` se não existir.
        """
        stmt = (
            select(Usuario)
            .options(joinedload(Usuario.perfil))
            .where(Usuario.login == login)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def criar(self, dados: dict) -> Usuario:
        """Cria um novo usuário a partir de um dicionário de campos.

        O dicionário deve conter ``senha_hash`` já calculado pelo
        :class:`AuthService` — repositório não conhece ``bcrypt``.
        """
        usuario = Usuario(**dados)
        self._session.add(usuario)
        self._session.flush()
        return usuario

    def atualizar(self, id: int, dados: dict) -> Usuario:
        """Atualiza os campos do usuário identificado por ``id``."""
        usuario = self._session.get(Usuario, id)
        if usuario is None:
            raise ValueError(f"Usuario id={id} não encontrado")
        for campo, valor in dados.items():
            setattr(usuario, campo, valor)
        self._session.flush()
        return usuario

    def deletar(self, id: int) -> None:
        """Remove fisicamente o usuário identificado por ``id`` (hard delete).

        Soft delete (marcar inativo) é responsabilidade do service: o
        caso de uso normal de "desativar usuário" deve chamar
        ``atualizar(id, {"ativo": False})`` para preservar auditoria de
        vendas/comandas vinculadas. Este método apaga de fato e só deve
        ser usado em casos excepcionais (ex.: usuário criado por engano,
        sem nenhuma movimentação vinculada).

        Args:
            id: Identificador do usuário a remover.

        Raises:
            ValueError: Se o ``id`` não existir.
        """
        usuario = self._session.get(Usuario, id)
        if usuario is None:
            raise ValueError(f"Usuario id={id} não encontrado")
        self._session.delete(usuario)
        self._session.flush()
