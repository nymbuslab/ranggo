"""Entry point real do Ranggo.

Único módulo responsável pelo *bootstrap* do aplicativo:

1. :func:`init_db` — cria as tabelas no SQLite (idempotente).
2. :func:`popular_dados_iniciais` — seed de UnidadeMedida e Perfil
   (idempotente).
3. :func:`ft.app` — inicia o runtime do Flet usando o wrapper
   :func:`_ui_main_com_assets`, que registra a fonte Inter antes de
   delegar para o ``main`` da camada de UI em ``src/ui/app.py``.

Em caso de falha em qualquer etapa de bootstrap, imprime o erro no
``stderr`` (com traceback) e aborta com ``sys.exit(1)`` — comportamento
*fail-fast*: melhor não abrir UI corrompida do que renderizar algo com
banco quebrado.

Este é o **único** lugar do projeto que importa ``init_db``,
``popular_dados_iniciais`` ou chama ``ft.app(...)``. Demais módulos
permanecem ignorantes sobre o ciclo de vida do app.
"""

import atexit
import sys
import traceback

import flet as ft

from src.database.connection import engine, init_db
from src.database.seed import popular_dados_iniciais
from src.ui.app import main as ui_main


# Rede de segurança: se o app encerrar por qualquer caminho que não passe pelo
# handler de CLOSE em src/ui/app.py (ex.: exceção no startup, kill externo),
# o pool ainda libera o lock do SQLite antes do processo morrer.
atexit.register(engine.dispose)


def _ui_main_com_assets(page: ft.Page) -> None:
    """Wrapper de UI que registra fontes antes de delegar para ``ui_main``.

    Mantém ``src/ui/app.py`` ignorante sobre caminhos físicos de
    arquivos — a UI pura conhece apenas a *família* ``Inter`` declarada
    em :data:`src.ui.theme.FONTE_FAMILIA`. O mapeamento família →
    arquivo .ttf vive aqui, no entry point, junto do bootstrap.

    Caminhos em ``page.fonts`` são relativos a ``assets_dir`` (definido
    em :func:`ft.app`), portanto **não** incluem o prefixo ``assets/``.

    Args:
        page: Página fornecida pelo runtime do Flet.
    """
    page.fonts = {
        "Inter": "fonts/Inter-VariableFont_opsz_wght.ttf",
        "Inter Italic": "fonts/Inter-Italic-VariableFont_opsz_wght.ttf",
    }
    ui_main(page)


def bootstrap() -> None:
    """Orquestra o startup completo do app.

    Fluxo: ``init_db`` → ``popular_dados_iniciais`` → ``ft.app(...)``.
    Qualquer exceção encerra o processo com ``sys.exit(1)`` após logar
    traceback em ``stderr``.
    """
    try:
        print("Iniciando Ranggo...")
        init_db()
        popular_dados_iniciais()
        print("UI iniciada.")
        ft.run(main=_ui_main_com_assets, assets_dir="assets")
    except Exception as e:
        print(f"[ERRO] Falha no startup: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    bootstrap()
