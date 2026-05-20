"""Repositório de :class:`Perfil` — CRUD puro sobre a tabela ``perfis``.

Camada "burra" de acesso a dados: não valida regras de negócio, não
gerencia ciclo de vida de :class:`Session` e não conhece UI nem
serviços. A :class:`Session` é injetada pelo caller (geralmente um
service) via construtor.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.perfil import Perfil


class PerfilRepository:
    """Acesso a dados da entidade :class:`Perfil`."""

    def __init__(self, session: Session) -> None:
        """Recebe a :class:`Session` que será usada por todas as operações.

        Args:
            session: Sessão SQLAlchemy ativa, gerenciada pelo caller.
        """
        self._session = session

    def listar(self) -> list[Perfil]:
        """Retorna todos os perfis cadastrados."""
        stmt = select(Perfil)
        return list(self._session.execute(stmt).scalars().all())

    def buscar_por_id(self, id: int) -> Perfil | None:
        """Busca um perfil pelo id (retorna ``None`` se não existir)."""
        return self._session.get(Perfil, id)

    def buscar_por_nome(self, nome: str) -> Perfil | None:
        """Busca perfil pelo nome (ex.: ``"Admin"``, ``"Gerente"``, ``"Caixa"``).

        Usado pelo seed do usuário Admin (Passo 5) e pela criação de
        usuários (Passo 9) para resolver ``perfil_id`` a partir do nome,
        evitando hardcode de IDs em código que precisa ser estável entre
        ambientes.

        Args:
            nome: Nome exato do perfil (case-sensitive).

        Returns:
            O :class:`Perfil` correspondente ou ``None`` se não existir.
        """
        stmt = select(Perfil).where(Perfil.nome == nome)
        return self._session.execute(stmt).scalar_one_or_none()

    def criar(self, dados: dict) -> Perfil:
        """Cria um novo perfil a partir de um dicionário de campos."""
        perfil = Perfil(**dados)
        self._session.add(perfil)
        self._session.flush()
        return perfil

    def atualizar(self, id: int, dados: dict) -> Perfil:
        """Atualiza os campos do perfil identificado por ``id``."""
        perfil = self._session.get(Perfil, id)
        if perfil is None:
            raise ValueError(f"Perfil id={id} não encontrado")
        for campo, valor in dados.items():
            setattr(perfil, campo, valor)
        self._session.flush()
        return perfil

    def deletar(self, id: int) -> None:
        """Remove fisicamente o perfil identificado por ``id`` (hard delete).

        Soft delete (marcar inativo) é responsabilidade do service: se o
        caso de uso exigir manter histórico, o service chama
        ``atualizar(id, {"ativo": False})``. Este método apaga de fato.

        Args:
            id: Identificador do perfil a remover.

        Raises:
            ValueError: Se o ``id`` não existir.
        """
        perfil = self._session.get(Perfil, id)
        if perfil is None:
            raise ValueError(f"Perfil id={id} não encontrado")
        self._session.delete(perfil)
        self._session.flush()
