"""Entry point da UI: configura janela, tema e despacha entre Login e Shell.

A função :func:`main` é o alvo de ``ft.run(main=...)`` chamado em
``main.py``. Decide o que renderizar baseado em :func:`sessao.esta_logado`:

    * Sem sessão → :class:`LoginView`.
    * Com sessão → shell (sidebar 240 px preta + topbar 64 px branca +
      área de conteúdo cinza com card central da Fase 0).

Re-render é feito limpando ``page.controls`` e chamando ``page.update``.
Não há roteamento por URL — a transição é puramente de estado, conforme
combinado para a Fase 1.
"""

from __future__ import annotations

import os

import flet as ft

from src.database.connection import engine
from src.database.models.usuario import Usuario
from src.services import sessao
from src.ui import theme
from src.ui.views.login_view import LoginView


# Itens do menu lateral. Ordem reflete o protótipo prototipos/02-dashboard.png.
# (rotulo, icone). O item "Dashboard" começa marcado como ativo.
_ITENS_MENU: list[tuple[str, ft.IconData]] = [
    ("Dashboard", ft.Icons.SPACE_DASHBOARD),
    ("Vendas", ft.Icons.POINT_OF_SALE),
    ("Comandas", ft.Icons.RECEIPT_LONG),
    ("Delivery", ft.Icons.DELIVERY_DINING),
    ("Cadastros", ft.Icons.FOLDER),
    ("Estoque", ft.Icons.INVENTORY_2),
    ("Relatórios", ft.Icons.BAR_CHART),
    ("Usuários", ft.Icons.PEOPLE),
    ("Configurações", ft.Icons.SETTINGS),
]


def main(page: ft.Page) -> None:
    """Ponto de entrada da UI do Ranggo.

    Aplica tema, configura a janela e despacha para Login ou Shell
    baseado no estado de :mod:`src.services.sessao`. Chamada por
    ``ft.run(main=main)`` no ``main.py``.

    Args:
        page: Página fornecida pelo runtime do Flet.
    """
    # --- Tema e configuração de janela ---
    page.title = "Ranggo"
    page.theme = theme.build_flet_theme()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = theme.COR_CINZA_100
    page.padding = 0  # shell ocupa 100% da viewport; padding é interno por área.

    # Dimensões iniciais. PDV exige 1280×720 para layout de 3 colunas; abaixo
    # disso quebra. ``maximized`` é aplicado depois do primeiro render (ver
    # final desta função) — setar aqui no Flet 0.85.1 é inconfiável.
    page.window.width = 1280
    page.window.height = 720
    page.window.min_width = 1280
    page.window.min_height = 720
    # Caminho relativo a assets_dir (definido em main.py).
    page.window.icon = "logo/logo.ico"

    # --- Shutdown limpo ---
    # Sem isso, ft.run() leva ~2s para retornar após o usuário fechar a janela
    # porque o subprocesso Flutter (flet.exe) demora a desmontar gracefully.
    # Durante esse delay, SQLite locks e portas internas ficam presos — a
    # próxima execução trava em "Working..." enquanto o sistema espera os
    # recursos liberarem. Forçar saída no evento CLOSE elimina o intervalo.
    # prevent_close=True é OBRIGATÓRIO para que o Flet 0.85.1 dispare
    # WindowEventType.CLOSE ao clicar no X. Com prevent_close=False
    # (default) o X fecha a janela direto, o handler NUNCA recebe CLOSE,
    # e Python sai apenas quando ft.run() retorna após o subprocesso
    # flet.exe desmontar — gradiente que deixa SQLite locks e portas
    # presos, travando a próxima execução em "Working...". Com
    # prevent_close=True, o handler abaixo intercepta, faz cleanup
    # síncrono e força os._exit(0) antes de qualquer desmontagem do
    # Flutter. Causa investigada com instrumentação em 2026-05-20.
    page.window.prevent_close = True

    def _on_window_event(e: ft.WindowEvent) -> None:
        if e.type != ft.WindowEventType.CLOSE:
            return

        # 1. Dispose do engine: libera o lock do SQLite imediatamente.
        try:
            engine.dispose()
        except Exception:
            pass

        # 2. Matar TODOS os flet.exe do sistema (não só filhos do Python).
        #    O Flet 0.85.1 cria netos que se desvinculam do pai, ficando
        #    como top-level invisíveis a ``psutil.children``. Kill global
        #    é brutal mas eficaz em ambiente single-app — o Ranggo é o
        #    único app Flet do PC. Matar o flet.exe é o que efetivamente
        #    fecha a janela (o flet.exe É o renderer Flutter); não
        #    chamamos ``page.window.destroy()`` porque em Flet 0.85.1
        #    é coroutine async e geraria RuntimeWarning sem efeito real.
        try:
            import psutil

            for proc in psutil.process_iter(["name"]):
                try:
                    if (proc.info.get("name") or "").lower() == "flet.exe":
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass

        # 3. Matar processo Python. ``os._exit`` em vez de ``sys.exit``
        #    para bypassar qualquer cleanup pendente do runtime Flet.
        os._exit(0)

    page.window.on_event = _on_window_event

    # --- Renderiza tela inicial ---
    _renderizar(page)

    # --- Maximize PÓS-RENDER ---
    # No Flet 0.85.1, ``page.window.maximized = True`` aplicado ANTES do
    # primeiro ``page.update()`` é inconfiável: ora não maximiza (janela
    # abre default com "Working..." até o usuário maximizar à mão), ora
    # abre ocupando até a área da taskbar (cortando rodapé do conteúdo).
    # Aplicar APÓS o render inicial faz o Flutter recalcular o tamanho da
    # área útil do Windows corretamente. Descoberto em 2026-05-20.
    page.window.maximized = True
    page.update()


