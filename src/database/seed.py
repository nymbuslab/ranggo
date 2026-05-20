"""População inicial idempotente do banco do Ranggo.

Executada no startup pelo ``main.py`` logo depois de :func:`init_db`.
Cada função de seed verifica o que **já existe** antes de inserir, de
modo que múltiplas execuções não duplicam dados nem disparam erro de
UNIQUE — pode ser chamada em todo boot da aplicação sem efeito colateral.

Escopo após Fase 1:
    * :class:`UnidadeMedida` — UN, KG, G, L, ML (cadastro fixo).
    * :class:`Perfil` — Admin, Gerente, Caixa (estrutura de papéis).
    * :class:`Permissao` — cadastrar_usuario, acessar_relatorios,
      aplicar_desconto (3 permissões da Fase 1).
    * Amarrações ``perfil_permissoes`` — Admin recebe todas, Gerente
      recebe relatórios + desconto, Caixa fica sem permissões granulares.
    * :class:`Usuario` Admin inicial — login ``admin`` / senha
      ``admin123`` (hash bcrypt). **Trocar antes de produção.**

Não populado nesta fase:
    * Permissões de Fases 2+ (cancelar_venda, editar_cadastros, etc.) —
      entram junto com as features que as exigem.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.connection import get_session
from src.database.models import Perfil, Permissao, UnidadeMedida
from src.repositories.perfil_repository import PerfilRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services.auth_service import AuthService


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

_PERMISSOES_PADRAO: list[tuple[str, str]] = [
    ("cadastrar_usuario", "Criar, editar e desativar usuarios do sistema"),
    ("acessar_relatorios", "Visualizar relatorios gerenciais"),
    ("aplicar_desconto", "Aplicar desconto manual em venda"),
]

# Cada perfil recebe a lista (possivelmente vazia) de códigos de
# permissão. Caixa fica sem permissões granulares — opera apenas as
# funções básicas de venda já liberadas implicitamente pelo perfil.
_AMARRACOES_PERFIL_PERMISSAO: dict[str, list[str]] = {
    "Admin": ["cadastrar_usuario", "acessar_relatorios", "aplicar_desconto"],
    "Gerente": ["acessar_relatorios", "aplicar_desconto"],
    "Caixa": [],
}

# ATENÇÃO: senha "admin123" é pública (código aberto na pasta).
# Trocar via tela de Usuários antes de instalar em ambiente real.
# Política de "trocar senha no primeiro login" entra na Fase 5.
_ADMIN_INICIAL: dict[str, str] = {
    "login": "admin",
    "nome": "Administrador",
    "senha_plana": "admin123",
}


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


def _seed_permissoes(session: Session) -> None:
    """Garante que as permissões da Fase 1 existam em ``permissoes``.

    Insere apenas os códigos ausentes; não atualiza descrição de permissão
    já cadastrada. Imprime resumo no console.

    Args:
        session: Sessão SQLAlchemy ativa; o ``commit`` é responsabilidade
            do chamador (via :func:`get_session`).
    """
    existentes: set[str] = set(
        session.execute(select(Permissao.codigo)).scalars().all()
    )
    a_inserir = [
        Permissao(codigo=codigo, descricao=descricao)
        for codigo, descricao in _PERMISSOES_PADRAO
        if codigo not in existentes
    ]
    if a_inserir:
        session.add_all(a_inserir)
    print(
        f"Seed Permissao: inseridas {len(a_inserir)}, "
        f"já existentes {len(existentes)}."
    )


def _seed_perfil_permissoes(session: Session) -> None:
    """Garante que as amarrações ``perfil_permissoes`` existam.

    Carrega cada perfil pelo nome e cada permissão pelo código (ambos
    via relationship N:N do model) e adiciona apenas as amarrações
    ausentes. Não remove amarrações extras criadas manualmente pelo
    operador — só insere o que falta para o estado mínimo.

    Args:
        session: Sessão SQLAlchemy ativa; o ``commit`` é responsabilidade
            do chamador (via :func:`get_session`).
    """
    criadas = 0
    ja_existentes = 0

    for nome_perfil, codigos in _AMARRACOES_PERFIL_PERMISSAO.items():
        if not codigos:
            continue

        perfil = session.execute(
            select(Perfil).where(Perfil.nome == nome_perfil)
        ).scalar_one()

        codigos_atuais = {p.codigo for p in perfil.permissoes}

        for codigo in codigos:
            if codigo in codigos_atuais:
                ja_existentes += 1
                continue
            permissao = session.execute(
                select(Permissao).where(Permissao.codigo == codigo)
            ).scalar_one()
            perfil.permissoes.append(permissao)
            criadas += 1

    print(
        f"Seed perfil_permissoes: criadas {criadas} amarracoes, "
        f"já existentes {ja_existentes}."
    )


def _seed_usuario_admin(session: Session) -> None:
    """Garante que o usuário Admin inicial exista em ``usuarios``.

    Se o login ``admin`` já existe, **não** atualiza nada — preserva
    eventual troca manual de senha feita pelo operador. Se não existe,
    cria com perfil Admin, senha ``admin123`` hasheada via
    :class:`AuthService`. A senha é pública (código aberto): trocar
    antes de qualquer instalação em produção real.

    Args:
        session: Sessão SQLAlchemy ativa; o ``commit`` é responsabilidade
            do chamador (via :func:`get_session`).

    Raises:
        RuntimeError: Se o perfil ``Admin`` não existir (significa que
            :func:`_seed_perfis` não rodou antes — bug de ordem em
            :func:`popular_dados_iniciais`).
    """
    repo_usuario = UsuarioRepository(session)

    if repo_usuario.buscar_por_login(_ADMIN_INICIAL["login"]) is not None:
        print("Seed Usuario Admin: ja existe, nada a fazer.")
        return

    repo_perfil = PerfilRepository(session)
    perfil_admin = repo_perfil.buscar_por_nome("Admin")
    if perfil_admin is None:
        raise RuntimeError(
            "Perfil 'Admin' nao encontrado — _seed_perfis deve rodar "
            "antes de _seed_usuario_admin."
        )

    auth = AuthService(session)
    senha_hash = auth.criar_hash(_ADMIN_INICIAL["senha_plana"])

    repo_usuario.criar(
        {
            "nome": _ADMIN_INICIAL["nome"],
            "login": _ADMIN_INICIAL["login"],
            "senha_hash": senha_hash,
            "perfil_id": perfil_admin.id,
            "ativo": True,
        }
    )
    print(
        f"Seed Usuario Admin: criado com login "
        f"'{_ADMIN_INICIAL['login']}' / senha "
        f"'{_ADMIN_INICIAL['senha_plana']}'."
    )


def popular_dados_iniciais() -> None:
    """Popula o banco com dados fixos da Fase 0 + Fase 1 (idempotente).

    Abre uma única :class:`Session` via :func:`get_session` e delega
    para as funções privadas de cada entidade. O ``commit`` é feito
    automaticamente pelo context manager no sucesso; em caso de exceção
    em qualquer função, o ``rollback`` é acionado e a exceção propaga.

    Ordem importa: perfis antes de amarrações e do usuário Admin;
    permissões antes das amarrações.
    """
    with get_session() as session:
        _seed_unidades_medida(session)
        _seed_perfis(session)
        _seed_permissoes(session)
        _seed_perfil_permissoes(session)
        _seed_usuario_admin(session)
    print("Dados iniciais OK.")
