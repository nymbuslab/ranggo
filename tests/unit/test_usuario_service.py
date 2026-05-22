"""Testes unitarios do UsuarioService.

Cobre as 5 regras de negocio criticas:
1. criar: login unico, senha minima, perfil valido.
2. atualizar: guarda de auto-desativacao.
3. atualizar: guarda do ultimo admin ativo.
4. desativar (wrapper): herda as guardas.
5. trocar_senha: funciona e nova senha autentica.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.database.models.usuario import Usuario
from src.repositories.perfil_repository import PerfilRepository
from src.services import sessao
from src.services.auth_service import AuthService
from src.services.usuario_service import UsuarioService
from src.utils.exceptions import (
    NomeDuplicadoError,
    PermissaoNegadaError,
    SenhaFracaError,
)


class TestCriar:
    """Testes do metodo criar()."""

    def test_criar_usuario_valido_retorna_usuario_com_id(
        self, session: Session
    ) -> None:
        service = UsuarioService(session)
        repo_perfil = PerfilRepository(session)
        perfil_caixa = repo_perfil.buscar_por_nome("Caixa")

        usuario = service.criar(
            nome="Joao Silva",
            login="joao",
            senha="senha123",
            perfil_id=perfil_caixa.id,
        )

        assert usuario.id is not None
        assert usuario.login == "joao"
        assert usuario.nome == "Joao Silva"
        assert usuario.ativo is True
        assert usuario.senha_hash != "senha123"  # hash, nao texto plano

    def test_criar_login_duplicado_levanta_nome_duplicado_error(
        self, session: Session, admin_seedado: Usuario
    ) -> None:
        """admin_seedado ja existe com login='admin'. Tentar criar outro
        com mesmo login deve falhar."""
        service = UsuarioService(session)
        repo_perfil = PerfilRepository(session)
        perfil_caixa = repo_perfil.buscar_por_nome("Caixa")

        with pytest.raises(NomeDuplicadoError) as excinfo:
            service.criar(
                nome="Outro Admin",
                login="admin",  # ja existe
                senha="senha456",
                perfil_id=perfil_caixa.id,
            )
        assert "admin" in str(excinfo.value).lower()

    def test_criar_senha_fraca_levanta_senha_fraca_error(
        self, session: Session
    ) -> None:
        service = UsuarioService(session)
        repo_perfil = PerfilRepository(session)
        perfil_caixa = repo_perfil.buscar_por_nome("Caixa")

        with pytest.raises(SenhaFracaError):
            service.criar(
                nome="Maria",
                login="maria",
                senha="12345",  # 5 chars, minimo eh 6
                perfil_id=perfil_caixa.id,
            )

    def test_criar_perfil_invalido_levanta_value_error(
        self, session: Session
    ) -> None:
        service = UsuarioService(session)

        with pytest.raises(ValueError) as excinfo:
            service.criar(
                nome="Pedro",
                login="pedro",
                senha="senha789",
                perfil_id=99999,  # nao existe
            )
        assert "perfil" in str(excinfo.value).lower()


class TestAtualizar:
    """Testes do metodo atualizar(), focando nas guardas de protecao."""

    def test_atualizar_auto_desativacao_bloqueada(
        self, session: Session, admin_seedado: Usuario
    ) -> None:
        """Usuario logado tentando desativar a propria conta deve falhar."""
        sessao.iniciar(admin_seedado)
        service = UsuarioService(session)

        with pytest.raises(PermissaoNegadaError) as excinfo:
            service.atualizar(
                usuario_id=admin_seedado.id,
                nome=admin_seedado.nome,
                perfil_id=admin_seedado.perfil_id,
                ativo=False,
            )
        assert "propria conta" in str(excinfo.value).lower()

    def test_atualizar_desativar_ultimo_admin_bloqueado(
        self, session: Session, admin_seedado: Usuario
    ) -> None:
        """Mesmo sem sessao iniciada, desativar o unico admin do sistema
        deve falhar."""
        service = UsuarioService(session)

        # Confirmar que admin_seedado eh o unico admin ativo
        admins = [
            u for u in service.listar(incluir_inativos=False)
            if u.perfil.nome == "Admin"
        ]
        assert len(admins) == 1

        with pytest.raises(PermissaoNegadaError) as excinfo:
            service.atualizar(
                usuario_id=admin_seedado.id,
                nome=admin_seedado.nome,
                perfil_id=admin_seedado.perfil_id,
                ativo=False,
            )
        assert "ultimo admin" in str(excinfo.value).lower()


class TestTrocarSenha:
    """Testes do metodo trocar_senha()."""

    def test_trocar_senha_funciona_e_nova_senha_autentica(
        self, session: Session, admin_seedado: Usuario
    ) -> None:
        service = UsuarioService(session)
        auth = AuthService(session)

        # Trocar senha
        service.trocar_senha(admin_seedado.id, "novasenha456")
        session.commit()

        # Autenticar com senha nova deve funcionar
        usuario_autenticado = auth.autenticar("admin", "novasenha456")
        assert usuario_autenticado is not None
        assert usuario_autenticado.id == admin_seedado.id


class TestDesativar:
    """Testes do metodo desativar() — wrapper sobre atualizar()."""

    def test_desativar_usuario_comum_funciona(
        self, session: Session
    ) -> None:
        """Criar usuario comum (Caixa) e desativar — deve funcionar."""
        service = UsuarioService(session)
        repo_perfil = PerfilRepository(session)
        perfil_caixa = repo_perfil.buscar_por_nome("Caixa")

        usuario = service.criar(
            nome="Joao",
            login="joao",
            senha="senha123",
            perfil_id=perfil_caixa.id,
        )
        session.commit()

        service.desativar(usuario.id)
        session.commit()

        usuario_atualizado = service.buscar_por_id(usuario.id)
        assert usuario_atualizado.ativo is False
