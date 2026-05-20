"""Sessão de usuário logado — singleton em memória.

Estado global do operador autenticado, acessível por toda a UI. **Não**
persiste entre execuções: ao reabrir o app, ninguém está logado.

Design:

* Estado no nível de módulo (``_usuario_atual``) — Python já garante
  singleton ao importar o módulo uma única vez, sem precisar de classe.
* Toda leitura/escrita passa por :data:`_lock` (``threading.Lock``)
  porque o Flet executa callbacks em threads variáveis e atribuir/ler
  uma referência composta não é atômica para todos os cenários.

Não importa repositories, services ou UI: este módulo só guarda quem
está logado. O fluxo de login (Passo 6) é responsável por chamar
:func:`iniciar` *depois* que ``AuthService.autenticar()`` retornar.
"""

from __future__ import annotations

import threading

from src.database.models.usuario import Usuario
from src.utils.exceptions import PermissaoNegadaError


_usuario_atual: Usuario | None = None
_lock: threading.Lock = threading.Lock()


def iniciar(usuario: Usuario) -> None:
    """Inicia uma sessão com o ``usuario`` informado.

    Chamado pelo fluxo de login (Passo 6) após
    ``AuthService.autenticar()`` retornar com sucesso. Thread-safe: a
    troca de estado é feita dentro do lock.

    Args:
        usuario: Usuário já autenticado.

    Raises:
        ValueError: Se já existe sessão ativa. O caller deve chamar
            :func:`encerrar` antes — não trocamos usuário silenciosamente,
            para evitar bugs onde a UI exibiria o usuário antigo.
    """
    global _usuario_atual
    with _lock:
        if _usuario_atual is not None:
            raise ValueError("Ja existe sessao ativa. Chame encerrar() antes.")
        _usuario_atual = usuario


def encerrar() -> None:
    """Encerra a sessão atual.

    Idempotente: chamar sem sessão ativa é no-op. Útil para a UI
    garantir limpeza em caminhos de erro (ex.: falha durante o startup
    pós-login).
    """
    global _usuario_atual
    with _lock:
        _usuario_atual = None


def usuario_atual() -> Usuario | None:
    """Retorna o usuário logado, ou ``None`` se não há sessão."""
    with _lock:
        return _usuario_atual


def esta_logado() -> bool:
    """Atalho de conveniência: ``True`` se há usuário na sessão."""
    with _lock:
        return _usuario_atual is not None


def requer_perfil(*nomes_perfil: str) -> Usuario:
    """Guarda de autorização: garante que o usuário atual tem um dos perfis listados.

    Uso típico em views/services restritos::

        from src.services import sessao

        usuario = sessao.requer_perfil("Admin")
        # ... segue com ``usuario`` disponível

    Args:
        *nomes_perfil: Nomes de perfis aceitos (ex.: ``"Admin"``,
            ``"Gerente"``). Comparação é case-sensitive.

    Returns:
        O :class:`Usuario` atual — conveniência para evitar uma chamada
        adicional a :func:`usuario_atual`.

    Raises:
        PermissaoNegadaError: Se não há sessão ativa **ou** se o perfil
            do usuário não está em ``nomes_perfil``. Uma única exceção
            cobre os dois casos — a UI não precisa diferenciar.
    """
    with _lock:
        usuario = _usuario_atual

    if usuario is None:
        raise PermissaoNegadaError("Acao requer autenticacao.")

    if usuario.perfil.nome not in nomes_perfil:
        perfis_aceitos = ", ".join(nomes_perfil)
        raise PermissaoNegadaError(
            f"Acao requer perfil: {perfis_aceitos}. "
            f"Seu perfil: {usuario.perfil.nome}."
        )

    return usuario
