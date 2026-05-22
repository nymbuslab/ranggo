"""Repositório de :class:`Categoria` — CRUD puro sobre ``categorias``.

Camada "burra" de acesso a dados: não valida regras de negócio, não
gerencia ciclo de vida de :class:`Session` e não conhece UI nem
serviços. A :class:`Session` é injetada pelo caller (geralmente um
service) via construtor.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.categoria import Categoria


class CategoriaRepository:
    """Acesso a dados da entidade :class:`Categoria`."""

    def __init__(self, session: Session) -> None:
        """Recebe a :class:`Session` que será usada por todas as operações.

        Args:
            session: Sessão SQLAlchemy ativa, gerenciada pelo caller.
        """
        self._session = session

    def listar(self) -> list[Categoria]:
        """Retorna todas as categorias ordenadas por nome."""
        stmt = select(Categoria).order_by(Categoria.nome)
        return list(self._session.execute(stmt).scalars().all())

    def buscar_por_id(self, categoria_id: int) -> Categoria | None:
        """Busca categoria pelo id (retorna ``None`` se não existir)."""
        return self._session.get(Categoria, categoria_id)

    def buscar_por_nome(self, nome: str) -> Categoria | None:
        """Busca categoria pelo nome (case-sensitive, retorna ``None`` se não existir)."""
        stmt = select(Categoria).where(Categoria.nome == nome)
        return self._session.execute(stmt).scalar_one_or_none()

    def criar(self, dados: dict) -> Categoria:
        """Cria nova categoria a partir de um dicionário de campos."""
        categoria = Categoria(**dados)
        self._session.add(categoria)
        self._session.flush()
        self._session.refresh(categoria)
        return categoria

    def atualizar(self, categoria_id: int, dados: dict) -> Categoria:
        """Atualiza os campos da categoria identificada por ``categoria_id``.

        Raises:
            ValueError: Se ``categoria_id`` não existe.
        """
        categoria = self._session.get(Categoria, categoria_id)
        if categoria is None:
            raise ValueError(f"Categoria id={categoria_id} nao encontrada.")
        for campo, valor in dados.items():
            setattr(categoria, campo, valor)
        self._session.flush()
        return categoria

    def deletar(self, categoria_id: int) -> None:
        """Remove fisicamente (hard delete) a categoria.

        Soft delete (``ativo=False``) é responsabilidade do service. Este
        método existe para casos administrativos/migração e não é exposto
        pela UI.
        """
        categoria = self._session.get(Categoria, categoria_id)
        if categoria is not None:
            self._session.delete(categoria)
            self._session.flush()
