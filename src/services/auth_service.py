"""Service de autenticação — hash, verificação e fluxo de login.

Camada de regras de negócio sobre :class:`Usuario`:

* Geração de hash bcrypt (com salt aleatório por chamada) e verificação
  resistente a timing attacks via :func:`bcrypt.checkpw`.
* Fluxo de login com tradução de erros para exceções de domínio
  (:class:`LoginInvalidoError`, :class:`UsuarioInativoError`).
* Política mínima de senha da Fase 1: ≥ 6 caracteres
  (vai endurecer na Fase 5).

O service **não** conhece Flet/UI e **não** gerencia transação: a
:class:`Session` é injetada pelo caller, que também é responsável por
``commit``/``rollback`` (normalmente via ``with get_session() as session``).
"""

from __future__ import annotations

import bcrypt

from sqlalchemy.orm import Session

from src.database.models.usuario import Usuario
from src.repositories.usuario_repository import UsuarioRepository
from src.utils.exceptions import (
    LoginInvalidoError,
    SenhaFracaError,
    UsuarioInativoError,
)


# Política de senha da Fase 1: mínimo de 6 caracteres. Vai endurecer na
# Fase 5 (letras + números, lista de senhas óbvias bloqueadas, etc.).
SENHA_MIN_LEN = 6


class AuthService:
    """Autenticação e gestão de credenciais de :class:`Usuario`."""

    def __init__(self, session: Session) -> None:
        """Recebe a :class:`Session` usada pelas operações de banco.

        Args:
            session: Sessão SQLAlchemy ativa, gerenciada pelo caller.
        """
        self._session = session
        self._usuarios = UsuarioRepository(session)

    def criar_hash(self, senha: str) -> str:
        """Gera hash bcrypt da senha em texto plano.

        Usado pelo seed do usuário Admin (Passo 5) e pelo CRUD de
        Usuários (Passo 9). Aplica a política mínima de senha **antes**
        de hashear — senha fraca não chega a gerar hash.

        Args:
            senha: Senha em texto plano.

        Returns:
            Hash bcrypt como string de 60 caracteres (formato
            ``$2b$<cost>$<salt><hash>``).

        Raises:
            SenhaFracaError: Se ``senha`` tiver menos de 6 caracteres.
        """
        if len(senha) < SENHA_MIN_LEN:
            raise SenhaFracaError(
                f"Senha deve ter pelo menos {SENHA_MIN_LEN} caracteres."
            )
        hash_bytes = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
        return hash_bytes.decode("utf-8")

    def verificar_senha(self, senha: str, hash_armazenado: str) -> bool:
        """Compara senha em texto plano com hash bcrypt armazenado.

        Internamente usa :func:`bcrypt.checkpw`, que faz comparação em
        tempo constante (resistente a timing attacks).

        Args:
            senha: Senha digitada pelo usuário.
            hash_armazenado: Valor de ``usuario.senha_hash``.

        Returns:
            ``True`` se a senha bate com o hash, ``False`` caso contrário.
        """
        return bcrypt.checkpw(
            senha.encode("utf-8"),
            hash_armazenado.encode("utf-8"),
        )

    def autenticar(self, login: str, senha: str) -> Usuario:
        """Executa o fluxo completo de login.

        Sequência:
            1. Busca usuário pelo login (case-sensitive).
            2. Verifica a senha contra o hash armazenado.
            3. Confere se o usuário está ativo.

        A mesma exceção (:class:`LoginInvalidoError`) é levantada tanto
        para login inexistente quanto para senha incorreta — com
        **mensagem idêntica** —, para não permitir que um atacante
        enumere logins válidos pela diferença de resposta.

        Args:
            login: Nome de login (case-sensitive).
            senha: Senha em texto plano.

        Returns:
            O :class:`Usuario` autenticado.

        Raises:
            LoginInvalidoError: Usuário não existe ou senha incorreta.
            UsuarioInativoError: Login + senha corretos, mas o usuário
                está marcado como ``ativo=False``.
        """
        usuario = self._usuarios.buscar_por_login(login)
        if usuario is None:
            raise LoginInvalidoError("Login ou senha incorretos.")

        if not self.verificar_senha(senha, usuario.senha_hash):
            raise LoginInvalidoError("Login ou senha incorretos.")

        if not usuario.ativo:
            raise UsuarioInativoError("Conta desativada.")

        return usuario
