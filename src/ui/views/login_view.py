"""Tela de Login — referência ``prototipos/01-login.png``.

View standalone (sem dependência de roteamento ou shell): recebe a
:class:`ft.Page` e um callback ``on_login_success`` no construtor; ao
autenticar com sucesso, repassa o :class:`Usuario` para o callback. Quem
decide o que fazer depois — iniciar :mod:`src.services.sessao`, trocar
para o shell autenticado, etc. — é o caller (``app.py``, no Passo 7).

Layout:
    * Coluna esquerda preta (50%) com logo SVG laranja, wordmark
      ``Ranggo`` e subtítulo.
    * Coluna direita branca (50%) com formulário centralizado (largura
      400 px): título, campos Usuário/Senha, link "Esqueci minha senha"
      desabilitado (placeholder Fase 5), botão "Entrar" e área de erro
      inline.

Decisões cravadas:
    * Erros aparecem **inline** abaixo do botão, em vermelho — nada de
      ``SnackBar`` nem ``Dialog`` no fluxo de login.
    * O erro some assim que o usuário começa a digitar novamente.
    * ``Enter`` no campo de senha submete o formulário.
    * View não conhece :mod:`src.services.sessao`; isso fica no Passo 7.
"""

from __future__ import annotations

import traceback
from typing import Callable

import flet as ft

from src.database.connection import get_session
from src.database.models.usuario import Usuario
from src.services.auth_service import AuthService
from src.ui import components, theme
from src.utils.exceptions import (
    LoginInvalidoError,
    RanggoError,
    UsuarioInativoError,
)


# Largura do cartão de formulário (lado direito). Mantém o conteúdo
# legível em monitores largos sem precisar de larguras dinâmicas.
_LARGURA_FORMULARIO: int = 400

# TODO: quando virar coisa recorrente, migrar para config.VERSION.
_VERSAO_RODAPE: str = "Versão 0.2.0"