# ---------------------------------------------------------------------------
# Despacho Login <-> Shell
# ---------------------------------------------------------------------------

def _renderizar(page: ft.Page) -> None:
    """Renderiza a tela atual baseado em :func:`sessao.esta_logado`.

    Chamada em três momentos:
        1. Startup, a partir de :func:`main`.
        2. Após login bem-sucedido (callback da :class:`LoginView`).
        3. Após logout (handler do botão "Fechar Caixa").

    Limpa ``page.controls`` antes de adicionar a nova árvore e chama
    ``page.update`` para refletir a troca.

    Args:
        page: Página Flet ativa.
    """
    page.controls.clear()
    if sessao.esta_logado():
        page.add(_build_shell(page))
    else:
        page.add(_build_login(page))
    page.update()


def _build_login(page: ft.Page) -> ft.Control:
    """Monta a :class:`LoginView` com callback que inicia sessão e re-renderiza.

    Args:
        page: Página Flet ativa, passada à view para que ela possa
            chamar ``page.update`` ao alterar estado interno.

    Returns:
        Control raiz da view de login.
    """
    def _on_login_success(usuario: Usuario) -> None:
        sessao.iniciar(usuario)
        _renderizar(page)

    login = LoginView(page, on_login_success=_on_login_success)
    return login.build()


