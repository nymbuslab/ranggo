"""Model :class:`Perfil` — agrupa permissões concedidas a usuários.

No Ranggo existem três perfis padrão (criados via seed na Fase 1):
``Admin``, ``Gerente`` e ``Caixa``. Cada perfil reúne um conjunto de
:class:`Permissao` (ex.: ``aplicar_desconto``, ``editar_cadastros``)
através da tabela de associação ``perfil_permissoes``.

Relacionamentos:
    * **permissoes** — N:N com :class:`Permissao` (via
      ``perfil_permissoes``).
    * **usuarios** — 1:N com :class:`Usuario` (cada usuário tem
      exatamente um perfil).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base
from src.database.models.perfil_permissao import perfil_permissoes

if TYPE_CHECKING:
    from src.database.models.permissao import Permissao
    from src.database.models.usuario import Usuario


class Perfil(Base):
    """Perfil de acesso atribuído a um :class:`Usuario`."""

    __tablename__ = "perfis"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    descricao: Mapped[str | None] = mapped_column(String(200))

    permissoes: Mapped[list[Permissao]] = relationship(
        secondary=perfil_permissoes,
        back_populates="perfis",
    )
    usuarios: Mapped[list[Usuario]] = relationship(back_populates="perfil")
