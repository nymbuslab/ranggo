"""Model :class:`Usuario` — operador autenticável do sistema.

Cada usuário tem exatamente um :class:`Perfil`, que por sua vez carrega
um conjunto de :class:`Permissao`. A senha **nunca** é persistida em
texto claro: o campo :attr:`senha_hash` armazena o digest gerado por
``bcrypt`` (Fase 1 implementa o ``AuthService``).

Notas:
    * ``senha_hash`` é mascarado no ``__repr__`` via
      ``__repr_exclude__`` para evitar vazamento em logs.
    * ``criado_em`` é gravado timezone-aware em UTC; a UI converte
      para o fuso local na exibição.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.perfil import Perfil


class Usuario(Base):
    """Operador do sistema (caixa, gerente, admin)."""

    __tablename__ = "usuarios"

    # ``senha_hash`` não aparece em repr/log — evita vazamento acidental.
    __repr_exclude__: ClassVar[frozenset[str]] = frozenset({"senha_hash"})

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    login: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(100))
    perfil_id: Mapped[int] = mapped_column(ForeignKey("perfis.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    perfil: Mapped[Perfil] = relationship(back_populates="usuarios")