def _build_shell(page: ft.Page) -> ft.Control:
    """Monta o shell autenticado (sidebar + topbar + área de conteúdo).

    Args:
        page: Página Flet ativa, repassada à sidebar para que o botão
            "Fechar Caixa" possa abrir o Dialog de confirmação.

    Returns:
        :class:`ft.Row` raiz do shell.
    """
    return ft.Row(
        controls=[
            _build_sidebar(page),
            ft.Column(
                controls=[
                    _build_topbar("Dashboard"),
                    _build_conteudo(),
                ],
                spacing=0,
                expand=True,
            ),
        ],
        spacing=0,
        expand=True,
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _build_sidebar(page: ft.Page) -> ft.Container:
    """Constrói a sidebar fixa de 240px (fundo preto).

    Args:
        page: Página Flet ativa, necessária para que o botão "Fechar
            Caixa" abra o Dialog de confirmação via :func:`_on_fechar_caixa`.
    """
    # Logo: ícone de talheres + wordmark.
    # Caminho de imagem é relativo a assets_dir (definido em main.py).
    logo = ft.Row(
        controls=[
            ft.Image(
                src="logo/logo.svg",
                width=28,
                height=28,
            ),
            ft.Text(
                "Ranggo",
                color=theme.COR_TERCIARIA,
                size=20,
                weight=ft.FontWeight.W_600,  # SemiBold
            ),
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
    )

    itens_menu = ft.Column(
        controls=[
            _build_item_menu(
                rotulo=rotulo,
                icone=icone,
                ativo=(i == 0),  # primeiro item (Dashboard) começa ativo
            )
            for i, (rotulo, icone) in enumerate(_ITENS_MENU)
        ],
        spacing=4,
    )

    # Rodapé: usuário mockado + botão "Fechar Caixa".
    # TODO Passo 8: substituir nome/perfil pelo usuário autenticado da sessão.
    rodape = ft.Column(
        controls=[
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.CircleAvatar(
                            content=ft.Icon(
                                icon=ft.Icons.PERSON,
                                color=theme.COR_TERCIARIA,
                                size=18,
                            ),
                            bgcolor=theme.COR_CINZA_600,
                            radius=16,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Usuário Padrão",
                                    color=theme.COR_TERCIARIA,
                                    size=theme.FONTE_TAMANHO_LABEL,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(
                                    "Sem login",
                                    color=theme.COR_CINZA_400,
                                    size=theme.FONTE_TAMANHO_HELPER,
                                ),
                            ],
                            spacing=0,
                            tight=True,
                        ),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding.symmetric(horizontal=4, vertical=8),
            ),
            ft.ElevatedButton(
                content="Fechar Caixa",
                icon=ft.Icons.LOGOUT,
                color=theme.COR_TERCIARIA,
                bgcolor=theme.COR_ERRO,
                height=theme.ALTURA_BOTAO,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(
                        radius=theme.BORDER_RADIUS_BOTAO,
                    ),
                ),
                # Largura útil da sidebar: LARGURA_SIDEBAR - 2 * padding lateral
                # (16 de cada lado, definido no Container raiz da sidebar).
                width=theme.LARGURA_SIDEBAR - 2 * 16,
                on_click=lambda e: _on_fechar_caixa(page),
            ),
        ],
        spacing=8,
    )

    return ft.Container(
        width=theme.LARGURA_SIDEBAR,
        bgcolor=theme.COR_SECUNDARIA,  # preto
        padding=ft.Padding.symmetric(horizontal=16, vertical=24),
        content=ft.Column(
            controls=[
                logo,
                ft.Container(height=24),  # respiro entre logo e menu
                itens_menu,
                ft.Container(expand=True),  # empurra rodapé para baixo
                rodape,
            ],
            spacing=0,
            expand=True,
        ),
    )


def _build_item_menu(
    rotulo: str,
    icone: ft.IconData,
    ativo: bool = False,
) -> ft.Container:
    """Constrói um item de menu da sidebar.

    Args:
        rotulo: Texto exibido ao lado do ícone.
        icone: Constante de :class:`ft.Icons` a renderizar.
        ativo: Se ``True``, item recebe fundo laranja e texto branco
            (estado selecionado). Caso contrário, fundo transparente
            com hover sutil.

    Returns:
        :class:`ft.Container` configurado para representar o item.
    """
    cor_texto = theme.COR_TERCIARIA
    bg = theme.COR_PRIMARIA if ativo else None

    # Item "Cadastros" recebe chevron à direita para sinalizar submenu futuro.
    trailing: ft.Control | None = None
    if rotulo == "Cadastros":
        trailing = ft.Icon(
            icon=ft.Icons.CHEVRON_RIGHT,
            color=theme.COR_CINZA_400,
            size=18,
        )

    conteudo_row = ft.Row(
        controls=[
            ft.Icon(icon=icone, color=cor_texto, size=20),
            ft.Text(
                rotulo,
                color=cor_texto,
                size=theme.FONTE_TAMANHO_LABEL,
                weight=ft.FontWeight.W_500,
                expand=True,
            ),
        ]
        + ([trailing] if trailing is not None else []),
        spacing=12,
    )

    return ft.Container(
        content=conteudo_row,
        bgcolor=bg,
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        border_radius=theme.BORDER_RADIUS_BOTAO,
        ink=True,  # ripple ao clicar — feedback visual mesmo sem callback
    )


# ---------------------------------------------------------------------------
# Topbar
# ---------------------------------------------------------------------------

