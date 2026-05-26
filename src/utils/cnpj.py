"""Utilitarios para tratamento de CNPJ.

Estrategia: armazenar 14 digitos puros, exibir formatado.
NAO validar algoritmo dos digitos verificadores (decisao MVP).
"""

from __future__ import annotations

import re


def normalizar_cnpj(cnpj_raw: str | None) -> str | None:
    """Remove todos os caracteres nao-digitos do CNPJ.

    Retorna ``None`` se input vazio/None. Retorna string com so digitos
    caso contrario.

    Exemplos:
        >>> normalizar_cnpj("12.345.678/0001-90")
        '12345678000190'
        >>> normalizar_cnpj("12345678000190")
        '12345678000190'
        >>> normalizar_cnpj("") is None
        True
        >>> normalizar_cnpj(None) is None
        True
    """
    if not cnpj_raw:
        return None
    digitos = re.sub(r"\D", "", cnpj_raw)
    return digitos if digitos else None


def formatar_cnpj(cnpj_normalizado: str | None) -> str:
    """Formata CNPJ para exibicao (``XX.XXX.XXX/XXXX-XX``).

    Espera input com 14 digitos puros. Retorna string vazia se ``None``.
    Se input nao tiver exatamente 14 digitos, retorna o input como esta
    (defensivo — nao quebra UI se dado historico for malformado).
    """
    if not cnpj_normalizado:
        return ""
    if len(cnpj_normalizado) != 14 or not cnpj_normalizado.isdigit():
        return cnpj_normalizado
    return (
        f"{cnpj_normalizado[:2]}.{cnpj_normalizado[2:5]}."
        f"{cnpj_normalizado[5:8]}/{cnpj_normalizado[8:12]}-"
        f"{cnpj_normalizado[12:]}"
    )
