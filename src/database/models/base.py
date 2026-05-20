"""Classe base do ORM e configuração centralizada de metadata.

Este módulo concentra a única instância de :class:`MetaData` do projeto.
Toda entidade persistida (Usuario, Perfil, Categoria, Produto, ...) deve
herdar de :class:`Base` para compartilhar essa metadata — caso contrário
``Base.metadata.create_all()`` não enxergará a tabela.

Configurações principais:

* **Naming convention** das constraints e índices: definida no padrão
  recomendado pelo SQLAlchemy 2.0
  (`docs.sqlalchemy.org/en/20/core/constraints.html`). Garante nomes
  determinísticos para PK, FK, UNIQUE, CHECK e índices — essencial para
  evitar dor em migrações futuras (renomear constraint anônimo gerado
  pelo SQLite vs por outro backend é um pesadelo).
* ``__repr__`` padrão herdado: itera sobre as colunas mapeadas e imprime
  algo como ``Usuario(id=1, nome='Joao')``. Facilita debug e logs.
* ``__repr_exclude__`` permite a cada subclasse omitir campos sensíveis
  do ``repr`` (ex.: ``Usuario.__repr_exclude__ = frozenset({"senha_hash"})``).

Notas:
    * Esta é uma classe **abstrata** — não declara ``__tablename__``.
      Cada model concreto define o seu em ``src/database/models/<entidade>.py``.
    * Não importe nada de models específicos aqui: este módulo deve ser
      o ponto mais "baixo" da hierarquia de imports do pacote ``database``.
"""

from typing import ClassVar

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


# Convenção de nomes para constraints e índices.
# Padrão oficial documentado em docs.sqlalchemy.org/en/20/core/constraints.html.
# Os tokens disponíveis (column_0_label, table_name, constraint_name, etc.)
# são expandidos automaticamente pelo SQLAlchemy quando o objeto é criado
# sem ``name=`` explícito.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Classe base declarativa de todos os models do Ranggo.

    Todos os models persistidos no SQLite devem herdar desta classe
    para compartilhar a mesma :class:`MetaData` — única forma de
    ``Base.metadata.create_all(engine)`` enxergar a tabela.

    Subclasses devem definir:
        * ``__tablename__``
        * Colunas com :func:`sqlalchemy.orm.mapped_column` (estilo 2.0)
        * Quando necessário, ``__table_args__`` para constraints
          compostas (UNIQUE multi-coluna, CHECK, etc.).
        * Opcionalmente ``__repr_exclude__`` para esconder campos
          sensíveis do ``repr`` (ex.: senha_hash, tokens).
    """

    # MetaData compartilhada com naming convention aplicada.
    # Toda PK/FK/UQ/CHECK/Index criado sem ``name=`` explícito recebe
    # nome determinístico baseado nos templates de NAMING_CONVENTION.
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Conjunto de nomes de colunas a omitir no __repr__.
    # Vazio por padrão; subclasses sobrescrevem para mascarar campos
    # sensíveis. Use ``frozenset`` para evitar mutação acidental.
    __repr_exclude__: ClassVar[frozenset[str]] = frozenset()

    def __repr__(self) -> str:
        """Representação padrão para debug.

        Itera sobre as colunas mapeadas via ``__mapper__.columns`` e
        produz uma string no formato ``ClasseModel(col1=valor1, col2='valor2', ...)``.
        Colunas listadas em ``__repr_exclude__`` aparecem com o valor
        mascarado como ``'<oculto>'`` — fica explícito que o campo
        existe sem vazar o conteúdo.

        Returns:
            String legível com nome da classe e valores (ou máscara)
            das colunas.
        """
        # ``__mapper__`` existe em qualquer subclasse mapeada do
        # DeclarativeBase. Não chamamos getattr nas relations pra evitar
        # disparar lazy-loads acidentais durante o repr.
        excluidas = self.__repr_exclude__
        partes: list[str] = []
        for col in self.__mapper__.columns:
            if col.key in excluidas:
                partes.append(f"{col.key}='<oculto>'")
            else:
                partes.append(f"{col.key}={getattr(self, col.key)!r}")
        return f"{self.__class__.__name__}({', '.join(partes)})"
