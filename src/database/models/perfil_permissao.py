"""Tabela de associação N:N entre :class:`Perfil` e :class:`Permissao`.

Modelada como :class:`sqlalchemy.Table` (estilo Core), padrão recomendado
pelo SQLAlchemy 2.0 para tabelas de junção puras — sem atributos próprios
além das FKs. Se um dia a junção ganhar colunas extras (ex.: ``criado_em``,
``criado_por``), promove-se para um model declarativo regular.

A tabela é referenciada via ``secondary=perfil_permissoes`` no
:func:`relationship` dos models ``Perfil`` e ``Permissao``.
"""

from sqlalchemy import Column, ForeignKey, Integer, Table

from src.database.models.base import Base


perfil_permissoes: Table = Table(
    "perfil_permissoes",
    Base.metadata,
    Column(
        "perfil_id",
        Integer,
        ForeignKey("perfis.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permissao_id",
        Integer,
        ForeignKey("permissoes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
