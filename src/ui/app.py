"""Entry point da UI: configura janela, tema e monta o shell visual.

A função :func:`main` é o alvo de ``ft.app(target=...)`` chamado em
``main.py``. Não acessa banco nem executa lógica de negócio — sua
única responsabilidade é a camada visual:

    * Aplica o :class:`ft.Theme` global (via :func:`theme.build_flet_theme`).
    * Configura a janela (título, tamanho mínimo, maximizada).
    * Monta o shell: sidebar 240px preta + topbar 64px branca + área
      de conteúdo cinza com o card central "Fundação OK".

Itens da sidebar são placeholders visuais — nenhum callback funcional
nesta fase. Roteamento e injeção de views entram na Fase 1.
"""

from __future__ import annotations

import os

import flet as ft

from src.database.connection import engine
from src.ui import theme


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

    Aplica tema, configura a janela e adiciona o shell visual à página.
    Chamada por ``ft.app(target=main)`` no ``main.py``.

    Args:
        page: Página fornecida pelo runtime do Flet.
    """
    # --- Tema e configuração de janela ---
    page.title = "Ranggo"
    page.theme = theme.build_flet_theme()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = theme.COR_CINZA_100
    page.padding = 0  # shell ocupa 100% da viewport; padding é interno por área.

    # PDV exige espaço para layout de 3 colunas — abaixo de 1280×720 quebra.
    page.window.min_width = 1280
    page.window.min_height = 720
    page.window.maximized = True
    # Caminho relativo a assets_dir (definido em main.py).
    page.window.icon = "logo/logo.ico"

    # --- Shutdown limpo ---
    # Sem isso, ft.run() leva ~2s para retornar após o usuário fechar a janela
    # porque o subprocesso Flutter (flet.exe) demora a desmontar gracefully.
    # Durante esse delay, SQLite locks e portas internas ficam presos — a
    # próxima execução trava em "Working..." enquanto o sistema espera os
    # recursos liberarem. Forçar saída no evento CLOSE elimina o intervalo.
    page.window.prevent_close = False

    def _on_window_event(e: ft.WindowEvent) -> None:
        if e.type == ft.WindowEventType.CLOSE:
            engine.dispose()
            page.window.destroy()
            # os._exit em vez de sys.exit: bypassa qualquer cleanup pendente
            # do runtime do Flet/Flutter. dispose() acima já liberou o engine.
            os._exit(0)

    page.window.on_event = _on_window_event

    # --- Shell visual ---
    shell = ft.Row(
        controls=[
            _build_sidebar(),
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

    page.add(shell)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _build_sidebar() -> ft.Container:
    """Constrói a sidebar fixa de 240px (fundo preto)."""
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

    # Rodapé: usuário mockado + botão "Finalizar Turno".
    # TODO Fase 1: substituir nome/perfil pelo usuário autenticado da session.
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
                content="Finalizar Turno",
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
