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
from src.ui import components, theme
from src.ui.views.cadastros.form_categoria_view import FormCategoriaView
from src.ui.views.cadastros.lista_categorias_view import ListaCategoriasView
from src.ui.views.cadastros.lista_unidades_medida_view import ListaUnidadesMedidaView
from src.ui.views.login_view import LoginView
from src.ui.views.usuarios.form_usuario_view import FormUsuarioView
from src.ui.views.usuarios.lista_usuarios_view import ListaUsuariosView


# Itens do menu lateral. Ordem reflete o protótipo prototipos/02-dashboard.png.
# (rotulo, icone, view_id). ``view_id=None`` → item placeholder visual sem
# navegação (será implementado em fases futuras). Itens condicionais de
# perfil são filtrados em ``_build_sidebar`` (ex.: "Usuários" só p/ Admin).
#
# "Cadastros" é tratado fora desta lista — é accordion com submenu (ver
# ``_SUBITENS_CADASTROS`` e ``_build_item_cadastros``). Sua posição lógica
# na ordem fica entre "Delivery" e "Estoque".
_ITENS_MENU: list[tuple[str, ft.IconData, str | None]] = [
    ("Dashboard", ft.Icons.SPACE_DASHBOARD, "dashboard"),
    ("Vendas", ft.Icons.POINT_OF_SALE, None),         # Fase 3
    ("Comandas", ft.Icons.RECEIPT_LONG, None),        # Fase 4
    ("Delivery", ft.Icons.DELIVERY_DINING, None),     # Fase 5
    # ↑ "Cadastros" injetado aqui pelo _build_sidebar (accordion).
    ("Estoque", ft.Icons.INVENTORY_2, None),          # Fase 2
    ("Relatórios", ft.Icons.BAR_CHART, None),         # Fase 5
    ("Usuários", ft.Icons.PEOPLE, "usuarios_lista"),  # Fase 1 (só Admin)
    ("Configurações", ft.Icons.SETTINGS, None),       # Fase 5
]


# Subitens do accordion "Cadastros". Visíveis a TODOS os perfis (Admin,
# Gerente, Caixa) — cadastros são operação diária. (rotulo, icone, view_id).
# ``view_id=None`` → subitem placeholder (clicável sem efeito) até a fase
# correspondente. O subitem "Categorias" liga ao Passo 1 da Fase 2.
_SUBITENS_CADASTROS: list[tuple[str, ft.IconData, str | None]] = [
    ("Categorias", ft.Icons.LABEL, "cadastros_categorias_lista"),
    ("Unidades de Medida", ft.Icons.STRAIGHTEN, "cadastros_unidades_lista"),
    ("Clientes", ft.Icons.PEOPLE_OUTLINE, None),          # Passo 4
    ("Fornecedores", ft.Icons.LOCAL_SHIPPING, None),      # Passo 3
    ("Produtos", ft.Icons.INVENTORY_2, None),             # Passo 5
    ("Insumos", ft.Icons.GRAIN, None),                    # Passo 6
    ("Pratos", ft.Icons.RESTAURANT_MENU, None),           # Passo 7
    ("Fichas Técnicas", ft.Icons.DESCRIPTION, None),      # Passo 8
]


# Conjunto de ``view_id`` que pertencem ao módulo "Cadastros" — usado para
# destacar o item pai em laranja quando alguma view-filha está ativa.
_VIEWS_CADASTROS: frozenset[str] = frozenset({
    "cadastros_categorias_lista",
    "cadastros_categorias_form",
    "cadastros_unidades_lista",
})


# ---------------------------------------------------------------------------
# Estado de navegação (módulo-level, mesmo padrão da ``sessao``)
#
# É estado **de UI** (qual view está visível), não de autenticação. Vive
# aqui em ``app.py`` em vez de ``sessao.py`` porque é específico da
# camada de apresentação e tem acoplamento com ``_renderizar``.
# ---------------------------------------------------------------------------

# View atualmente em exibição. Resetada para "dashboard" a cada logout.
_view_atual: str = "dashboard"

# ``usuario_id`` repassado ao :class:`FormUsuarioView` em modo EDITAR.
# ``None`` significa modo CRIAR (quando ``_view_atual == "usuarios_form"``).
_form_usuario_id: int | None = None