def _build_topbar(titulo: str) -> ft.Container:
    """Constrói a topbar (64px, fundo branco, borda inferior cinza)."""
    titulo_widget = ft.Text(
        titulo,
        size=theme.FONTE_TAMANHO_TITULO_PRINCIPAL,
        weight=ft.FontWeight.W_600,
        color=theme.COR_SECUNDARIA,
    )

    # Ações à direita: ícone de notificação + botão "+ Nova Venda".
    # Placeholders visuais; sem callback nesta fase.
    acoes_direita = ft.Row(
        controls=[
            ft.IconButton(
                icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                icon_color=theme.COR_CINZA_600,
            ),
            ft.ElevatedButton(
                content="Nova Venda",
                icon=ft.Icons.ADD,
                color=theme.COR_TERCIARIA,
                bgcolor=theme.COR_PRIMARIA,
                height=theme.ALTURA_BOTAO,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(
                        radius=theme.BORDER_RADIUS_BOTAO,
                    ),
                ),
            ),
        ],
        spacing=12,
        alignment=ft.MainAxisAlignment.END,
    )

    return ft.Container(
        height=theme.ALTURA_TOPBAR,
        bgcolor=theme.COR_TERCIARIA,
        padding=ft.Padding.symmetric(horizontal=24, vertical=8),
        border=ft.Border.only(
            bottom=ft.BorderSide(width=1, color=theme.COR_CINZA_200),
        ),
        content=ft.Row(
            controls=[
                titulo_widget,
                ft.Container(expand=True),
                acoes_direita,
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


# ---------------------------------------------------------------------------
# Área de conteúdo
# ---------------------------------------------------------------------------

def _build_conteudo() -> ft.Container:
    """Área de conteúdo da Fase 0: card central 'Fundação OK'."""
    card = ft.Container(
        width=480,
        bgcolor=theme.COR_TERCIARIA,
        border_radius=theme.BORDER_RADIUS_CARD,
        padding=theme.PADDING_CARD,
        border=ft.Border.all(width=1, color=theme.COR_CINZA_200),
        content=ft.Column(
            controls=[
                ft.Icon(
                    icon=ft.Icons.CHECK_CIRCLE,
                    color=theme.COR_SUCESSO,
                    size=56,
                ),
                ft.Container(height=8),
                ft.Text(
                    "Fundação OK",
                    size=theme.FONTE_TAMANHO_TITULO_PRINCIPAL,
                    weight=ft.FontWeight.W_600,
                    color=theme.COR_SECUNDARIA,
                ),
                ft.Text(
                    "Banco inicializado, identidade visual aplicada.",
                    size=theme.FONTE_TAMANHO_LABEL,
                    color=theme.COR_CINZA_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=16),
                ft.Text(
                    "Ranggo · v0.1.0 (Fase 0)",
                    size=theme.FONTE_TAMANHO_HELPER,
                    color=theme.COR_CINZA_400,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    return ft.Container(
        bgcolor=theme.COR_CINZA_100,
        padding=32,
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=card,
    )


# ---------------------------------------------------------------------------
# Logout (Dialog de confirmação)
# ---------------------------------------------------------------------------

def _on_fechar_caixa(page: ft.Page) -> None:
    """Abre Dialog de confirmação; se confirmado, desloga e volta ao Login.

    Args:
        page: Página Flet ativa, usada para abrir/fechar o Dialog e para
            re-renderizar após o logout.
    """
    # Em Flet 0.85.1 a API correta é page.show_dialog(dialog) /
    # page.pop_dialog() — page.open()/page.close() não existem nesta
    # versão (foram introduzidos em uma release mais nova).
    def _confirmar(e: ft.ControlEvent) -> None:
        page.pop_dialog()
        sessao.encerrar()
        _renderizar(page)

    def _cancelar(e: ft.ControlEvent) -> None:
        page.pop_dialog()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Fechar Caixa"),
        content=ft.Text(
            "Deseja realmente fechar o caixa e sair do sistema?"
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=_cancelar),
            ft.ElevatedButton(
                content="Fechar Caixa",
                on_click=_confirmar,
                bgcolor=theme.COR_ERRO,
                color=theme.COR_TERCIARIA,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(
                        radius=theme.BORDER_RADIUS_BOTAO,
                    ),
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)
