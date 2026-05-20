"""População inicial idempotente do banco do Oui Chef.

Executada no startup pelo ``main.py`` logo depois de :func:`init_db`.
Cada função de seed verifica o que **já existe** antes de inserir, de
modo que múltiplas execuções não duplicam dados nem disparam erro de
UNIQUE — pode ser chamada em todo boot da aplicação sem efeito colateral.

Escopo da Fase 0 (Opção C — meio-termo):
    * :class:`UnidadeMedida` — UN, KG, G, L, ML (cadastro fixo).
    * :class:`Perfil` — Admin, Gerente, Caixa (estrutura de papéis).

Não populado nesta fase:
    * Permissões — serão criadas pelas features que as usam (Fase 1+).
    * Usuário Admin — entra na Fase 1 junto com bcrypt e AuthService.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.connection import get_session
from src.database.models import Perfil, UnidadeMedida


# Cadastros fixos, em ordem de exibição preferida.
_UNIDADES_PADRAO: list[tuple[str, str]] = [
    ("UN", "Unidade"),
    ("KG", "Quilograma"),
    ("G", "Grama"),
    ("L", "Litro"),
    ("ML", "Mililitro"),
]

_PERFIS_PADRAO: list[tuple[str, str]] = [
    ("Admin", "Acesso total ao sistema"),
    ("Gerente", "Gestão operacional, sem acesso a configurações sensíveis"),
    ("Caixa", "Operação de venda e visualização de cardápio"),
]


def _seed_unidades_medida(session: Session) -> None:
    """Garante que UN, KG, G, L e ML existam em ``unidades_medida``.

    Insere apenas as siglas ausentes; não toca em linhas já existentes
    (mesmo que a descrição esteja diferente — não sobrescreve dados do
    operador). Imprime resumo no console.

    Args:
        session: Sessão SQLAlchemy ativa; o ``commit`` é responsabilidade
            do chamador (via :func:`get_session`).
    """
    existentes: set[str] = set(
        session.execute(select(UnidadeMedida.sigla)).scalars().all()
    )
    a_inserir = [
        UnidadeMedida(sigla=sigla, descricao=descricao)
        for sigla, descricao in _UNIDADES_PADRAO
        if sigla not in existentes
    ]
    if a_inserir:
        session.add_all(a_inserir)
    print(
        f"Seed UnidadeMedida: inseridas {len(a_inserir)}, "
        f"já existentes {len(existentes)}."
    )


def _seed_perfis(session: Session) -> None:
    """Garante que Admin, Gerente e Caixa existam em ``perfis``.

    Insere apenas os nomes ausentes; não atualiza descrição de perfil
    já cadastrado, para preservar customizações eventuais feitas pelo
    operador. Imprime resumo no console.

    Args:
        session: Sessão SQLAlchemy ativa; o ``commit`` é responsabilidade
            do chamador (via :func:`get_session`).
    """
    existentes: set[str] = set(
        session.execute(select(Perfil.nome)).scalars().all()
    )
    a_inserir = [
        Perfil(nome=nome, descricao=descricao)
        for nome, descricao in _PERFIS_PADRAO
        if nome not in existentes
    ]
    if a_inserir:
        session.add_all(a_inserir)
    print(
        f"Seed Perfil: inseridos {len(a_inserir)}, "
        f"já existentes {len(existentes)}."
    )


def popular_dados_iniciais() -> None:
    """Popula o banco com dados fixos da Fase 0 (idempotente).

    Abre uma única :class:`Session` via :func:`get_session` e delega
    para as funções privadas de cada entidade. O ``commit`` é feito
    automaticamente pelo context manager no sucesso; em caso de exceção
    em qualquer função, o ``rollback`` é acionado e a exceção propaga.
    """
    with get_session() as session:
        _seed_unidades_medida(session)
        _seed_perfis(session)
    print("Dados iniciais OK.")
