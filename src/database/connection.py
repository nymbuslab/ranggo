"""Conexão SQLite, sessions e inicialização do banco do Ranggo.

Ponto único de configuração da camada de persistência:

* :data:`engine` — engine SQLAlchemy compartilhada, com PRAGMA
  ``foreign_keys=ON`` ativado em cada conexão.
* :data:`SessionLocal` — factory de :class:`Session` usada por
  repositories e services.
* :func:`get_session` — context manager que abre/comita/rollback/fecha
  sessions de forma segura.
* :func:`init_db` — cria as tabelas no SQLite (idempotente).

Decisões importantes:

* **Pool ``StaticPool``**: app desktop single-process; faz sentido
  compartilhar uma única conexão entre threads do Flet em vez de abrir
  várias (SQLite serializa escritas de qualquer jeito, e múltiplas
  conexões só atrapalhariam).
* **``check_same_thread=False``**: Flet executa callbacks em threads
  variáveis. Sem isso, qualquer acesso ao banco fora da thread que
  criou a conexão dispara erro do ``sqlite3``. **Importante**: cada
  operação ainda deve abrir sua própria :class:`Session` via
  :func:`get_session` — não compartilhe instâncias de ``Session`` entre
  threads.
* **PRAGMA ``foreign_keys=ON``**: o SQLite desativa FKs por padrão. Sem
  esse pragma, ``ondelete="CASCADE"`` definido nos models é ignorado
  silenciosamente.
* **``expire_on_commit=False``**: após ``session.commit()`` os objetos
  permanecem utilizáveis sem reload automático — em UI desktop queremos
  exibir o objeto recém-salvo sem disparar nova query.

``init_db()`` **não** é chamado no nível do módulo. ``main.py`` é
responsável por invocá-lo no startup.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import config


# URL de conexão no formato esperado pelo SQLAlchemy.
# 3 barras + path relativo (ex.: "sqlite:///data/ranggo.db").
_DB_URL = f"sqlite:///{config.DB_PATH}"


engine: Engine = create_engine(
    _DB_URL,
    echo=config.SQL_ECHO,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _ativar_foreign_keys(dbapi_connection, connection_record) -> None:
    """Ativa PRAGMA ``foreign_keys=ON`` em cada conexão criada.

    Necessário para que ``ondelete="CASCADE"`` (e demais constraints
    referenciais) sejam realmente aplicados pelo SQLite.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Factory de sessions. ``expire_on_commit=False`` evita reload automático
# de atributos após commit — importante em UI desktop, onde queremos
# exibir o objeto recém-salvo sem disparar nova query.
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Iterator[Session]:
    """Context manager para uso seguro de :class:`Session`.

    Abre uma sessão, faz ``commit`` no sucesso, ``rollback`` em exceção
    (com re-raise) e ``close`` em qualquer caso. Cada operação no banco
    deve abrir sua própria session — nunca compartilhar instâncias entre
    threads.

    Example:
        >>> from src.database.connection import get_session
        >>> from src.database.models import Usuario
        >>> with get_session() as session:
        ...     usuario = session.get(Usuario, 1)

    Yields:
        :class:`Session` pronta para uso.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Cria as tabelas do Ranggo no banco configurado.

    Operação **idempotente**: :meth:`MetaData.create_all` só cria as
    tabelas que ainda não existem; bancos já populados ficam intactos.
    Garante também que a pasta ``data/`` exista antes da criação do
    arquivo SQLite.

    Importa o pacote :mod:`src.database.models` para registrar todas as
    tabelas em ``Base.metadata`` antes do ``create_all``.
    """
    # Garante a pasta-pai do arquivo .db.
    db_path = Path(config.DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    ja_existia = db_path.exists()

    # Import com efeito colateral: registra todas as tabelas em
    # ``Base.metadata``. ``noqa: F401`` para o linter não reclamar do
    # import "não usado".
    from src.database import models  # noqa: F401
    from src.database.models import Base

    Base.metadata.create_all(engine)

    if ja_existia:
        print(f"Banco já existe em {config.DB_PATH}")
    else:
        print(f"Banco inicializado em {config.DB_PATH}")
