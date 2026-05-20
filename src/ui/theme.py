"""Identidade visual do Oui Chef — fonte única de verdade no código.

Este módulo espelha **exatamente** ``PROJETO.md §3`` (Identidade Visual):
cores, tipografia, espaçamento e forma. Qualquer divergência entre
``PROJETO.md`` e este arquivo deve ser resolvida atualizando este
arquivo — ``PROJETO.md`` é a fonte de verdade do projeto.

Regras de uso:
    * Nenhuma view pode hardcodar cor, fonte ou dimensão. Sempre
      importar a constante deste módulo.
    * Adicionar uma nova constante aqui só depois de atualizar
      ``PROJETO.md §3`` primeiro.
    * Helpers de componente (``botao_primario()``, ``card_padrao()``,
      etc.) NÃO entram aqui — vão para ``src/ui/components/`` à medida
      que cada componente for usado.

Mapeamento com PROJETO.md:
    * §3.1 (Tipografia) → seção "Tipografia" abaixo.
    * §3.2 (Paleta de cores) → seção "Cores".
    * §3.3 (Espaçamento e forma) → seção "Espaçamento e forma".
"""

import flet as ft


# ---------------------------------------------------------------------------
# Cores (PROJETO.md §3.2)
# ---------------------------------------------------------------------------

# Primárias
COR_PRIMARIA: str = "#FF6600"      # Laranja Oui Chef — CTAs, destaques, ativo
COR_SECUNDARIA: str = "#0D0D0D"    # Preto — sidebar, textos principais
COR_TERCIARIA: str = "#FFFFFF"     # Branco — fundo de conteúdo

# Funcionais
COR_SUCESSO: str = "#16A34A"       # Venda finalizada, estoque ok
COR_ALERTA: str = "#F59E0B"        # Estoque baixo, comanda atrasada
COR_ERRO: str = "#DC2626"          # Falha, estoque crítico, cancelamento
COR_INFO: str = "#2563EB"          # Informações neutras

# Cinzas
COR_CINZA_100: str = "#F5F5F5"     # Fundo de área de conteúdo, hover sutil
COR_CINZA_200: str = "#E5E5E5"     # Bordas, divisores
COR_CINZA_400: str = "#A3A3A3"     # Textos secundários, placeholders
COR_CINZA_600: str = "#525252"     # Textos de apoio

# Estados
COR_HOVER_LARANJA: str = "#E55A00"  # Hover de botão primário
COR_LARANJA_SUAVE: str = "#FFF1E6"  # Fundo de item ativo na sidebar, badges


# ---------------------------------------------------------------------------
# Tipografia (PROJETO.md §3.1)
# ---------------------------------------------------------------------------

FONTE_FAMILIA: str = "Inter"

# Pesos (Inter — Google Fonts).
FONTE_PESO_REGULAR: int = 400      # Corpo de texto, descrições, labels secundários
FONTE_PESO_MEDIUM: int = 500       # Labels de campos, textos de tabela, nomes
FONTE_PESO_SEMIBOLD: int = 600     # Títulos de seção, valores em destaque, botões
FONTE_PESO_BOLD: int = 700         # Títulos principais, valores monetários, métricas

# Tamanhos (em px).
FONTE_TAMANHO_TITULO_PRINCIPAL: int = 24   # Título principal de tela (SemiBold)
FONTE_TAMANHO_TITULO_SECAO: int = 18       # Título de seção (SemiBold)
FONTE_TAMANHO_LABEL: int = 14              # Subtítulo / label (Medium)
FONTE_TAMANHO_CORPO: int = 14              # Corpo de texto (Regular)
FONTE_TAMANHO_HELPER: int = 12             # Texto de apoio / helper (Regular)
FONTE_TAMANHO_VALOR_DESTAQUE: int = 28     # Valor monetário em destaque (Bold)


# ---------------------------------------------------------------------------
# Espaçamento e forma (PROJETO.md §3.3)
# ---------------------------------------------------------------------------

# Border-radius.
BORDER_RADIUS_INPUT: int = 8
BORDER_RADIUS_BOTAO: int = 8
BORDER_RADIUS_CARD: int = 12
BORDER_RADIUS_MODAL: int = 16

# Alturas (em px).
ALTURA_INPUT: int = 44
ALTURA_BOTAO: int = 48
ALTURA_BOTAO_GRANDE: int = 56      # CTAs grandes (ex.: "Finalizar Venda")
ALTURA_LINHA_TABELA: int = 60
ALTURA_TOPBAR: int = 64

# Largura fixa da sidebar.
LARGURA_SIDEBAR: int = 240

# Paddings.
PADDING_CARD: int = 24
PADDING_FORMULARIO: int = 32


# ---------------------------------------------------------------------------
# Factory do Theme Flet
# ---------------------------------------------------------------------------

def build_flet_theme() -> ft.Theme:
    """Constrói o :class:`ft.Theme` global da aplicação.

    Aplica ``Inter`` como fonte padrão e usa :data:`COR_PRIMARIA` como
    semente do Material 3 — o Flet deriva uma paleta coerente a partir
    do laranja Oui Chef. ``visual_density`` é ``COMFORTABLE`` para dar
    respiro adequado em monitores desktop (sem virar interface de tablet).

    A fonte ``Inter`` propriamente dita precisa ser registrada em
    ``page.fonts`` no ``main.py`` (assets bundled) — esta função apenas
    declara a família a ser usada.

    Returns:
        :class:`ft.Theme` pronto para atribuição em ``page.theme``.
    """
    return ft.Theme(
        font_family=FONTE_FAMILIA,
        color_scheme_seed=COR_PRIMARIA,
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
