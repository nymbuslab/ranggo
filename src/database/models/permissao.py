"""Model :class:`Permissao` — ação granular concedida via :class:`Perfil`.

Cada permissão é identificada por um ``codigo`` curto, estável e usado
no código de checagem (ex.: ``aplicar_desconto``, ``cancelar_venda``,
``editar_cadastros``). O ``codigo`` é a chave funcional — não usar o
``id`` em comparações de regra de negócio.

Relacionamentos:
    * **perfis** — N:N com :class:`Perfil` (via ``perfil_permissoes``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base
from src.database.models.perfil_permissao import perfil_permissoes

if TYPE_CHECKING:
    from src.database.models.perfil import Perfil


class Permissao(Base):
    """Permissão atômica do sistema (ex.: ``aplicar_desconto``)."""

    __tablename__ = "permissoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    descricao: Mapped[str] = mapped_column(String(200))

    perfis: Mapped[list[Perfil]] = relationship(
        secondary=perfil_permissoes,
        back_populates="permissoes",
    )
