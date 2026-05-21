"""Tela de listagem de usuários — exclusiva do perfil Admin.

Referência visual: ``prototipos/08-listagem-usuarios.png``.

Componentes principais:
    * Page header com título "Usuários" e CTA "+ Novo Usuário".
    * Filter bar com busca local (nome/login) e toggle "Mostrar inativos".
    * Tabela custom (não :class:`ft.DataTable`) com avatar circular,
      badge de status, ações por linha e zebra striping.
    * Footer com contador total filtrado.

Decisão de UX: os 3 IconButtons da coluna **Ações** ficam **sempre
visíveis** — descobribilidade > minimalismo estético em PDV de
restaurante. O protótipo (Stitch) suprime os ícones para visual limpo;
nossa implementação não segue isso.

A view delega criar/editar/trocar-senha via callbacks (Passo 9.3 conecta
ao roteamento real). **Ativar/desativar** é tratado internamente: a view
chama :class:`UsuarioService` com confirmação via dialog e mostra erros
de :class:`PermissaoNegadaError` (auto-desativação, último Admin) em
SnackBar vermelho.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from src.database.connection import get_session
from src.database.models.usuario import Usuario
from src.services.usuario_service import UsuarioService
from src.ui import theme
from src.utils.exceptions import PermissaoNegadaError


# ---------------------------------------------------------------------------
# Cores específicas dos badges de status — paleta Tailwind green-100/700,
# coerentes com o verde funcional COR_SUCESSO (#16A34A = green-600) já
# usado no theme. Não estão em ``theme.py`` ainda porque são as únicas
# variantes "claras/escuras" usadas até agora; se aparecer um segundo
# caso, promover para constantes do tema.
# ---------------------------------------------------------------------------
_BADGE_ATIVO_BG: str = "#DCFCE7"      # green-100
_BADGE_ATIVO_TEXTO: str = "#15803D"   # green-700


# Largura das colunas fixas da tabela (USUARIO usa o espaço restante).
_COL_LOGIN_WIDTH: int = 160
_COL_PERFIL_WIDTH: int = 140
_COL_STATUS_WIDTH: int = 120
_COL_ACOES_WIDTH: int = 160


class ListaUsuariosView:
    """View de listagem de usuários para o perfil Admin.

    Uso típico::

        view = ListaUsuariosView(
            page,
            on_novo_usuario=callback_novo,
            on_editar_usuario=callback_editar,
            on_trocar_senha=callback_senha,
        )
        page.add(view.build())

    Após criar/editar usuário em outra view, o caller deve invocar
    :meth:`recarregar` para refletir as mudanças.
    """

    def __init__(
        self,
        page: ft.Page,
        on_novo_usuario: Callable[[], None],
        on_editar_usuario: Callable[[int], None],
        on_trocar_senha: Callable[[int], None],
    ) -> None:
        """Cria a view.

        Args:
            page: Página Flet onde a view será montada (usada para
                ``page.update`` e ``page.show_dialog``).
            on_novo_usuario: Callback do botão "+ Novo Usuário".
            on_editar_usuario: Callback do ícone de edição na linha,
                recebe ``usuario_id``.
            on_trocar_senha: Callback do ícone de chave na linha,
                recebe ``usuario_id``.
        """
        self._page = page
        self._on_novo_usuario = on_novo_usuario
        self._on_editar_usuario = on_editar_usuario
        self._on_trocar_senha = on_trocar_senha

        # Estado em memória.
        self._usuarios: list[Usuario] = []
        self._busca: str = ""
        self._mostrar_inativos: bool = False

        # Referências aos controles atualizados em ``_filtrar_e_renderizar``.
        self._campo_busca: ft.TextField | None = None
        self._switch_inativos: ft.Switch | None = None
        self._corpo_tabela: ft.Column | None = None
        self._texto_total: ft.Text | None = None

    # ------------------------------------------------------------------
    # Construção da árvore
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Constrói a árvore de Controls e retorna a raiz.

        Carrega os dados via :class:`UsuarioService` no build inicial e
        já aplica os filtros default (oculta inativos, sem busca).

        Returns:
            :class:`ft.Container` raiz da view, expansível.
        """
        self._campo_busca = ft.TextField(
            hint_text="Buscar por nome ou login...",
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
            "Total: 0 usuários",
            size=theme.FONTE_TAMANHO_HELPER + 1,  # 13px
            color=theme.COR_CINZA_400,
            weight=ft.FontWeight.W_400,
        )

        # Header da página (título + CTA).
        page_header = ft.Container(
            height=80,
            bgcolor=theme.COR_TERCIARIA,
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
            border=ft.Border.only(
                bottom=ft.BorderSide(width=1, color=theme.COR_CINZA_200),
            ),
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Usuários",
                        size=28,
                        weight=ft.FontWeight.W_600,
                        color=theme.COR_SECUNDARIA,
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        content="Novo Usuário",
                        icon=ft.Icons.ADD,
                        bgcolor=theme.COR_PRIMARIA,
                        color=theme.COR_TERCIARIA,
                        height=theme.ALTURA_BOTAO,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(
                                radius=theme.BORDER_RADIUS_BOTAO,
                            ),
                        ),
                        on_click=lambda e: self._on_novo_usuario(),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
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

        # Área da tabela com padding cinza ao redor (espelha shell pattern).
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
        self._carregar_usuarios()
        self._filtrar_e_renderizar(atualizar_pagina=False)

        return raiz

    def recarregar(self) -> None:
        """Recarrega usuários do banco e re-renderiza.

        Chamado pelo caller após criar/editar usuário em outra view, e
        internamente após ações de ativar/desativar/trocar-senha.
        """
        self._carregar_usuarios()
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
                # Flet 0.85.1 não tem letter_spacing em Text — aplicaria
                # via TextStyle no theme se virasse padrão recorrente.
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
                    col("Usuário", expand=True),
                    col("Login", width=_COL_LOGIN_WIDTH),
                    col("Perfil", width=_COL_PERFIL_WIDTH),
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

    def _build_linha(self, usuario: Usuario, indice: int) -> ft.Container:
        """Constrói uma linha de dados da tabela.

        Args:
            usuario: O usuário renderizado.
            indice: Posição na lista filtrada (usado para zebra striping).

        Returns:
            :class:`ft.Container` da linha (com opacity reduzida se inativo).
        """
        # Avatar circular laranja com inicial do nome.
        inicial = usuario.nome[0].upper() if usuario.nome else "?"
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

        col_usuario = ft.Container(
            expand=True,
            content=ft.Row(
                controls=[
                    avatar,
                    ft.Text(
                        usuario.nome,
                        size=15,
                        weight=ft.FontWeight.W_500,
                        color=theme.COR_SECUNDARIA,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        col_login = ft.Container(
            width=_COL_LOGIN_WIDTH,
            content=ft.Text(
                usuario.login,
                size=14,
                color=theme.COR_CINZA_600,
                weight=ft.FontWeight.W_400,
            ),
        )

        col_perfil = ft.Container(
            width=_COL_PERFIL_WIDTH,
            content=ft.Text(
                usuario.perfil.nome,
                size=14,
                color=theme.COR_SECUNDARIA,
                weight=ft.FontWeight.W_400,
            ),
        )

        col_status = ft.Container(
            width=_COL_STATUS_WIDTH,
            content=self._build_badge_status(usuario.ativo),
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
                        on_click=lambda e, uid=usuario.id: self._on_editar_usuario(uid),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.KEY,
                        icon_color=theme.COR_CINZA_600,
                        icon_size=18,
                        tooltip="Trocar senha",
                        on_click=lambda e, uid=usuario.id: self._on_trocar_senha(uid),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.BLOCK if usuario.ativo else ft.Icons.PLAY_CIRCLE,
                        icon_color=theme.COR_CINZA_600,
                        icon_size=18,
                        tooltip="Desativar" if usuario.ativo else "Ativar",
                        on_click=lambda e, u=usuario: self._toggle_status(u),
                    ),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.END,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Zebra striping: linhas pares brancas, ímpares cinza claro.
        bg = theme.COR_CINZA_100 if indice % 2 == 1 else theme.COR_TERCIARIA

        row = ft.Row(
            controls=[col_usuario, col_login, col_perfil, col_status, col_acoes],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            height=64,
            bgcolor=bg,
            padding=ft.Padding.symmetric(horizontal=24, vertical=0),
            # Inativo: linha inteira dimmed para reforçar visualmente o estado.
            opacity=0.6 if not usuario.ativo else 1.0,
            content=row,
        )

    def _build_badge_status(self, ativo: bool) -> ft.Control:
        """Badge pill verde (ativo) ou cinza (inativo).

        Duas camadas de :class:`ft.Container`:
            * Interno (``badge``) — altura fixa 24px + ``alignment.CENTER``
              para o texto. Sem ``height`` o Container estica para a
              altura da célula (64px) e o pill vira retângulo gigante.
            * Externo (wrapper) — ``alignment.CENTER_LEFT`` para
              centralizar o pill verticalmente na linha sem esticá-lo.
        """
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

    def _carregar_usuarios(self) -> None:
        """Busca a lista completa via service (com perfil eager-loaded)."""
        with get_session() as session:
            service = UsuarioService(session)
            self._usuarios = service.listar(incluir_inativos=True)

    def _filtrar_e_renderizar(self, atualizar_pagina: bool = True) -> None:
        """Reaplica filtros em memória e re-renderiza o corpo da tabela.

        Args:
            atualizar_pagina: Se ``True`` (default), chama ``page.update``
                ao final. Passar ``False`` no build inicial — a árvore
                ainda não foi attachada à página.
        """
        assert self._corpo_tabela is not None
        assert self._texto_total is not None

        filtrados = self._usuarios
        if not self._mostrar_inativos:
            filtrados = [u for u in filtrados if u.ativo]

        busca = self._busca.strip().lower()
        if busca:
            filtrados = [
                u for u in filtrados
                if busca in u.nome.lower() or busca in u.login.lower()
            ]

        self._corpo_tabela.controls = [
            self._build_linha(u, i) for i, u in enumerate(filtrados)
        ]
        sufixo = "" if len(filtrados) == 1 else "s"
        self._texto_total.value = f"Total: {len(filtrados)} usuário{sufixo}"

        if atualizar_pagina:
            self._page.update()

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
    # Toggle de status (ativar/desativar) com dialog + tratamento de erro
    # ------------------------------------------------------------------

    def _toggle_status(self, usuario: Usuario) -> None:
        """Abre dialog confirmando ativar/desativar; aplica via service."""
        if usuario.ativo:
            titulo = "Desativar usuário"
            acao_label = "Desativar"
            cor_acao = theme.COR_ERRO
        else:
            titulo = "Ativar usuário"
            acao_label = "Ativar"
            cor_acao = theme.COR_SUCESSO

        mensagem = f"Tem certeza que deseja {acao_label.lower()} '{usuario.nome}'?"

        # Capturar dados necessários do usuário ANTES — o objeto pode
        # ficar inutilizável (DetachedInstance) após o ``with get_session``
        # do confirmador fechar.
        uid = usuario.id
        nome = usuario.nome
        perfil_id = usuario.perfil_id
        estava_ativo = usuario.ativo

        def _confirmar(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()
            try:
                with get_session() as session:
                    service = UsuarioService(session)
                    if estava_ativo:
                        service.desativar(uid)
                    else:
                        service.atualizar(uid, nome, perfil_id, True)
                self.recarregar()
            except PermissaoNegadaError as ex:
                self._mostrar_erro(str(ex))
            except Exception as ex:
                self._mostrar_erro(f"Erro inesperado: {ex}")

        def _cancelar(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(titulo),
            content=ft.Text(mensagem),
            actions=[
                ft.TextButton("Cancelar", on_click=_cancelar),
                ft.ElevatedButton(
                    content=acao_label,
                    on_click=_confirmar,
                    bgcolor=cor_acao,
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
        self._page.show_dialog(dialog)

    def _mostrar_erro(self, mensagem: str) -> None:
        """Exibe SnackBar vermelho com a mensagem de erro.

        Flet 0.85.1 expõe :class:`ft.SnackBar` como ``DialogControl`` —
        o padrão correto é ``page.show_dialog(snack_bar)``, mesmo método
        usado para :class:`ft.AlertDialog`. ``page.snack_bar = ...`` e
        ``page.show_snack_bar(...)`` **não existem** nesta versão.
        """
        snack = ft.SnackBar(
            content=ft.Text(mensagem, color=theme.COR_TERCIARIA),
            bgcolor=theme.COR_ERRO,
        )
        self._page.show_dialog(snack)
