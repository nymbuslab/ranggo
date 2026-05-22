"""Componentes UI padronizados do Ranggo.

Centraliza estruturas visuais recorrentes (cabeçalhos, dialogs,
snackbars, **botões** e **layouts de formulário**) para garantir
consistência visual entre todas as views.

**Regra obrigatória**: views NUNCA devem montar :class:`ft.AlertDialog`,
:class:`ft.SnackBar`, :class:`ft.ElevatedButton`, :class:`ft.TextButton`,
``Container`` de formulário ou cabeçalhos manualmente. Sempre passam por
estas funções. Veja a seção "Componentes UI padronizados" no ``CLAUDE.md``.

Razão: o Material 3 do Flet (ativado via ``color_scheme_seed`` no
:mod:`src.ui.theme`) tonaliza componentes não explicitamente configurados
— bgcolor, bordas, fill, padding interno de botões, etc. — gerando
inconsistência visual entre views. A camada de componentes força
explicitude e centraliza padrões.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from src.ui import theme


# ============================================================================
# Cabeçalhos de página
# ============================================================================

def topbar(
    titulo: str,
    acao_direita: ft.Control | None = None,
) -> ft.Control:
    """Topbar padronizada do shell — chrome consistente entre todas as telas.

    **REGRA OBRIGATÓRIA**: toda view do shell (Dashboard, Lista de
    Usuários, Form de Usuário, e todas as futuras) deve renderizar
    ``components.topbar(...)`` como **primeiro elemento** do seu
    Column raiz. Garante transição visual fluida entre telas — só
    título e conteúdo mudam, o chrome permanece.

    Padrão visual:
        * Fundo branco :data:`theme.COR_TERCIARIA`.
        * Border-bottom 1px :data:`theme.COR_CINZA_200`.
        * Altura fixa **80px**.
        * Padding horizontal 32, vertical 16.
        * Título Inter SemiBold 28px :data:`theme.COR_SECUNDARIA` à esquerda.
        * Ação opcional alinhada à direita (tipicamente um
          :func:`botao_primario` com ``icone=ft.Icons.ADD``).

    Args:
        titulo: Título da tela.
        acao_direita: Control opcional alinhado à direita (botão CTA,
            badge, etc.). Use :func:`botao_primario` para padronizar.

    Returns:
        :class:`ft.Container` com a topbar montada.
    """
    children: list[ft.Control] = [
        ft.Text(
            titulo,
            size=28,
            weight=ft.FontWeight.W_600,
            color=theme.COR_SECUNDARIA,
        ),
    ]
    if acao_direita is not None:
        children.extend([
            ft.Container(expand=True),  # spacer
            acao_direita,
        ])

    return ft.Container(
        bgcolor=theme.COR_TERCIARIA,
        border=ft.Border.only(
            bottom=ft.BorderSide(width=1, color=theme.COR_CINZA_200),
        ),
        height=80,
        padding=ft.Padding.symmetric(horizontal=32, vertical=16),
        content=ft.Row(
            controls=children,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def cabecalho_pagina(
    titulo: str,
    acao_direita: ft.Control | None = None,
) -> ft.Control:
    """[DEPRECATED] Use :func:`topbar` em vez disso.

    Esta função foi substituída por :func:`topbar`, que segue o padrão
    do shell (fundo branco, border-bottom, altura fixa 80px). Mantida
    temporariamente como alias para não quebrar código legado durante
    a migração. Será removida em commit subsequente.
    """
    return topbar(titulo, acao_direita)


# ============================================================================
# Botões padronizados
# ============================================================================

# Padding e altura comuns dos botões. Mesmo bloco em todos para que
# variantes (primário/secundário/perigo/sucesso) sejam visualmente
# idênticas em forma — só a cor de fundo muda.
_BOTAO_PADDING = ft.Padding.symmetric(horizontal=24, vertical=12)
_BOTAO_TEXT_STYLE = ft.TextStyle(size=14, weight=ft.FontWeight.W_600)


def _botao_base(
    texto: str,
    on_click: Callable[[ft.ControlEvent], None],
    *,
    bgcolor: str,
    color: str,
    icone: ft.IconData | None = None,
    disabled: bool = False,
    tooltip: str | None = None,
) -> ft.ElevatedButton:
    """Factory interna: ``ElevatedButton`` com forma padronizada do Ranggo.

    Não usar diretamente nas views — passar por :func:`botao_primario`,
    :func:`botao_secundario`, :func:`botao_perigo` ou :func:`botao_sucesso`.
    """
    return ft.ElevatedButton(
        content=texto,
        icon=icone,
        on_click=on_click,
        disabled=disabled,
        tooltip=tooltip,
        bgcolor=bgcolor,
        color=color,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=theme.BORDER_RADIUS_BOTAO),
            padding=_BOTAO_PADDING,
            text_style=_BOTAO_TEXT_STYLE,
        ),
    )


def botao_primario(
    texto: str,
    on_click: Callable[[ft.ControlEvent], None],
    icone: ft.IconData | None = None,
    disabled: bool = False,
    tooltip: str | None = None,
) -> ft.ElevatedButton:
    """Botão primário laranja — ação principal de uma tela ou modal.

    Padrão visual:
        * Fundo :data:`theme.COR_PRIMARIA` (#FF6600).
        * Texto branco :data:`theme.COR_TERCIARIA`, Inter SemiBold 14px.
        * Padding 12 vertical / 24 horizontal, border-radius do tema.

    **Usar para**: "Salvar", "Criar Usuário", "Confirmar", "+ Novo X",
    "Entrar", "Adicionar".

    Args:
        texto: Label do botão.
        on_click: Handler do clique.
        icone: Constante de :class:`ft.Icons` opcional (ex.: ``ft.Icons.ADD``).
        disabled: Se ``True``, botão fica inativo.
        tooltip: Tooltip opcional.
    """
    return _botao_base(
        texto,
        on_click,
        bgcolor=theme.COR_PRIMARIA,
        color=theme.COR_TERCIARIA,
        icone=icone,
        disabled=disabled,
        tooltip=tooltip,
    )


def botao_secundario(
    texto: str,
    on_click: Callable[[ft.ControlEvent], None],
    icone: ft.IconData | None = None,
    disabled: bool = False,
    tooltip: str | None = None,
) -> ft.ElevatedButton:
    """Botão secundário cinza — par visual do primário em formulários e modais.

    Padrão visual:
        * Fundo :data:`theme.COR_CINZA_100` (#F5F5F5).
        * Texto preto :data:`theme.COR_SECUNDARIA`, Inter SemiBold 14px.
        * Mesma forma/padding do :func:`botao_primario` — pares
          [Cancelar, Salvar] ficam visualmente alinhados.

    **Usar para**: "Cancelar", "Voltar", "Fechar", "Limpar Filtros".

    NUNCA usar :class:`ft.TextButton` para ação secundária em formulários.
    Os pares Cancelar/Salvar devem ser sempre
    ``[botao_secundario, botao_primario]``.
    """
    return _botao_base(
        texto,
        on_click,
        bgcolor=theme.COR_CINZA_100,
        color=theme.COR_SECUNDARIA,
        icone=icone,
        disabled=disabled,
        tooltip=tooltip,
    )


def botao_perigo(
    texto: str,
    on_click: Callable[[ft.ControlEvent], None],
    icone: ft.IconData | None = None,
    disabled: bool = False,
    tooltip: str | None = None,
) -> ft.ElevatedButton:
    """Botão destrutivo vermelho — ações irreversíveis.

    Padrão visual: mesma forma do :func:`botao_primario`, fundo
    :data:`theme.COR_ERRO`, texto branco.

    **Usar para**: "Desativar", "Excluir", "Cancelar Venda",
    "Fechar Caixa" (no logout), "Confirmar Exclusão".

    Restrito a confirmações destrutivas. Em casos cinza, use
    :func:`botao_primario`.
    """
    return _botao_base(
        texto,
        on_click,
        bgcolor=theme.COR_ERRO,
        color=theme.COR_TERCIARIA,
        icone=icone,
        disabled=disabled,
        tooltip=tooltip,
    )


def botao_sucesso(
    texto: str,
    on_click: Callable[[ft.ControlEvent], None],
    icone: ft.IconData | None = None,
    disabled: bool = False,
    tooltip: str | None = None,
) -> ft.ElevatedButton:
    """Botão de ação positiva verde — raro, usado em reativação etc.

    **Usar para**: "Ativar usuário", "Confirmar Pagamento",
    "Finalizar Venda" (em casos específicos onde a positividade é destacada).
    """
    return _botao_base(
        texto,
        on_click,
        bgcolor=theme.COR_SUCESSO,
        color=theme.COR_TERCIARIA,
        icone=icone,
        disabled=disabled,
        tooltip=tooltip,
    )


def _botao_por_cor(cor: str) -> Callable[..., ft.ElevatedButton]:
    """Mapeia uma cor do tema para o factory de botão correspondente.

    Usado por :func:`dialog_confirmacao` para escolher entre primário,
    perigo ou sucesso baseado em ``cor_botao_confirmar``.
    """
    if cor == theme.COR_ERRO:
        return botao_perigo
    if cor == theme.COR_SUCESSO:
        return botao_sucesso
    return botao_primario


# ============================================================================
# Layout de formulário
# ============================================================================

def card_form(
    campos: list[ft.Control],
    botoes: list[ft.Control],
    largura: int = 800,
) -> ft.Control:
    """Container do card de formulário centralizado (sem título).

    Título é responsabilidade da :func:`topbar` do shell — a view deve
    montar ``Column([topbar(titulo), card_form(campos, botoes)])``.

    Estrutura visual:
        * Container externo cinza, ``expand=True``, alinhado ao topo-centro.
        * Card branco centralizado horizontalmente, largura fixa (default
          800px):
            - Column interna com ``horizontal_alignment=STRETCH`` —
              campos preenchem 100% da largura do card. Sem isso, o
              default do Flet é ``CENTER`` e campos ficam encolhidos.
            - Spacing 20 entre campos.
            - Divisor sutil acima dos botões.
            - Row dos botões alinhada à direita, ``spacing=12``.

    Args:
        campos: Lista de controls (TextField, Dropdown, Switch, etc.).
            Use :func:`campo_linha_dupla` para pares lado a lado
            (Senha + Confirmar). Campos individuais esticam horizontalmente
            via STRETCH da Column interna do card.
        botoes: Lista de botões para o rodapé, tipicamente
            ``[botao_secundario, botao_primario]``.
        largura: Largura do conteúdo (default 800px).
    """
    card_branco = ft.Container(
        width=largura,
        bgcolor=theme.COR_TERCIARIA,
        border_radius=12,
        border=ft.Border.all(1, theme.COR_CINZA_200),
        padding=ft.Padding.all(32),
        content=ft.Column(
            controls=[
                *campos,
                ft.Container(height=8),
                ft.Divider(height=1, thickness=1, color=theme.COR_CINZA_200),
                ft.Container(height=8),
                ft.Row(
                    controls=botoes,
                    alignment=ft.MainAxisAlignment.END,
                    spacing=12,
                ),
            ],
            spacing=20,
            # STRETCH é o que faz os campos preencherem 100% do card.
            # Default do Flet é CENTER (campos ficam com width natural,
            # encolhidos no meio). Sem STRETCH, ``expand=True`` no campo
            # não tem efeito em Column (expand=main axis, não cross).
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            tight=True,
        ),
    )

    return ft.Container(
        bgcolor=theme.COR_CINZA_100,
        expand=True,
        alignment=ft.Alignment.TOP_CENTER,
        padding=ft.Padding.only(top=32, bottom=32, left=24, right=24),
        content=card_branco,
    )


def campo_linha_dupla(
    esquerda: ft.Control,
    direita: ft.Control,
    spacing: int = 16,
) -> ft.Row:
    """Wrapper para dois campos lado a lado, cada um ocupando 50%.

    **Usar para**: Senha + Confirmar Senha, Cidade + Estado, etc.

    Garante que os dois campos tenham largura igual (``expand=1``) com
    spacing consistente. Muta os controles em-place adicionando ``expand=1``.
    """
    esquerda.expand = 1
    direita.expand = 1
    return ft.Row(
        controls=[esquerda, direita],
        spacing=spacing,
    )


# ============================================================================
# Dialogs de confirmação
# ============================================================================

def dialog_confirmacao(
    titulo: str,
    mensagem: str,
    texto_botao_confirmar: str,
    cor_botao_confirmar: str,
    on_confirmar: Callable[[ft.ControlEvent], None],
    on_cancelar: Callable[[ft.ControlEvent], None],
    texto_botao_cancelar: str = "Cancelar",
) -> ft.AlertDialog:
    """Dialog padronizado de confirmação (com 2 botões).

    Padrão visual:
        * Fundo **branco puro** (:data:`theme.COR_TERCIARIA`) — bgcolor
          explícito mata a tonalização Material 3 (rosé/pêssego).
        * Border-radius 12.
        * Título Inter SemiBold 20px, cor :data:`theme.COR_SECUNDARIA`.
        * Mensagem Inter Regular 14px, cor :data:`theme.COR_CINZA_600`.
        * Botões via componentes padronizados:
            - Cancelar: :func:`botao_secundario` (cinza).
            - Confirmar: ``_botao_por_cor(cor_botao_confirmar)`` →
              :func:`botao_primario` / :func:`botao_perigo` /
              :func:`botao_sucesso`.

    **Usar para**: confirmações destrutivas (desativar, excluir, fechar
    caixa) ou destrutivas-suaves (cancelar venda, sair sem salvar).

    Args:
        titulo: Título do dialog (ex.: ``"Desativar usuário"``).
        mensagem: Texto explicativo (ex.: ``"Tem certeza..."``).
        texto_botao_confirmar: Label do botão primário.
        cor_botao_confirmar: :data:`theme.COR_ERRO`,
            :data:`theme.COR_SUCESSO` ou :data:`theme.COR_PRIMARIA`.
        on_confirmar: Callback ao clicar confirmar. **Deve** fechar o
            dialog via ``page.pop_dialog()`` e executar a ação.
        on_cancelar: Callback ao clicar cancelar. **Deve** fechar o
            dialog via ``page.pop_dialog()``.
        texto_botao_cancelar: Default ``"Cancelar"``.

    Returns:
        :class:`ft.AlertDialog` pronto para ``page.show_dialog()``.
    """
    factory_confirmar = _botao_por_cor(cor_botao_confirmar)

    return ft.AlertDialog(
        modal=True,
        bgcolor=theme.COR_TERCIARIA,
        title=ft.Text(
            titulo,
            size=20,
            weight=ft.FontWeight.W_600,
            color=theme.COR_SECUNDARIA,
        ),
        content=ft.Text(
            mensagem,
            size=14,
            color=theme.COR_CINZA_600,
        ),
        actions=[
            botao_secundario(texto_botao_cancelar, on_cancelar),
            factory_confirmar(texto_botao_confirmar, on_confirmar),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=12),
    )


# ============================================================================
# SnackBars de feedback
# ============================================================================

def snackbar_erro(mensagem: str) -> ft.SnackBar:
    """SnackBar vermelho para erros de validação ou regras de negócio.

    Usar para :class:`~src.utils.exceptions.PermissaoNegadaError`,
    :class:`~src.utils.exceptions.NomeDuplicadoError`, ``ValueError``, etc.

    No Flet 0.85.1, :class:`ft.SnackBar` herda de ``DialogControl`` — o
    caller dispara via ``page.show_dialog(snackbar_erro(...))``, **não**
    via ``page.snack_bar = ...`` (essa API não existe nesta versão).
    """
    return ft.SnackBar(
        content=ft.Text(mensagem, color=theme.COR_TERCIARIA),
        bgcolor=theme.COR_ERRO,
    )


def snackbar_sucesso(mensagem: str) -> ft.SnackBar:
    """SnackBar verde para feedback de sucesso de ações.

    Usar para "Usuário criado", "Senha alterada", "Venda finalizada", etc.

    Veja a nota em :func:`snackbar_erro` sobre como disparar via
    ``page.show_dialog``.
    """
    return ft.SnackBar(
        content=ft.Text(mensagem, color=theme.COR_TERCIARIA),
        bgcolor=theme.COR_SUCESSO,
    )
