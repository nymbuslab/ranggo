"""Fixtures pytest compartilhadas entre todos os testes unitarios.

Cada teste roda contra um banco SQLite em memoria isolado, com perfis
populados via seed e (opcionalmente) um Admin seedado.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que a raiz do projeto esta no sys.path antes dos imports de
# `src.*`. Necessario porque nao usamos pyproject.toml nem instalamos o
# pacote em modo editavel — pytest descobre o conftest mas nao injeta a
# raiz no path automaticamente quando ha __init__.py em tests/unit/.
_RAIZ_PROJETO = Path(__file__).resolve().parents[2]
if str(_RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROJETO))

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import Base
from src.database.models.usuario import Usuario
from src.database.seed import _seed_perfis, _seed_unidades_medida
from src.repositories.perfil_repository import PerfilRepository
from src.services import sessao
from src.services.auth_service import AuthService


@pytest.fixture
def session() -> Session:
    """Cria banco SQLite em memoria isolado por teste.

    - Aplica todas as migrations (Base.metadata.create_all).
    - Popula perfis e unidades de medida (mesmo seed do app).
    - Habilita PRAGMA foreign_keys ON.
    - Retorna sessao SQLAlchemy ativa.
    - Encerra/limpa apos cada teste.

    Usa StaticPool + check_same_thread=False para que a unica conexao
    do :memory: seja reutilizada entre eventos do SQLAlchemy (caso
    contrario, o PRAGMA roda em conexao descartada e o teste perde os
    dados seedados).
    """
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    session = SessionLocal()

    _seed_perfis(session)
    _seed_unidades_medida(session)
    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def admin_seedado(session: Session) -> Usuario:
    """Cria usuario Admin no banco e retorna o objeto Usuario.

    Util para testes que precisam de um admin existente (ex: testar
    auto-desativacao ou guarda do ultimo admin).
    """
    repo_perfil = PerfilRepository(session)
    perfil_admin = repo_perfil.buscar_por_nome("Admin")
    assert perfil_admin is not None, "Perfil Admin deveria existir apos seed"

    auth = AuthService(session)
    senha_hash = auth.criar_hash("admin123")

    admin = Usuario(
        nome="Administrador",
        login="admin",
        senha_hash=senha_hash,
        perfil_id=perfil_admin.id,
        ativo=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


@pytest.fixture(autouse=True)
def limpar_sessao_singleton():
    """Garante que sessao singleton esta limpa antes/apos cada teste.

    `autouse=True` aplica essa fixture automaticamente em todos os
    testes — sem precisar declarar como parametro.
    """
    sessao.encerrar()
    yield
    sessao.encerrar()
