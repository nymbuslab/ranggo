"""Models do ORM (SQLAlchemy 2.0).

Cada entidade do domínio fica em seu próprio arquivo. Os símbolos são
re-exportados aqui para permitir imports curtos:

    from src.database.models import Base, Usuario, Perfil

Importar este pacote tem o efeito colateral de registrar todas as
tabelas em ``Base.metadata`` — pré-requisito para
``Base.metadata.create_all(engine)`` em ``init_db()``.

Ordem de import: ``Base`` primeiro, depois entidades sem dependências
(``Permissao``, ``UnidadeMedida``), depois entidades dependentes
(``Perfil`` referencia ``Permissao``; ``Usuario`` referencia ``Perfil``).
"""

from src.database.models.base import Base
from src.database.models.perfil_permissao import perfil_permissoes
from src.database.models.permissao import Permissao
from src.database.models.perfil import Perfil
from src.database.models.usuario import Usuario
from src.database.models.unidade_medida import UnidadeMedida

__all__ = [
    "Base",
    "Perfil",
    "Permissao",
    "perfil_permissoes",
    "Usuario",
    "UnidadeMedida",
]
