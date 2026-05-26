"""Repositorio de :class:`Fornecedor` — CRUD puro sobre ``fornecedores``.

Camada "burra" de acesso a dados: nao valida regras de negocio, nao
gerencia ciclo de vida de :class:`Session` e nao conhece UI nem
servicos. A :class:`Session` eh injetada pelo caller (geralmente um
service) via construtor.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.fornecedor import Fornecedor


class FornecedorRepository:
    """Acesso a dados da entidade :class:`Fornecedor`."""

    def __init__(self, session: Session) -> None:
        """Recebe a :class:`Session` que sera usada por todas as operacoes.

        Args:
            session: Sessao SQLAlchemy ativa, gerenciada pelo caller.
        """
        self._session = session

    def listar(self) -> list[Fornecedor]:
        """Retorna todos os fornecedores ordenados por nome."""
        stmt = select(Fornecedor).order_by(Fornecedor.nome)
        return list(self._session.execute(stmt).scalars().all())

    def buscar_por_id(self, fornecedor_id: int) -> Fornecedor | None:
        """Busca fornecedor pelo id (retorna ``None`` se nao existir)."""
        return self._session.get(Fornecedor, fornecedor_id)

    def buscar_por_cnpj(self, cnpj_normalizado: str) -> Fornecedor | None:
        """Busca fornecedor pelo CNPJ ja normalizado (14 digitos puros).

        Retorna ``None`` se nao existir. Nao busca por nome — nome nao
        eh unique para Fornecedor (decisao Fase 2 #9).
        """
        stmt = select(Fornecedor).where(Fornecedor.cnpj == cnpj_normalizado)
        return self._session.execute(stmt).scalar_one_or_none()

    def criar(self, dados: dict) -> Fornecedor:
        """Cria novo fornecedor a partir de um dicionario de campos."""
        fornecedor = Fornecedor(**dados)
        self._session.add(fornecedor)
        self._session.flush()
        self._session.refresh(fornecedor)
        return fornecedor

    def atualizar(self, fornecedor_id: int, dados: dict) -> Fornecedor:
        """Atualiza os campos do fornecedor identificado por ``fornecedor_id``.

        Raises:
            ValueError: Se ``fornecedor_id`` nao existe.
        """
        fornecedor = self._session.get(Fornecedor, fornecedor_id)
        if fornecedor is None:
            raise ValueError(f"Fornecedor id={fornecedor_id} nao encontrado.")
        for campo, valor in dados.items():
            setattr(fornecedor, campo, valor)
        self._session.flush()
        return fornecedor

    def deletar(self, fornecedor_id: int) -> None:
        """Remove fisicamente (hard delete) o fornecedor.

        Soft delete (``ativo=False``) eh responsabilidade do service.
        Este metodo existe para casos administrativos/migracao e nao eh
        exposto pela UI.
        """
        fornecedor = self._session.get(Fornecedor, fornecedor_id)
        if fornecedor is not None:
            self._session.delete(fornecedor)
            self._session.flush()
