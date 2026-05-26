"""Tela de listagem de Fornecedores — Passo 3 da Fase 2.

Referencias visuais:
    * ``prototipos/03-listagem-cadastro.png`` (estrutura geral).
    * Mesmo padrao estrutural de :class:`ListaCategoriasView`, com
      colunas extras especificas de Fornecedor (CNPJ, Telefone, Contato).

Estrutura:
    * Topbar padronizada (``components.topbar``) com botao
      "+ Novo Fornecedor".
    * Filter bar com busca local (nome OU CNPJ) e toggle "Mostrar
      inativos".
    * Tabela custom com colunas: Nome, CNPJ, Telefone, Contato, Status,
      Acoes.
    * Footer com contador total filtrado.

Busca por CNPJ tolera mascara — usuario digitando "12.345" acha "12345"
no banco porque a busca normaliza ambos os lados antes de comparar.

Visivel a todos os perfis (cravado nas decisoes da Fase 2 — cadastros
sao operacao diaria).
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from src.database.connection import get_session
from src.database.models.fornecedor import Fornecedor
from src.services.fornecedor_service import FornecedorService
from src.ui import components, theme
from src.utils.cnpj import formatar_cnpj, normalizar_cnpj


# Cores especificas dos badges de status — mesma paleta de
# ListaUsuariosView / ListaCategoriasView.
_BADGE_ATIVO_BG: str = "#DCFCE7"      # green-100
_BADGE_ATIVO_TEXTO: str = "#15803D"   # green-700


# Larguras de colunas fixas (NOME usa o espaco restante).
_COL_CNPJ_WIDTH: int = 200
_COL_TELEFONE_WIDTH: int = 160
_COL_CONTATO_WIDTH: int = 180
_COL_STATUS_WIDTH: int = 110
_COL_ACOES_WIDTH: int = 110


class ListaFornecedoresView:
    """View de listagem de Fornecedores (Passo 3 da Fase 2)."""

    def __init__(
        self,
        page: ft.Page,
        on_novo: Callable[[], None],
        on_editar: Callable[[int], None],
    ) -> None:
        """Cria a view.

        Args:
            page: Pagina Flet onde a view sera montada (usada para
                ``page.update`` e ``page.show_dialog``).
            on_novo: Callback do botao "+ Novo Fornecedor".
            on_editar: Callback do icone de edicao na linha,
                recebe ``fornecedor_id``.
        """
        self._page = page
        self._on_novo = on_novo
        self._on_editar = on_editar

        # Estado em memoria.
        self._fornecedores: list[Fornecedor] = []
        self._busca: str = ""
        self._mostrar_inativos: bool = False

        # Referencias aos controles atualizados em ``_filtrar_e_renderizar``.
        self._campo_busca: ft.TextField | None = None
        self._switch_inativos: ft.Switch | None = None
        self._corpo_tabela: ft.Column | None = None
        self._texto_total: ft.Text | None = None

    # ------------------------------------------------------------------
    # Construcao da arvore
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Constroi a arvore de Controls e retorna a raiz."""
        self._campo_busca = ft.TextField(
            hint_text="Buscar por nome ou CNPJ...",
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

        self._switch_inativos = ft.Switch(
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
            "Total: 0 fornecedores",
            size=theme.FONTE_TAMANHO_HELPER + 1,  # 13px
            color=theme.COR_CINZA_400,
            weight=ft.FontWeight.W_400,
        )

        # Header via topbar padrao do shell.
        page_header = components.topbar(
            "Fornecedores",
            acao_direita=components.botao_primario(
                "Novo Fornecedor",
                on_click=lambda e: self._on_novo(),
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
                                "Mostrar inativos",
                                size=theme.FONTE_TAMANHO_LABEL,
                                color=theme.COR_CINZA_600,
                                weight=ft.FontWeight.W_500,
                            ),
                            self._switch_inativos,
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Tabela: header + body (rows scrollaveis) + footer.
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
        self._carregar_fornecedores()
        self._filtrar_e_renderizar(atualizar_pagina=False)

        return raiz

    def recarregar(self) -> None:
        """Recarrega fornecedores do banco e re-renderiza."""
        self._carregar_fornecedores()
        self._filtrar_e_renderizar()

    # ------------------------------------------------------------------
    # Sub-builders
    # ------------------------------------------------------------------

    def _build_header_tabela(self) -> ft.Container:
        """Cabecalho da tabela com nomes de coluna em uppercase."""
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
                    col("CNPJ", width=_COL_CNPJ_WIDTH),
                    col("Telefone", width=_COL_TELEFONE_WIDTH),
                    col("Contato", width=_COL_CONTATO_WIDTH),
                    col("Status", width=_COL_STATUS_WIDTH),
                    col("Ações", width=_COL_ACOES_WIDTH,
                        alinhamento=ft.TextAlign.RIGHT),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
        )

    def _build_footer_tabela(self) -> ft.Container:
        """Rodape com contador total filtrado."""
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

    def _build_linha(self, fornecedor: Fornecedor, indice: int) -> ft.Container:
        """Constroi uma linha de dados da tabela.

        Args:
            fornecedor: O fornecedor renderizado.
            indice: Posicao na lista filtrada (usado para zebra striping).
        """
        # Avatar circular laranja com inicial do nome.
        inicial = fornecedor.nome[0].upper() if fornecedor.nome else "?"
        avatar = ft.CircleAvatar(
            content=ft.Text(
                inicial,
                color=theme.COR_TERCIARIA,
                size=14,
                weight=ft.FontWeight.W_700,
            ),
            bgcolor=theme.COR_PRIMARIA,
            radius=16,  # 32px de diametro
        )

        col_nome = ft.Container(
            expand=True,
            content=ft.Row(
                controls=[
                    avatar,
                    ft.Text(
                        fornecedor.nome,
                        size=15,
                        weight=ft.FontWeight.W_500,
                        color=theme.COR_SECUNDARIA,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        cnpj_formatado = formatar_cnpj(fornecedor.cnpj) or "—"
        col_cnpj = ft.Container(
            width=_COL_CNPJ_WIDTH,
            content=ft.Text(
                cnpj_formatado,
                size=14,
                color=theme.COR_CINZA_600 if fornecedor.cnpj else theme.COR_CINZA_400,
                weight=ft.FontWeight.W_400,
            ),
        )

        telefone_texto = fornecedor.telefone or "—"
        col_telefone = ft.Container(
            width=_COL_TELEFONE_WIDTH,
            content=ft.Text(
                telefone_texto,
                size=14,
                color=theme.COR_CINZA_600 if fornecedor.telefone else theme.COR_CINZA_400,
                weight=ft.FontWeight.W_400,
            ),
        )

        contato_texto = fornecedor.contato or "—"
        col_contato = ft.Container(
            width=_COL_CONTATO_WIDTH,
            content=ft.Text(
                contato_texto,
                size=14,
                color=theme.COR_CINZA_600 if fornecedor.contato else theme.COR_CINZA_400,
                weight=ft.FontWeight.W_400,
            ),
        )

        col_status = ft.Container(
            width=_COL_STATUS_WIDTH,
            content=self._build_badge_status(fornecedor.ativo),
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
                        on_click=lambda e, fid=fornecedor.id: self._on_editar(fid),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.BLOCK if fornecedor.ativo else ft.Icons.PLAY_CIRCLE,
                        icon_color=theme.COR_CINZA_600,
                        icon_size=18,
                        tooltip="Desativar" if fornecedor.ativo else "Ativar",
                        on_click=lambda e, f=fornecedor: self._toggle_status(f),
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
            controls=[
                col_nome,
                col_cnpj,
                col_telefone,
                col_contato,
                col_status,
                col_acoes,
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            height=64,
            bgcolor=bg,
            padding=ft.Padding.symmetric(horizontal=24, vertical=0),
            opacity=0.6 if not fornecedor.ativo else 1.0,
            content=row,
        )

    def _build_badge_status(self, ativo: bool) -> ft.Control:
        """Badge pill verde (ativo) ou cinza (inativo)."""
        if ativo:
            bg = _BADGE_ATIVO_BG
            texto = "Ativo"
            cor_texto = _BADGE_ATIVO_TEXTO
        else:
            bg = theme.COR_CINZA_100
            texto = "Inativo"
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

    def _carregar_fornecedores(self) -> None:
        """Busca a lista completa (incluindo inativos)."""
        with get_session() as session:
            service = FornecedorService(session)
            self._fornecedores = service.listar(incluir_inativos=True)

    def _filtrar_e_renderizar(self, atualizar_pagina: bool = True) -> None:
        """Reaplica filtros em memoria e re-renderiza o corpo da tabela."""
        assert self._corpo_tabela is not None
        assert self._texto_total is not None

        filtrados = self._fornecedores
        if not self._mostrar_inativos:
            filtrados = [f for f in filtrados if f.ativo]

        busca_raw = self._busca.strip()
        if busca_raw:
            busca_lower = busca_raw.lower()
            # Normaliza o input de busca para comparar com cnpj puro do banco.
            # Permite que usuario digitando "12.345" ache "12345678000190".
            busca_cnpj = normalizar_cnpj(busca_raw)

            def _match(f: Fornecedor) -> bool:
                if busca_lower in f.nome.lower():
                    return True
                if busca_cnpj and f.cnpj and busca_cnpj in f.cnpj:
                    return True
                return False

            filtrados = [f for f in filtrados if _match(f)]

        if not filtrados:
            self._corpo_tabela.controls = [self._build_estado_vazio()]
        else:
            self._corpo_tabela.controls = [
                self._build_linha(f, i) for i, f in enumerate(filtrados)
            ]

        sufixo = "" if len(filtrados) == 1 else "es"
        self._texto_total.value = f"Total: {len(filtrados)} fornecedor{sufixo}"

        if atualizar_pagina:
            self._page.update()

    def _build_estado_vazio(self) -> ft.Container:
        """Mensagem amigavel quando nao ha fornecedores filtrados."""
        # Mensagem muda: se nada cadastrado vs filtro sem resultado.
        if not self._fornecedores:
            mensagem = "Nenhum fornecedor cadastrado."
        else:
            mensagem = "Nenhum fornecedor encontrado."

        return ft.Container(
            height=120,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                controls=[
                    ft.Icon(
                        icon=ft.Icons.LOCAL_SHIPPING_OUTLINED,
                        color=theme.COR_CINZA_400,
                        size=32,
                    ),
                    ft.Text(
                        mensagem,
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
        assert self._switch_inativos is not None
        self._mostrar_inativos = bool(self._switch_inativos.value)
        self._filtrar_e_renderizar()

    # ------------------------------------------------------------------
    # Toggle de status (ativar/desativar) com dialog
    # ------------------------------------------------------------------

    def _toggle_status(self, fornecedor: Fornecedor) -> None:
        """Abre dialog confirmando ativar/desativar; aplica via service.

        Cor do botao: LARANJA em ambos os casos. Fornecedor nao eh
        destrutivo-irreversivel (cravado nas decisoes — vermelho reservado
        para Desativar Usuario, Excluir, Cancelar Venda).
        """
        if fornecedor.ativo:
            titulo = "Desativar fornecedor"
            acao_label = "Desativar"
        else:
            titulo = "Ativar fornecedor"
            acao_label = "Ativar"

        mensagem = (
            f"Tem certeza que deseja {acao_label.lower()} '{fornecedor.nome}'?"
        )

        # Captura dados antes do session fechar.
        fid = fornecedor.id
        nome = fornecedor.nome
        cnpj = fornecedor.cnpj
        telefone = fornecedor.telefone
        contato = fornecedor.contato
        observacoes = fornecedor.observacoes
        estava_ativo = fornecedor.ativo

        def _confirmar(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()
            try:
                with get_session() as session:
                    service = FornecedorService(session)
                    if estava_ativo:
                        service.desativar(fid)
                    else:
                        service.atualizar(
                            fid, nome, cnpj, telefone, contato,
                            observacoes, True,
                        )
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
                # Laranja para ambas as acoes (fornecedor nao eh
                # destrutivo irreversivel). Decisao cravada nas regras
                # de design.
                cor_botao_confirmar=theme.COR_PRIMARIA,
                on_confirmar=_confirmar,
                on_cancelar=_cancelar,
            )
        )

    def _mostrar_erro(self, mensagem: str) -> None:
        """Exibe SnackBar vermelho com a mensagem de erro."""
        self._page.show_dialog(components.snackbar_erro(mensagem))