# ``categoria_id`` repassado ao :class:`FormCategoriaView` em modo EDITAR.
# ``None`` significa modo CRIAR (quando ``_view_atual ==
# "cadastros_categorias_form"``).
_form_categoria_id: int | None = None

# Estado de expansão do accordion "Cadastros" na sidebar. Toggle manual ao
# clicar no item. Auto-expande quando entra numa view-filha de Cadastros
# (ver ``_navegar``). Auto-recolhe no logout (junto com ``_view_atual``).
_cadastros_expandido: bool = False


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
        4. Navegação interna do shell (via :func:`_navegar`).

    Limpa ``page.controls`` antes de adicionar a nova árvore e chama
    ``page.update`` para refletir a troca.

    Args:
        page: Página Flet ativa.
    """
    global _view_atual, _form_usuario_id, _form_categoria_id, _cadastros_expandido

    page.controls.clear()
    if sessao.esta_logado():
        page.add(_build_shell(page))
    else:
        # Logout: reseta estado de navegação para que o próximo login
        # comece sempre no Dashboard, não na última view visitada.
        _view_atual = "dashboard"
        _form_usuario_id = None
        _form_categoria_id = None
        _cadastros_expandido = False
        page.add(_build_login(page))
    page.update()


def _navegar(
    page: ft.Page,
    nova_view: str,
    form_id: int | None = None,
) -> None:
    """Troca a view ativa do shell e re-renderiza.

    Auto-expande o accordion "Cadastros" se ``nova_view`` pertence ao
    módulo de Cadastros (evita o efeito visual de o usuário "perder" o
    contexto da navegação quando entra direto numa view de Cadastros).

    Args:
        page: Página Flet ativa.
        nova_view: Identificador da view destino. Valores aceitos:
            ``"dashboard"``, ``"usuarios_lista"``, ``"usuarios_form"``,
            ``"cadastros_categorias_lista"``, ``"cadastros_categorias_form"``.
        form_id: Em forms (``"usuarios_form"``,
            ``"cadastros_categorias_form"``), ``None`` para modo CRIAR
            e ``int`` para EDITAR. Roteado para o ``_form_*_id`` correto
            baseado em ``nova_view``. Ignorado nas demais views.
    """
    global _view_atual, _form_usuario_id, _form_categoria_id, _cadastros_expandido
    _view_atual = nova_view

    # Roteia ``form_id`` para o estado correto baseado na view destino.
    # Quando virarem 3+ forms simultâneos (Passo 5+), provavelmente vale
    # virar dict {view_id → form_id}. Por enquanto if/elif é mais legível.
    if nova_view == "usuarios_form":
        _form_usuario_id = form_id
    elif nova_view == "cadastros_categorias_form":
        _form_categoria_id = form_id

    # Auto-expande o accordion quando navega para uma view de Cadastros.
    if nova_view in _VIEWS_CADASTROS:
        _cadastros_expandido = True

    _renderizar(page)


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
    """Monta o shell autenticado (sidebar + área de conteúdo dinâmica).

    A área de conteúdo é despachada por :func:`_build_conteudo` baseado
    em :data:`_view_atual`. Views internas (Usuários) trazem o próprio
    page header e dispensam a topbar do shell; o Dashboard mantém a
    topbar do protótipo original.

    Args:
        page: Página Flet ativa, repassada à sidebar e às views para
            ``show_dialog``, ``page.update`` e o botão "Fechar Caixa".

    Returns:
        :class:`ft.Row` raiz do shell.
    """
    return ft.Row(
        controls=[
            _build_sidebar(page),
            _build_conteudo(page),
        ],
        spacing=0,
        expand=True,
    )


def _build_conteudo(page: ft.Page) -> ft.Control:
    """Roteador da área central: escolhe a view por :data:`_view_atual`.

    Args:
        page: Página Flet ativa, repassada às views.

    Returns:
        Control raiz da view selecionada.
    """
    if _view_atual == "usuarios_lista":
        return ListaUsuariosView(
            page,
            on_novo_usuario=lambda: _navegar(page, "usuarios_form", None),
            on_editar_usuario=lambda uid: _navegar(page, "usuarios_form", uid),
        ).build()

    if _view_atual == "usuarios_form":
        return FormUsuarioView(
            page,
            usuario_id=_form_usuario_id,
            on_voltar=lambda: _navegar(page, "usuarios_lista"),
            on_salvar=lambda: _navegar(page, "usuarios_lista"),
        ).build()

    if _view_atual == "cadastros_categorias_lista":
        return ListaCategoriasView(
            page,
            on_nova=lambda: _navegar(page, "cadastros_categorias_form"),
            on_editar=lambda cid: _navegar(
                page, "cadastros_categorias_form", form_id=cid
            ),
        ).build()

    if _view_atual == "cadastros_categorias_form":
        return FormCategoriaView(
            page,
            categoria_id=_form_categoria_id,
            on_voltar=lambda: _navegar(page, "cadastros_categorias_lista"),
            on_salvar=lambda: _navegar(page, "cadastros_categorias_lista"),
        ).build()

    if _view_atual == "cadastros_unidades_lista":
        return ListaUnidadesMedidaView(page).build()

    # Default: Dashboard. Cada view do shell carrega a própria topbar
    # via ``components.topbar(...)`` (regra cravada: chrome consistente
    # entre Dashboard, Lista de Usuários, Form de Usuário, etc.).
    return _build_dashboard_placeholder()


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

    # ``usuario`` é resolvido logo abaixo (rodapé) — antecipo aqui só
    # o perfil para filtrar itens condicionais ao papel.
    usuario_logado = sessao.usuario_atual()
    eh_admin = (
        usuario_logado is not None
        and usuario_logado.perfil.nome == "Admin"
    )

    controles_menu: list[ft.Control] = []
    for rotulo, icone, view_id in _ITENS_MENU:
        # "Usuários" é restrito a Admin (gating na UI; service também
        # protege ações específicas via PermissaoNegadaError).
        if rotulo == "Usuários" and not eh_admin:
            continue

        if view_id == "usuarios_lista":
            # Item ativo tanto na lista quanto no form (mesma seção).
            ativo = _view_atual in ("usuarios_lista", "usuarios_form")
        else:
            ativo = view_id is not None and view_id == _view_atual

        # Itens placeholder (view_id None) ficam clicáveis sem efeito —
        # quando suas fases chegarem, basta plugar o ``_navegar``.
        if view_id is not None:
            # Capturar view_id por default-arg para não fechar sobre a
            # variável de loop (clássico).
            on_click = lambda e, v=view_id: _navegar(page, v)
        else:
            on_click = None

        controles_menu.append(
            _build_item_menu(
                rotulo=rotulo,
                icone=icone,
                ativo=ativo,
                on_click=on_click,
            )
        )

        # Injeta o accordion "Cadastros" logo após "Delivery" (entre
        # "Delivery" e "Estoque" na ordem visual do menu).
        if rotulo == "Delivery":
            controles_menu.extend(_build_item_cadastros(page))

    itens_menu = ft.Column(controls=controles_menu, spacing=4)

    # Rodapé: usuário autenticado da sessão + botão "Fechar Caixa".
    # ``_build_sidebar`` só é chamado de dentro de ``_build_shell``, que
    # por sua vez só roda se ``sessao.esta_logado()``. Logo, ``usuario``
    # nunca é None aqui — se for, é bug e o AttributeError deve aparecer.
    usuario = sessao.usuario_atual()
    inicial = usuario.nome[0].upper() if usuario.nome else "?"

    rodape = ft.Column(
        controls=[
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.CircleAvatar(
                            content=ft.Text(
                                inicial,
                                color=theme.COR_TERCIARIA,
                                size=16,
                                weight=ft.FontWeight.W_700,  # Bold
                            ),
                            bgcolor=theme.COR_PRIMARIA,
                            radius=20,  # 40px de diâmetro
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    usuario.nome,
                                    color=theme.COR_TERCIARIA,
                                    size=theme.FONTE_TAMANHO_LABEL,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(
                                    usuario.perfil.nome,
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


def _toggle_cadastros(page: ft.Page) -> None:
    """Toggle do accordion "Cadastros" (clique no item pai).

    Inverte ``_cadastros_expandido`` e re-renderiza. Não muda
    ``_view_atual`` — clicar no item pai só expande/recolhe, não navega.
    """
    global _cadastros_expandido
    _cadastros_expandido = not _cadastros_expandido
    _renderizar(page)


def _build_item_cadastros(page: ft.Page) -> list[ft.Control]:
    """Constrói o item "Cadastros" (accordion) + subitens se expandido.

    O item pai tem comportamento próprio (toggle do accordion), por isso
    é construído fora do loop padrão do menu. Visível a TODOS os perfis
    (cadastros são operação diária — cravado nas decisões da Fase 2).

    Returns:
        Lista de :class:`ft.Control` na ordem: [item pai, subitens...].
        Quando recolhido, retorna apenas [item pai].
    """
    # Item pai destacado em laranja quando expandido OU quando alguma
    # view-filha está ativa. Cravado nas decisões da Fase 2 (item 7).
    em_view_filha = _view_atual in _VIEWS_CADASTROS
    pai_ativo = _cadastros_expandido or em_view_filha

    # Ícone da seta: > recolhido, ▾ expandido.
    icone_seta = (
        ft.Icons.ARROW_DROP_DOWN
        if _cadastros_expandido
        else ft.Icons.CHEVRON_RIGHT
    )

    item_pai = _build_item_menu_com_trailing(
        rotulo="Cadastros",
        icone=ft.Icons.FOLDER,
        ativo=pai_ativo,
        on_click=lambda e: _toggle_cadastros(page),
        trailing_icon=icone_seta,
    )

    controles: list[ft.Control] = [item_pai]

    if _cadastros_expandido:
        for sub_rotulo, sub_icone, sub_view_id in _SUBITENS_CADASTROS:
            sub_ativo = (
                sub_view_id is not None and sub_view_id == _view_atual
            )
            # Subitem "Categorias" também fica ativo quando estamos no
            # form de Categoria (mesma seção lógica).
            if sub_view_id == "cadastros_categorias_lista":
                sub_ativo = _view_atual in (
                    "cadastros_categorias_lista",
                    "cadastros_categorias_form",
                )

            if sub_view_id is not None:
                sub_on_click = (
                    lambda e, v=sub_view_id: _navegar(page, v)
                )
            else:
                sub_on_click = None

            controles.append(
                _build_subitem_cadastros(
                    rotulo=sub_rotulo,
                    icone=sub_icone,
                    ativo=sub_ativo,
                    on_click=sub_on_click,
                )
            )

    return controles


def _build_subitem_cadastros(
    rotulo: str,
    icone: ft.IconData,
    ativo: bool = False,
    on_click=None,
) -> ft.Container:
    """Subitem do accordion Cadastros — menor que o item principal.

    Estilo (cravado nas decisões da Fase 2):
        * Altura ~36px (vs 48px do principal).
        * Padding-left aumentado (~32px) para sensação de indent.
        * Ícone 16px (vs 20px do principal).
        * Texto Inter Regular 13px (vs 14px do principal).
        * Cor: COR_CINZA_400 se inativo, COR_TERCIARIA se ativo
          (sobre fundo laranja).
    """
    cor_texto = theme.COR_TERCIARIA if ativo else theme.COR_CINZA_400
    bg = theme.COR_PRIMARIA if ativo else None

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(icon=icone, color=cor_texto, size=16),
                ft.Text(
                    rotulo,
                    color=cor_texto,
                    size=13,
                    weight=ft.FontWeight.W_400,
                    expand=True,
                ),
            ],
            spacing=10,
        ),
        bgcolor=bg,
        padding=ft.Padding.only(left=32, right=12, top=8, bottom=8),
        border_radius=theme.BORDER_RADIUS_BOTAO,
        ink=True,
        on_click=on_click,
    )


def _build_item_menu_com_trailing(
    rotulo: str,
    icone: ft.IconData,
    ativo: bool = False,
    on_click=None,
    trailing_icon: ft.IconData | None = None,
) -> ft.Container:
    """Variante de :func:`_build_item_menu` com trailing icon customizável.

    Usada pelo item "Cadastros" (accordion) para mostrar seta ▾ vs >.
    Quando ``trailing_icon=None``, comporta-se como :func:`_build_item_menu`.
    """
    cor_texto = theme.COR_TERCIARIA
    bg = theme.COR_PRIMARIA if ativo else None

    controls: list[ft.Control] = [
        ft.Icon(icon=icone, color=cor_texto, size=20),
        ft.Text(
            rotulo,
            color=cor_texto,
            size=theme.FONTE_TAMANHO_LABEL,
            weight=ft.FontWeight.W_500,
            expand=True,
        ),
    ]
    if trailing_icon is not None:
        controls.append(
            ft.Icon(
                icon=trailing_icon,
                color=theme.COR_TERCIARIA if ativo else theme.COR_CINZA_400,
                size=18,
            )
        )

    return ft.Container(
        content=ft.Row(controls=controls, spacing=12),
        bgcolor=bg,
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        border_radius=theme.BORDER_RADIUS_BOTAO,
        ink=True,
        on_click=on_click,
    )


def _build_item_menu(
    rotulo: str,
    icone: ft.IconData,
    ativo: bool = False,
    on_click=None,
) -> ft.Container:
    """Constrói um item de menu da sidebar.

    Args:
        rotulo: Texto exibido ao lado do ícone.
        icone: Constante de :class:`ft.Icons` a renderizar.
        ativo: Se ``True``, item recebe fundo laranja e texto branco
            (estado selecionado). Caso contrário, fundo transparente
            com hover sutil.
        on_click: Handler ``(e) -> None``. Quando ``None``, o item
            continua exibindo ripple mas não navega (placeholder de
            features futuras).

    Returns:
        :class:`ft.Container` configurado para representar o item.
    """
    cor_texto = theme.COR_TERCIARIA
    bg = theme.COR_PRIMARIA if ativo else None

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
        ],
        spacing=12,
    )

    return ft.Container(
        content=conteudo_row,
        bgcolor=bg,
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        border_radius=theme.BORDER_RADIUS_BOTAO,
        ink=True,  # ripple ao clicar — feedback visual mesmo sem callback
        on_click=on_click,
    )


# ---------------------------------------------------------------------------
# Área de conteúdo
# ---------------------------------------------------------------------------

def _build_dashboard_placeholder() -> ft.Control:
    """Dashboard placeholder com topbar padronizada + card 'Fundação OK'.

    Topbar via :func:`components.topbar` para garantir chrome consistente
    com Lista de Usuários, Form de Usuário e demais views do shell.
    O botão "Nova Venda" é placeholder (sem callback) até a Fase 3.
    """
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

    area_central = ft.Container(
        bgcolor=theme.COR_CINZA_100,
        padding=32,
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=card,
    )

    return ft.Column(
        controls=[
            components.topbar(
                "Dashboard",
                acao_direita=components.botao_primario(
                    "Nova Venda",
                    on_click=lambda e: None,  # placeholder Fase 3
                    icone=ft.Icons.ADD,
                ),
            ),
            area_central,
        ],
        spacing=0,
        expand=True,
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
    # versão (foram introduzidos em uma release mais nova). Usamos o
    # componente padrão para manter o visual consistente com os demais
    # dialogs de confirmação do sistema (Desativar/Ativar usuário, etc).
    def _confirmar(e: ft.ControlEvent) -> None:
        page.pop_dialog()
        sessao.encerrar()
        _renderizar(page)

    def _cancelar(e: ft.ControlEvent) -> None:
        page.pop_dialog()

    # Fechar Caixa é apenas logout — não destrói dado nenhum. Usa
    # laranja (padrão do app). Vermelho fica reservado para destrutivas
    # irreversíveis (Desativar, Excluir, Cancelar Venda).
    page.show_dialog(
        components.dialog_confirmacao(
            titulo="Fechar Caixa",
            mensagem="Deseja realmente fechar o caixa e sair do sistema?",
            texto_botao_confirmar="Fechar Caixa",
            cor_botao_confirmar=theme.COR_PRIMARIA,
            on_confirmar=_confirmar,
            on_cancelar=_cancelar,
        )
    )
