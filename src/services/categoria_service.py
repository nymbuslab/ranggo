"""Service de gestão de Categorias.

Camada de regras de negócio sobre :class:`Categoria`. Centraliza tudo
que o repository (burro) não pode decidir sozinho:

* Validação de nome obrigatório (não-vazio após ``strip``).
* Validação de nome único (não permite duplicar — mesmo caso de mudança
  de caixa exata levanta :class:`NomeDuplicadoError`).
* **Soft delete**: desativar é ``ativo=False``, nunca ``DELETE`` físico.

Service **não** conhece Flet/UI e **não** comita: a :class:`Session` é
injetada pelo caller, que também é responsável por ``commit``/``rollback``
(normalmente via ``with get_session() as session``).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.categoria import Categoria
from src.repositories.categoria_repository import CategoriaRepository
from src.utils.exceptions import NomeDuplicadoError


class CategoriaService:
    """Service para gestão de Categorias.

    Aplica regras de negócio:
        * Nome obrigatório (não-vazio após ``strip``).
        * Nome UNIQUE (:class:`NomeDuplicadoError` em conflito).
        * Soft delete via ``ativo=False`` (nunca hard delete via UI).
    """

    def __init__(self, session: Session) -> None:
        """Recebe a :class:`Session` usada por todas as operações.

        Args:
            session: Sessão SQLAlchemy ativa, gerenciada pelo caller.
        """
        self._session = session
        self._repo = CategoriaRepository(session)

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def listar(self, incluir_inativas: bool = False) -> list[Categoria]:
        """Lista categorias ordenadas por nome.

        Args:
            incluir_inativas: Se ``True``, retorna inclusive as com
                ``ativo=False``. Default ``False`` — listagem normal de
                operação esconde inativas, e a UI controla via toggle.

        Returns:
            Lista de :class:`Categoria`.
        """
        stmt = select(Categoria).order_by(Categoria.nome)
        if not incluir_inativas:
            stmt = stmt.where(Categoria.ativo.is_(True))
        return list(self._session.execute(stmt).scalars().all())

    def buscar_por_id(self, categoria_id: int) -> Categoria | None:
        """Busca categoria por id (retorna ``None`` se não existir)."""
        return self._repo.buscar_por_id(categoria_id)

    # ------------------------------------------------------------------
    # Criação
    # ------------------------------------------------------------------

    def criar(self, nome: str, descricao: str | None = None) -> Categoria:
        """Cria nova categoria.

        Validações (na ordem):
            1. Nome obrigatório (após ``strip``).
            2. Nome único (não existe outra categoria com o mesmo nome).

        Args:
            nome: Nome da categoria (será trim).
            descricao: Descrição opcional (será trim; vazio vira ``None``).

        Returns:
            :class:`Categoria` criada.

        Raises:
            ValueError: Se ``nome`` é vazio após ``strip``.
            NomeDuplicadoError: Se já existe categoria com esse nome.
        """
        nome = nome.strip()
        if not nome:
            raise ValueError("Nome eh obrigatorio.")

        if self._repo.buscar_por_nome(nome) is not None:
            raise NomeDuplicadoError(
                f"Ja existe uma categoria com nome '{nome}'."
            )

        descricao_limpa = descricao.strip() if descricao else None
        if descricao_limpa == "":
            descricao_limpa = None

        return self._repo.criar({
            "nome": nome,
            "descricao": descricao_limpa,
            "ativo": True,
        })

    # ------------------------------------------------------------------
    # Atualização
    # ------------------------------------------------------------------

    def atualizar(
        self,
        categoria_id: int,
        nome: str,
        descricao: str | None,
        ativo: bool,
    ) -> Categoria:
        """Atualiza dados da categoria.

        Args:
            categoria_id: Id da categoria a atualizar.
            nome: Novo nome (será trim).
            descricao: Nova descrição (será trim; vazio vira ``None``).
            ativo: Novo status.

        Returns:
            :class:`Categoria` atualizada.

        Raises:
            ValueError: Se ``categoria_id`` não existe ou ``nome`` vazio.
            NomeDuplicadoError: Se já existe OUTRA categoria com esse nome.
        """
        nome = nome.strip()
        if not nome:
            raise ValueError("Nome eh obrigatorio.")

        categoria = self._repo.buscar_por_id(categoria_id)
        if categoria is None:
            raise ValueError(f"Categoria id={categoria_id} nao encontrada.")

        # Conflito de nome — excluindo a própria categoria.
        existente = self._repo.buscar_por_nome(nome)
        if existente is not None and existente.id != categoria_id:
            raise NomeDuplicadoError(
                f"Ja existe outra categoria com nome '{nome}'."
            )

        descricao_limpa = descricao.strip() if descricao else None
        if descricao_limpa == "":
            descricao_limpa = None

        return self._repo.atualizar(categoria_id, {
            "nome": nome,
            "descricao": descricao_limpa,
            "ativo": ativo,
        })

    def desativar(self, categoria_id: int) -> None:
        """Soft delete: marca ``ativo=False`` preservando o registro.

        Atalho para o botão "Desativar" da listagem. Categoria não tem
        regras de guarda como Usuario (auto-desativação, último admin) —
        é só flag de status.

        Args:
            categoria_id: Id da categoria a desativar.

        Raises:
            ValueError: Se ``categoria_id`` não existe.
        """
        categoria = self._repo.buscar_por_id(categoria_id)
        if categoria is None:
            raise ValueError(f"Categoria id={categoria_id} nao encontrada.")
        self.atualizar(
            categoria_id,
            categoria.nome,
            categoria.descricao,
            False,
        )
