"""Model :class:`Fornecedor` — empresa ou pessoa que fornece insumos/produtos.

Cadastro basico da Fase 2. Soft delete via ``ativo=False``. Apenas
``nome`` eh obrigatorio. ``cnpj`` eh UNIQUE quando preenchido (vazio
pode duplicar — SQLite permite multiplos NULLs em coluna UNIQUE
naturalmente, nao precisa cuidado extra no schema). Endereco e email
NAO sao armazenados (decisao Fase 2 #6).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models.base import Base


class Fornecedor(Base):
    """Fornecedor de insumos/produtos para o restaurante."""

    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(
        String(14), unique=True, nullable=True
    )
    telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contato: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Fornecedor id={self.id} nome={self.nome!r} "
            f"ativo={self.ativo}>"
        )
