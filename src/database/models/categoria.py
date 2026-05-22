"""Model :class:`Categoria` — agrupa Produtos, Insumos e Pratos.

Cadastro básico da Fase 2. Toda Categoria tem soft delete (``ativo=False``).
Nome é UNIQUE no banco para evitar duplicação acidental.

Categoria é fundação da Fase 2: Produto, Insumo e Prato referenciam
``categoria_id``. Soft delete preserva integridade referencial — quando
um cadastro filho ainda aponta para uma categoria desativada, a UI
mostra o nome dimmed mas o histórico continua íntegro.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models.base import Base


class Categoria(Base):
    """Categoria de cadastro: agrupa Produtos, Insumos e Pratos."""

    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
