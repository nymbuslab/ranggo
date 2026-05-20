"""Model :class:`UnidadeMedida` — unidades de medida fixas do sistema.

Cadastro **fixo**, populado via ``seed.py`` na inicialização do banco:
``UN``, ``KG``, ``G``, ``L``, ``ML``. Insumos e produtos vendidos a peso
referenciam essa tabela.

A ``sigla`` é a chave funcional usada em UI e relatórios; o ``id`` é
estritamente referência de FK. Não criar/remover linhas em runtime —
o conjunto é estável durante toda a vida do sistema.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models.base import Base


class UnidadeMedida(Base):
    """Unidade de medida (UN, KG, G, L, ML)."""

    __tablename__ = "unidades_medida"

    id: Mapped[int] = mapped_column(primary_key=True)
    sigla: Mapped[str] = mapped_column(String(5), unique=True)
    descricao: Mapped[str] = mapped_column(String(40))
