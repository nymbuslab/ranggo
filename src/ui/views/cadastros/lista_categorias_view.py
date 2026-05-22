"""Tela de listagem de Categorias — Passo 1 da Fase 2.

Referências visuais:
    * ``prototipos/03-listagem-cadastro.png`` (estrutura geral).
    * Mesmo padrão estrutural de :class:`ListaUsuariosView`, sem
      colunas/funcionalidades específicas de usuário (perfil, login,
      trocar senha).

Estrutura:
    * Topbar padronizada (``components.topbar``) com botão "+ Nova Categoria".
    * Filter bar com busca local (nome) e toggle "Mostrar inativas".
    * Tabela custom com colunas: Nome, Descrição, Status, Ações.
    * Footer com contador total filtrado.

Visível a todos os perfis (cravado nas decisões da Fase 2 — cadastros
são operação diária).
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from src.database.connection import get_session
from src.database.models.categoria import Categoria
from src.services.categoria_service import CategoriaService
from src.ui import components, theme


# Cores específicas dos badges de status — mesma paleta de ListaUsuariosView.
_BADGE_ATIVO_BG: str = "#DCFCE7"      # green-100
_BADGE_ATIVO_TEXTO: str = "#15803D"   # green-700


# Larguras de colunas fixas (NOME usa o espaço restante).
_COL_DESCRICAO_WIDTH: int = 360
_COL_STATUS_WIDTH: int = 120
_COL_ACOES_WIDTH: int = 120

# Limite de caracteres da descrição na tabela (truncar com "...").
_MAX_DESCRICAO_TABELA: int = 60


class ListaCategoriasView:
    """View de listagem de Categorias (Passo 1 da Fase 2)."""

    def __init__(
        self,
        page: ft.Page,
        on_nova: Callable[[], None],
        on_editar: Callable[[int], None],
    ) -> None:
        """Cria a view.

        Args:
            page: Página Flet onde a view será montada (usada para
                ``page.update`` e ``page.show_dialog``).
            on_nova: Callback do botão "+ Nova Categoria".
            on_editar: Callback do ícone de edição na linha,
                recebe ``categoria_id``.
        """
        self._page = page
        self._on_nova = on_nova
        self._on_editar = on_editar

        # Estado em memória.
        self._categorias: list[Categoria] = []
        self._busca: str = ""
        self._mostrar_inativas: bool = False

        # Referências aos controles atualizados em ``_filtrar_e_renderizar``.
        self._campo_busca: ft.TextField | None = None
        self._switch_inativas: ft.Switch | None = None
        self._corpo_tabela: ft.Column | None = None
        self._texto_total: ft.Text | None = None

    # ------------------------------------------------------------------
    # Construção da árvore
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Constrói a árvore de Controls e retorna a raiz."""
        self._campo_busca = ft.TextField(
            hint_text="Buscar por nome...",
            prefix_icon=ft.Icons.SEARCH,
            width=320,
            height=40,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border_radius=theme.BORDER_RADIUS_INPUT,
            border_color=theme.COR_CINZA_200,
            focused_border_color=theme.COR_PRIMARIA,
            text_size=theme.FONTE_TAMANHO_CORPO,
            on_change=self._on_busca_change,
        )

        self._switch_inativas = ft.Switch(
            value=False,
            active_color=theme.COR_PRIMARIA,
            on_change=self._on_switch_change,
        )

        self._corpo_tabela = ft.Column(
            controls=[],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self._texto_total = ft.Text(
            "Total: 0 categorias",
            size=theme.FONTE_TAMANHO_HELPER + 1,  # 13px
            color=theme.COR_CINZA_400,
            weight=ft.FontWeight.W_400,
        )

        # Header via topbar padrão do shell.
        page_header = components.topbar(
            "Categorias",
            acao_direita=components.botao_primario(
                "Nova Categoria",
                on_click=lambda e: self._on_nova(),
                icone=ft.Icons.ADD,
            ),
        )

        # Filter bar (busca + toggle).
        filter_bar = ft.Container(
            height=64,
            bgcolor=theme.COR_TERCIARIA,
            padding=ft.Padding.symmetric(horizontal=24, vertical=12),
            border=ft.Border.only(
                bottom=ft.BorderSide(width=1, color=theme.COR_CINZA_200),
            ),
            content=ft.Row(
                controls=[
                    self._campo_busca,
                    ft.Container(expand=True),
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Mostrar inativas",
                                size=theme.FONTE_TAMANHO_LABEL,
                                color=theme.COR_CINZA_600,
                                weight=ft.FontWeight.W_500,
                            ),
                            self._switch_inativas,
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Tabela: header + body (rows scrolláveis) + footer.
        tabela = ft.Container(
            bgcolor=theme.COR_TERCIARIA,
            border=ft.Border.all(width=1, color=theme.COR_CINZA_200),
            border_radius=theme.BORDER_RADIUS_CARD,
            expand=True,
            content=ft.Column(
                controls=[
                    self._build_header_tabela(),
                    ft.Container(
                        expand=True,
                        content=self._corpo_tabela,
                    ),
                    self._build_footer_tabela(),
                ],
                spacing=0,
                expand=True,
            ),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        area_tabela = ft.Container(
            bgcolor=theme.COR_CINZA_100,
            padding=ft.Padding.all(24),
            expand=True,
            content=tabela,
        )

        raiz = ft.Container(
            bgcolor=theme.COR_CINZA_100,
            expand=True,
            content=ft.Column(
                controls=[page_header, filter_bar, area_tabela],
                spacing=0,
                expand=True,
            ),
        )

        # Carrega dados e renderiza.
        self._carregar_categorias()
        self._filtrar_e_renderizar(atualizar_pagina=False)

        return raiz

    def recarregar(self) -> None:
        """Recarrega categorias do banco e re-renderiza."""
        self._carregar_categorias()
        self._filtrar_e_renderizar()

    # ------------------------------------------------------------------
    # Sub-builders
    # ------------------------------------------------------------------

    def _build_header_tabela(self) -> ft.Container:
        """Cabeçalho da tabela com nomes de coluna em uppercase."""
        def col(texto: str, width: int | None = None, expand: bool = False,
                alinhamento: ft.TextAlign = ft.TextAlign.LEFT) -> ft.Control:
            t = ft.Text(
                texto.upper(),
                size=13,
                weight=ft.FontWeight.W_600,
                color=theme.COR_CINZA_600,
                text_align=alinhamento,
            )
            if expand:
                return ft.Container(content=t, expand=True)
            return ft.Container(content=t, width=width)

        return ft.Container(
            height=60,
            bgcolor=theme.COR_CINZA_100,
            padding=ft.Padding.symmetric(horizontal=24, vertical=0),
            border=ft.Border.only(
                bottom=ft.BorderSide(width=1, color=theme.COR_CINZA_200),
            ),
            content=ft.Row(
                controls=[
                    col("Nome", expand=True),
                    col("Descrição", width=_COL_DESCRICAO_WIDTH),
                    col("Status", width=_COL_STATUS_WIDTH),
                    col("Ações", width=_COL_ACOES_WIDTH,
                        alinhamento=ft.TextAlign.RIGHT),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
        )

    def _build_footer_tabela(self) -> ft.Container:
        """Rodapé com contador total filtrado."""
        return ft.Container(
            height=40,
            padding=ft.Padding.symmetric(horizontal=24, vertical=8),
            border=ft.Border.only(
                top=ft.BorderSide(width=1, color=theme.COR_CINZA_200),
            ),
            content=ft.Row(
                controls=[
                    ft.Container(expand=True),
                    self._texto_total,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _build_linha(self, categoria: Categoria, indice: int) -> ft.Container:
        """Constrói uma linha de dados da tabela.

        Args:
            categoria: A categoria renderizada.
            indice: Posição na lista filtrada (usado para zebra striping).
        """
        # Avatar circular laranja com inicial do nome.
        inicial = categoria.nome[0].upper() if categoria.nome else "?"
        avatar = ft.CircleAvatar(
            content=ft.Text(
                inicial,
                color=theme.COR_TERCIARIA,
                size=14,
                weight=ft.FontWeight.W_700,
            ),
            bgcolor=theme.COR_PRIMARIA,
            radius=16,  # 32px de diâmetro
        )

        col_nome = ft.Container(
            expand=True,
            content=ft.Row(
                controls=[
                    avatar,
                    ft.Text(
                        categoria.nome,
                        size=15,
                        weight=ft.FontWeight.W_500,
                        color=theme.COR_SECUNDARIA,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Descrição: trunca com "..." se passar do limite.
        descricao_texto = categoria.descricao or "—"
        if len(descricao_texto) > _MAX_DESCRICAO_TABELA:
            descricao_texto = descricao_texto[:_MAX_DESCRICAO_TABELA - 1] + "…"

        col_descricao = ft.Container(
            width=_COL_DESCRICAO_WIDTH,
            content=ft.Text(
                descricao_texto,
                size=14,
                color=theme.COR_CINZA_600 if categoria.descricao else theme.COR_CINZA_400,
                weight=ft.FontWeight.W_400,
            ),
        )

        col_status = ft.Container(
            width=_COL_STATUS_WIDTH,
            content=self._build_badge_status(categoria.ativo),
        )

        col_acoes = ft.Container(
            width=_COL_ACOES_WIDTH,
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=theme.COR_CINZA_600,
                        icon_size=18,
                        tooltip="Editar",
                        on_click=lambda e, cid=categoria.id: self._on_editar(cid),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.BLOCK if categoria.ativo else ft.Icons.PLAY_CIRCLE,
                        icon_color=theme.COR_CINZA_600,
                        icon_size=18,
                        tooltip="Desativar" if categoria.ativo else "Ativar",
                        on_click=lambda e, c=categoria: self._toggle_status(c),
                    ),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.END,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Zebra striping.
        bg = theme.COR_CINZA_100 if indice % 2 == 1 else theme.COR_TERCIARIA

        row = ft.Row(
            controls=[col_nome, col_descricao, col_status, col_acoes],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            height=64,
            bgcolor=bg,
            padding=ft.Padding.symmetric(horizontal=24, vertical=0),
            opacity=0.6 if not categoria.ativo else 1.0,
            content=row,
        )

    def _build_badge_status(self, ativo: bool) -> ft.Control:
        """Badge pill verde (ativa) ou cinza (inativa).

        Mesmo padrão de :class:`ListaUsuariosView._build_badge_status`.
        """
        if ativo:
            bg = _BADGE_ATIVO_BG
            texto = "Ativa"
            cor_texto = _BADGE_ATIVO_TEXTO
        else:
            bg = theme.COR_CINZA_100
            texto = "Inativa"
            cor_texto = theme.COR_CINZA_400

        badge = ft.Container(
            content=ft.Text(
                texto,
                size=12,
                weight=ft.FontWeight.W_600,
                color=cor_texto,
            ),
            bgcolor=bg,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            height=24,
            alignment=ft.Alignment.CENTER,
        )

        return ft.Container(
            content=badge,
            alignment=ft.Alignment.CENTER_LEFT,
        )

    # ------------------------------------------------------------------
    # Carga e filtros
    # ------------------------------------------------------------------

    def _carregar_categorias(self) -> None:
        """Busca a lista completa (incluindo inativas)."""
        with get_session() as session:
            service = CategoriaService(session)
            self._categorias = service.listar(incluir_inativas=True)

    def _filtrar_e_renderizar(self, atualizar_pagina: bool = True) -> None:
        """Reaplica filtros em memória e re-renderiza o corpo da tabela."""
        assert self._corpo_tabela is not None
        assert self._texto_total is not None

        filtradas = self._categorias
        if not self._mostrar_inativas:
            filtradas = [c for c in filtradas if c.ativo]

        busca = self._busca.strip().lower()
        if busca:
            filtradas = [c for c in filtradas if busca in c.nome.lower()]

        if not filtradas:
            self._corpo_tabela.controls = [self._build_estado_vazio()]
        else:
            self._corpo_tabela.controls = [
                self._build_linha(c, i) for i, c in enumerate(filtradas)
            ]

        sufixo = "" if len(filtradas) == 1 else "s"
        self._texto_total.value = f"Total: {len(filtradas)} categoria{sufixo}"

        if atualizar_pagina:
            self._page.update()

    def _build_estado_vazio(self) -> ft.Container:
        """Mensagem amigável quando não há categorias filtradas."""
        return ft.Container(
            height=120,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                controls=[
                    ft.Icon(
                        icon=ft.Icons.LABEL_OUTLINE,
                        color=theme.COR_CINZA_400,
                        size=32,
                    ),
                    ft.Text(
                        "Nenhuma categoria encontrada.",
                        size=14,
                        color=theme.COR_CINZA_400,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

    # ------------------------------------------------------------------
    # Handlers de filtro
    # ------------------------------------------------------------------

    def _on_busca_change(self, e: ft.ControlEvent) -> None:
        assert self._campo_busca is not None
        self._busca = self._campo_busca.value or ""
        self._filtrar_e_renderizar()

    def _on_switch_change(self, e: ft.ControlEvent) -> None:
        assert self._switch_inativas is not None
        self._mostrar_inativas = bool(self._switch_inativas.value)
        self._filtrar_e_renderizar()

    # ------------------------------------------------------------------
    # Toggle de status (ativar/desativar) com dialog
    # ------------------------------------------------------------------

    def _toggle_status(self, categoria: Categoria) -> None:
        """Abre dialog confirmando ativar/desativar; aplica via service.

        Cor do botão: LARANJA em ambos os casos. Categoria não é
        destrutivo-irreversível (cravado nas decisões — vermelho reservado
        para Desativar Usuário, Excluir, Cancelar Venda).
        """
        if categoria.ativo:
            titulo = "Desativar categoria"
            acao_label = "Desativar"
        else:
            titulo = "Ativar categoria"
            acao_label = "Ativar"

        mensagem = (
            f"Tem certeza que deseja {acao_label.lower()} '{categoria.nome}'?"
        )

        # Captura dados antes do session fechar.
        cid = categoria.id
        nome = categoria.nome
        descricao = categoria.descricao
        estava_ativa = categoria.ativo

        def _confirmar(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()
            try:
                with get_session() as session:
                    service = CategoriaService(session)
                    if estava_ativa:
                        service.desativar(cid)
                    else:
                        service.atualizar(cid, nome, descricao, True)
                self.recarregar()
            except Exception as ex:
                self._mostrar_erro(f"Erro inesperado: {ex}")

        def _cancelar(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            components.dialog_confirmacao(
                titulo=titulo,
                mensagem=mensagem,
                texto_botao_confirmar=acao_label,
                # Laranja para ambas as ações (categoria não é destrutiva
                # irreversível). Decisão cravada nas regras de design.
                cor_botao_confirmar=theme.COR_PRIMARIA,
                on_confirmar=_confirmar,
                on_cancelar=_cancelar,
            )
        )

    def _mostrar_erro(self, mensagem: str) -> None:
        """Exibe SnackBar vermelho com a mensagem de erro."""
        self._page.show_dialog(components.snackbar_erro(mensagem))
