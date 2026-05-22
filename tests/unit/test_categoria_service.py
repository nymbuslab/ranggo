"""Testes unitarios do CategoriaService.

Cobre as regras criticas:
1. criar: valida nome obrigatorio, nome unico.
2. atualizar: permite manter proprio nome, bloqueia roubo de nome alheio.
3. desativar: marca ativo=False.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.services.categoria_service import CategoriaService
from src.utils.exceptions import NomeDuplicadoError


class TestCriar:
    """Testes do metodo criar()."""

    def test_criar_categoria_valida(self, session: Session) -> None:
        service = CategoriaService(session)

        categoria = service.criar(nome="Bebidas", descricao="Refrigerantes e sucos")

        assert categoria.id is not None
        assert categoria.nome == "Bebidas"
        assert categoria.descricao == "Refrigerantes e sucos"
        assert categoria.ativo is True

    def test_criar_nome_duplicado_levanta_erro(self, session: Session) -> None:
        service = CategoriaService(session)
        service.criar(nome="Bebidas")
        session.commit()

        with pytest.raises(NomeDuplicadoError) as excinfo:
            service.criar(nome="Bebidas")
        assert "bebidas" in str(excinfo.value).lower()

    def test_criar_nome_vazio_levanta_value_error(self, session: Session) -> None:
        service = CategoriaService(session)

        with pytest.raises(ValueError) as excinfo:
            service.criar(nome="   ")  # so espacos, fica vazio apos strip
        assert "obrigatorio" in str(excinfo.value).lower()


class TestAtualizar:
    """Testes do metodo atualizar()."""

    def test_atualizar_nome_para_outro_existente_levanta_erro(
        self, session: Session
    ) -> None:
        """Criar 2 categorias; tentar mudar nome da 2a para o nome da 1a."""
        service = CategoriaService(session)
        bebidas = service.criar(nome="Bebidas")
        marmitex = service.criar(nome="Marmitex")
        session.commit()

        with pytest.raises(NomeDuplicadoError) as excinfo:
            service.atualizar(
                categoria_id=marmitex.id,
                nome="Bebidas",  # ja existe (id != marmitex.id)
                descricao=None,
                ativo=True,
            )
        assert "bebidas" in str(excinfo.value).lower()
        # bebidas referenciado para garantir que esta no escopo
        assert bebidas.id != marmitex.id

    def test_atualizar_mantendo_proprio_nome_nao_levanta(
        self, session: Session
    ) -> None:
        """Editar uma categoria mantendo seu proprio nome eh valido."""
        service = CategoriaService(session)
        categoria = service.criar(nome="Bebidas", descricao="velha")
        session.commit()

        atualizada = service.atualizar(
            categoria_id=categoria.id,
            nome="Bebidas",  # mesmo nome
            descricao="nova descricao",
            ativo=True,
        )

        assert atualizada.id == categoria.id
        assert atualizada.nome == "Bebidas"
        assert atualizada.descricao == "nova descricao"


class TestDesativar:
    """Testes do metodo desativar() — wrapper sobre atualizar()."""

    def test_desativar_categoria_marca_ativo_false(
        self, session: Session
    ) -> None:
        service = CategoriaService(session)
        categoria = service.criar(nome="Petiscos")
        session.commit()

        service.desativar(categoria.id)
        session.commit()

        atualizada = service.buscar_por_id(categoria.id)
        assert atualizada is not None
        assert atualizada.ativo is False
        # Nome e descricao preservados.
        assert atualizada.nome == "Petiscos"
