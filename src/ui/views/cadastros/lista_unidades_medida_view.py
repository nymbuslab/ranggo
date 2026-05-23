"""Lista somente-leitura de Unidades de Medida — Passo 2 da Fase 2.

UnidadeMedida é cadastro **fixo** do sistema, decidido na Fase 0 (ver
docstring do model). Esta view existe para que o operador **veja** as
unidades disponíveis, mas não há CRUD por design — sem botão "+ Nova",
sem ações de editar/desativar, sem busca, sem toggle de inativas. A
decisão arquitetural está documentada na seção 2.1 do `ROADMAP.md`.

Estrutura:
    * Topbar padrão (``components.topbar("Unidades de Medida")``) — sem
      ação à direita.
    * Banner informativo cinza no topo explicando que o cadastro é fixo.
    * Tabela com 2 colunas: NOME (descricao) e SÍMBOLO (sigla).
    * Footer com contador total.

Acesso a dados: query direta via ``get_session`` — sem ``Service`` nem
``Repository`` próprios, porque não há regra de negócio para encapsular
(apenas leitura ordenada).
"""

from __future__ import annotations

import flet as ft
from sqlalchemy import select

from src.database.connection import get_session
from src.database.models.unidade_medida import UnidadeMedida
from src.ui import components, theme


# Larguras de colunas (NOME usa o espaço restante).
_COL_SIMBOLO_WIDTH: int = 160


class ListaUnidadesMedidaView:
    """View somente-leitura das Unidades de Medida (Passo 2 da Fase 2)."""

    def __init__(self, page: ft.Page) -> None:
        """Cria a view.

        Args:
            page: Página Flet onde a view será montada. **Sem callbacks**:
                a view não tem ações que disparem navegação externa
                (CRUD desabilitado por decisão arquitetural).
        """
        self._page = page
        self._unidades: list[UnidadeMedida] = []

    # ------------------------------------------------------------------
    # Construção
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Constrói a árvore de Controls e retorna a raiz."""
        self._carregar_unidades()

        # Header sem acao_direita (não há "+ Nova").
        page_header = components.topbar("Unidades de Medida")

        banner = self._build_banner_informativo()

        # Tabela: header + body + footer (mesma estrutura visual da Lista
        # de Categorias, sem busca/inativos).
        if not self._unidades:
            corpo = self._build_estado_vazio()
        else:
            corpo = ft.Column(
                controls=[
                    self._build_linha(u, i)
                    for i, u in enumerate(self._unidades)
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

        tabela = ft.Container(
            bgcolor=theme.COR_TERCIARIA,
            border=ft.Border.all(width=1, color=theme.COR_CINZA_200),
            border_radius=theme.BORDER_RADIUS_CARD,
            expand=True,
            content=ft.Column(
                controls=[
                    self._build_header_tabela(),
                    ft.Container(expand=True, content=corpo),
                    self._build_footer_tabela(),
                ],
                spacing=0,
                expand=True,
            ),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        area_tabela = ft.Container(
            bgcolor=theme.COR_CINZA_100,
            padding=ft.Padding.only(left=24, right=24, top=0, bottom=24),
            expand=True,
            content=tabela,
        )

        return ft.Container(
            bgcolor=theme.COR_CINZA_100,
            expand=True,
            content=ft.Column(
                controls=[page_header, banner, area_tabela],
                spacing=0,
                expand=True,
            ),
        )

    # ------------------------------------------------------------------
    # Sub-builders
    # ------------------------------------------------------------------

    def _build_banner_informativo(self) -> ft.Container:
        """Banner cinza permanente no topo explicando que o cadastro é fixo."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.INFO_OUTLINE,
                        size=16,
                        color=theme.COR_CINZA_400,
                    ),
                    ft.Text(
                        "As unidades de medida são padronizadas pelo sistema. "
                        "Se houver necessidade de unidade customizada, será "
                        "disponibilizada em Configurações > Sistema em versão futura.",
                        size=12,
                        color=theme.COR_CINZA_400,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=12),
            bgcolor=theme.COR_CINZA_100,
            border_radius=8,
            margin=ft.Margin.only(left=24, right=24, top=16, bottom=16),
            border=ft.Border.all(width=1, color=theme.COR_CINZA_200),
        )

    def _build_header_tabela(self) -> ft.Container:
        """Cabeçalho da tabela com nomes de coluna em uppercase."""
        def col(texto: str, width: int | None = None, expand: bool = False
                ) -> ft.Control:
            t = ft.Text(
                texto.upper(),
                size=13,
                weight=ft.FontWeight.W_600,
                color=theme.COR_CINZA_600,
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
                    col("Símbolo", width=_COL_SIMBOLO_WIDTH),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
        )

    def _build_footer_tabela(self) -> ft.Container:
        """Rodapé com contador total."""
        total = len(self._unidades)
        sufixo = "" if total == 1 else "s"
        return ft.Container(
            height=40,
            padding=ft.Padding.symmetric(horizontal=24, vertical=8),
            border=ft.Border.only(
                top=ft.BorderSide(width=1, color=theme.COR_CINZA_200),
            ),
            content=ft.Row(
                controls=[
                    ft.Container(expand=True),
                    ft.Text(
                        f"Total: {total} unidade{sufixo}",
                        size=theme.FONTE_TAMANHO_HELPER + 1,  # 13px
                        color=theme.COR_CINZA_400,
                        weight=ft.FontWeight.W_400,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _build_linha(self, unidade: UnidadeMedida, indice: int) -> ft.Container:
        """Constrói uma linha de dados — avatar + nome + símbolo."""
        inicial = (
            unidade.descricao[0].upper() if unidade.descricao else "?"
        )
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
                        unidade.descricao,
                        size=15,
                        weight=ft.FontWeight.W_500,
                        color=theme.COR_SECUNDARIA,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        col_simbolo = ft.Container(
            width=_COL_SIMBOLO_WIDTH,
            content=ft.Text(
                unidade.sigla,
                size=14,
                color=theme.COR_CINZA_600,
                weight=ft.FontWeight.W_500,
            ),
        )

        # Zebra striping (mesma convenção da Lista de Categorias).
        bg = theme.COR_CINZA_100 if indice % 2 == 1 else theme.COR_TERCIARIA

        return ft.Container(
            height=64,
            bgcolor=bg,
            padding=ft.Padding.symmetric(horizontal=24, vertical=0),
            content=ft.Row(
                controls=[col_nome, col_simbolo],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _build_estado_vazio(self) -> ft.Container:
        """Mensagem defensiva — não deveria acontecer (seed roda no boot)."""
        return ft.Container(
            height=120,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                controls=[
                    ft.Icon(
                        icon=ft.Icons.STRAIGHTEN,
                        color=theme.COR_CINZA_400,
                        size=32,
                    ),
                    ft.Text(
                        "Nenhuma unidade de medida cadastrada.",
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
    # Carga
    # ------------------------------------------------------------------

    def _carregar_unidades(self) -> None:
        """Carrega todas as UMs ordenadas alfabeticamente por descrição.

        Query direta via :func:`get_session` (sem service nem repository
        próprios — não há regra de negócio para encapsular).
        """
        with get_session() as session:
            stmt = select(UnidadeMedida).order_by(UnidadeMedida.descricao)
            self._unidades = list(session.execute(stmt).scalars().all())