class LoginView:
    """Tela de autenticação.

    Uso típico::

        login = LoginView(page, on_login_success=callback)
        page.add(login.build())

    O callback recebe o :class:`Usuario` autenticado. A view **não**
    inicia sessão (:mod:`src.services.sessao`) — isso é responsabilidade
    do caller, para manter a view independente da máquina de estado.
    """

    def __init__(
        self,
        page: ft.Page,
        on_login_success: Callable[[Usuario], None],
    ) -> None:
        """Cria a view.

        Args:
            page: Página Flet onde a view será montada (usada para
                disparar ``page.update`` após mudanças de estado da UI).
            on_login_success: Callback chamado com o :class:`Usuario`
                autenticado quando o login dá certo.
        """
        self._page = page
        self._on_login_success = on_login_success

        self._campo_login: ft.TextField | None = None
        self._campo_senha: ft.TextField | None = None
        self._texto_erro: ft.Text | None = None

    # ------------------------------------------------------------------
    # Construção da árvore de Controls
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Constrói e retorna o :class:`ft.Control` raiz da view.

        Returns:
            :class:`ft.Row` que ocupa 100% da viewport, com a coluna
            esquerda preta e a coluna direita branca.
        """
        return ft.Row(
            controls=[
                self._build_lado_esquerdo(),
                self._build_lado_direito(),
            ],
            spacing=0,
            expand=True,
        )

    def _build_lado_esquerdo(self) -> ft.Container:
        """Coluna esquerda: fundo preto com logo + wordmark + subtítulo."""
        bloco = ft.Column(
            controls=[
                ft.Image(
                    src="logo/logo.svg",
                    width=80,
                    height=80,
                ),
                ft.Container(height=16),
                ft.Text(
                    "Ranggo",
                    color=theme.COR_TERCIARIA,
                    size=32,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    "Sistema de Gestão para Restaurantes",
                    color=theme.COR_CINZA_400,
                    size=theme.FONTE_TAMANHO_CORPO,
                    weight=ft.FontWeight.W_400,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        return ft.Container(
            expand=1,
            bgcolor=theme.COR_SECUNDARIA,
            alignment=ft.Alignment.CENTER,
            content=bloco,
        )

    def _build_lado_direito(self) -> ft.Container:
        """Coluna direita: fundo branco com o formulário centralizado."""
        # Largura explícita IDÊNTICA nos dois campos — sem isso, o
        # ``can_reveal_password=True`` no campo de senha desloca a borda
        # direita do input (o ícone do olho é renderizado como suffix
        # nativo) e o campo Senha aparece mais largo que o de Usuário.
        self._campo_login = ft.TextField(
            label="Usuário",
            hint_text="Digite seu usuário",
            autofocus=True,
            width=_LARGURA_FORMULARIO,
            border_radius=theme.BORDER_RADIUS_INPUT,
            border_color=theme.COR_CINZA_200,
            focused_border_color=theme.COR_PRIMARIA,
            height=theme.ALTURA_INPUT + 16,  # +16 para acomodar o label flutuante
            text_size=theme.FONTE_TAMANHO_CORPO,
            on_change=self._on_campo_change,
        )

        self._campo_senha = ft.TextField(
            label="Senha",
            hint_text="Digite sua senha",
            password=True,
            can_reveal_password=True,
            width=_LARGURA_FORMULARIO,
            border_radius=theme.BORDER_RADIUS_INPUT,
            border_color=theme.COR_CINZA_200,
            focused_border_color=theme.COR_PRIMARIA,
            height=theme.ALTURA_INPUT + 16,
            text_size=theme.FONTE_TAMANHO_CORPO,
            on_change=self._on_campo_change,
            on_submit=lambda e: self._tentar_login(),
        )

        # Enter no campo Usuario foca campo Senha. Tab escapa pra
        # sidebar (limitacao do Flet 0.85.1 — ver CLAUDE.md
        # "Pegadinhas Flet 0.85.1"); Enter eh a navegacao usavel.
        # focus() eh coroutine async — usar helper que retorna async
        # handler. Lambda sync NAO funciona (coroutine nao eh awaited).
        self._campo_login.on_submit = components.proximo_campo(
            self._campo_senha
        )

        link_esqueci = ft.Row(
            controls=[
                ft.TextButton(
                    content=ft.Text(
                        "Esqueci minha senha",
                        size=theme.FONTE_TAMANHO_HELPER,
                        color=theme.COR_PRIMARIA,
                        weight=ft.FontWeight.W_500,
                    ),
                    disabled=True,
                    tooltip=(
                        "Disponível em versão futura. "
                        "Peça reset ao administrador."
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
        )

        botao_entrar = ft.ElevatedButton(
            content=ft.Text(
                "Entrar",
                color=theme.COR_TERCIARIA,
                size=theme.FONTE_TAMANHO_LABEL,
                weight=ft.FontWeight.W_600,
            ),
            bgcolor=theme.COR_PRIMARIA,
            color=theme.COR_TERCIARIA,
            height=theme.ALTURA_BOTAO,
            width=_LARGURA_FORMULARIO,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(
                    radius=theme.BORDER_RADIUS_BOTAO,
                ),
            ),
            on_click=lambda e: self._tentar_login(),
        )

        self._texto_erro = ft.Text(
            value="",
            color=theme.COR_ERRO,
            size=theme.FONTE_TAMANHO_CORPO,
            weight=ft.FontWeight.W_500,
            visible=False,
        )

        rodape_versao = ft.Text(
            _VERSAO_RODAPE,
            size=theme.FONTE_TAMANHO_HELPER,
            color=theme.COR_CINZA_400,
        )

        # Column sem ``tight=True``: deixa a coluna preencher toda a altura
        # do Container pai. Combinado com ``alignment=MainAxisAlignment.CENTER``,
        # o conteúdo é centralizado verticalmente — mesmo padrão usado no
        # lado esquerdo. Com ``tight=True`` o ``alignment`` vira no-op e
        # o formulário fica visualmente colado no topo em monitores grandes.
        formulario = ft.Column(
            controls=[
                ft.Text(
                    "Bem-vindo de volta",
                    color=theme.COR_SECUNDARIA,
                    size=28,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    "Faça login para continuar",
                    color=theme.COR_CINZA_600,
                    size=theme.FONTE_TAMANHO_CORPO,
                    weight=ft.FontWeight.W_400,
                ),
                ft.Container(height=32),  # respiro maior antes do primeiro campo
                self._campo_login,
                ft.Container(height=12),
                self._campo_senha,
                ft.Container(height=4),
                link_esqueci,
                ft.Container(height=8),
                botao_entrar,
                ft.Container(height=8),
                self._texto_erro,
                ft.Container(height=32),
                rodape_versao,
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.CENTER,
            width=_LARGURA_FORMULARIO,
        )

        return ft.Container(
            expand=1,
            bgcolor=theme.COR_TERCIARIA,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(horizontal=32, vertical=32),
            content=formulario,
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_campo_change(self, e: ft.ControlEvent) -> None:
        """Limpa a mensagem de erro assim que o usuário começa a digitar."""
        if self._texto_erro is not None and self._texto_erro.visible:
            self._texto_erro.value = ""
            self._texto_erro.visible = False
            self._page.update()

    def _tentar_login(self) -> None:
        """Lê os campos, valida e dispara o fluxo de autenticação."""
        assert self._campo_login is not None
        assert self._campo_senha is not None

        login = (self._campo_login.value or "").strip()
        senha = self._campo_senha.value or ""

        if not login or not senha:
            self._mostrar_erro("Preencha login e senha.")
            return

        try:
            with get_session() as session:
                auth = AuthService(session)
                usuario = auth.autenticar(login, senha)
        except LoginInvalidoError:
            self._mostrar_erro("Login ou senha incorretos.")
            return
        except UsuarioInativoError:
            self._mostrar_erro("Conta desativada. Contate o administrador.")
            return
        except RanggoError as e:
            self._mostrar_erro(f"Erro no login: {e}")
            return
        except Exception:
            # Inesperado: registra stack no stderr para debug e mostra
            # mensagem genérica ao operador (sem expor detalhes técnicos).
            traceback.print_exc()
            self._mostrar_erro("Erro inesperado. Tente novamente.")
            return

        self._on_login_success(usuario)

    def _mostrar_erro(self, mensagem: str) -> None:
        """Exibe ``mensagem`` na área de erro inline abaixo do botão."""
        if self._texto_erro is None:
            return
        self._texto_erro.value = mensagem
        self._texto_erro.visible = True
        self._page.update()
