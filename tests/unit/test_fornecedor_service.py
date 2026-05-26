"""Testes unitarios do FornecedorService + helpers de CNPJ.

Cobre as regras criticas:
1. criar: nome obrigatorio; CNPJ opcional; CNPJ duplicado da erro;
   varios sem CNPJ nao conflitam.
2. atualizar: permite manter proprio CNPJ; bloqueia roubar CNPJ alheio.
3. helpers cnpj: normalizar/formatar — happy path + edge cases.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.services.fornecedor_service import FornecedorService
from src.utils.cnpj import formatar_cnpj, normalizar_cnpj
from src.utils.exceptions import NomeDuplicadoError


# ----------------------------------------------------------------------
# FornecedorService.criar
# ----------------------------------------------------------------------

class TestCriar:
    """Testes do metodo criar()."""

    def test_criar_fornecedor_valido_com_so_nome(self, session: Session) -> None:
        """Apenas nome eh obrigatorio — outros 4 campos podem ser None."""
        service = FornecedorService(session)

        fornecedor = service.criar(nome="Distribuidora Sao Paulo")

        assert fornecedor.id is not None
        assert fornecedor.nome == "Distribuidora Sao Paulo"
        assert fornecedor.cnpj is None
        assert fornecedor.telefone is None
        assert fornecedor.contato is None
        assert fornecedor.observacoes is None
        assert fornecedor.ativo is True

    def test_criar_fornecedor_completo(self, session: Session) -> None:
        """Todos campos preenchidos — CNPJ vem com mascara, sai normalizado."""
        service = FornecedorService(session)

        fornecedor = service.criar(
            nome="Hortifruti Bom Preco",
            cnpj="12.345.678/0001-90",
            telefone="(11) 99999-9999",
            contato="Maria",
            observacoes="Entrega quarta e sabado",
        )

        assert fornecedor.cnpj == "12345678000190"  # so digitos
        assert fornecedor.telefone == "(11) 99999-9999"  # livre, nao normaliza
        assert fornecedor.contato == "Maria"
        assert fornecedor.observacoes == "Entrega quarta e sabado"

    def test_criar_nome_vazio_levanta_value_error(self, session: Session) -> None:
        service = FornecedorService(session)

        with pytest.raises(ValueError) as excinfo:
            service.criar(nome="   ")  # so espacos, fica vazio apos strip
        assert "obrigatorio" in str(excinfo.value).lower()

    def test_criar_dois_fornecedores_sem_cnpj_nao_conflita(
        self, session: Session
    ) -> None:
        """CNPJ vazio em ambos nao deve levantar erro — multiplos NULLs OK."""
        service = FornecedorService(session)

        primeiro = service.criar(nome="Fornecedor A")
        session.commit()
        segundo = service.criar(nome="Fornecedor B")  # sem CNPJ tambem
        session.commit()

        assert primeiro.id != segundo.id
        assert primeiro.cnpj is None
        assert segundo.cnpj is None

    def test_criar_cnpj_duplicado_levanta_nome_duplicado_error(
        self, session: Session
    ) -> None:
        """Dois fornecedores com mesmo CNPJ — segundo deve falhar."""
        service = FornecedorService(session)
        service.criar(nome="Empresa A", cnpj="12.345.678/0001-90")
        session.commit()

        with pytest.raises(NomeDuplicadoError) as excinfo:
            service.criar(nome="Empresa B", cnpj="12345678000190")
        # Mensagem usa CNPJ formatado.
        assert "12.345.678/0001-90" in str(excinfo.value)


# ----------------------------------------------------------------------
# FornecedorService.atualizar
# ----------------------------------------------------------------------

class TestAtualizar:
    """Testes do metodo atualizar()."""

    def test_atualizar_mantendo_proprio_cnpj_nao_levanta(
        self, session: Session
    ) -> None:
        """Editar fornecedor com CNPJ X mantendo CNPJ X eh valido."""
        service = FornecedorService(session)
        fornecedor = service.criar(
            nome="Original", cnpj="12.345.678/0001-90"
        )
        session.commit()

        atualizado = service.atualizar(
            fornecedor_id=fornecedor.id,
            nome="Atualizado",
            cnpj="12.345.678/0001-90",  # mesmo CNPJ
            telefone=None,
            contato=None,
            observacoes=None,
            ativo=True,
        )

        assert atualizado.id == fornecedor.id
        assert atualizado.nome == "Atualizado"
        assert atualizado.cnpj == "12345678000190"

    def test_atualizar_para_cnpj_de_outro_levanta_erro(
        self, session: Session
    ) -> None:
        """Fornecedor A com CNPJ X; B tenta usar CNPJ X — erro."""
        service = FornecedorService(session)
        a = service.criar(nome="A", cnpj="11.111.111/0001-11")
        b = service.criar(nome="B", cnpj="22.222.222/0001-22")
        session.commit()

        with pytest.raises(NomeDuplicadoError):
            service.atualizar(
                fornecedor_id=b.id,
                nome="B",
                cnpj="11.111.111/0001-11",  # ja eh do A
                telefone=None,
                contato=None,
                observacoes=None,
                ativo=True,
            )
        # a referenciado para garantir que esta no escopo
        assert a.id != b.id


# ----------------------------------------------------------------------
# Helpers de CNPJ
# ----------------------------------------------------------------------

class TestUtilCnpj:
    """Testes dos helpers ``normalizar_cnpj`` / ``formatar_cnpj``."""

    def test_normalizar_remove_mascara(self) -> None:
        assert normalizar_cnpj("12.345.678/0001-90") == "12345678000190"
        # ja-normalizado fica como esta
        assert normalizar_cnpj("12345678000190") == "12345678000190"

    def test_normalizar_vazio_retorna_none(self) -> None:
        assert normalizar_cnpj("") is None
        assert normalizar_cnpj(None) is None
        # string so com caracteres nao-digitos colapsa para None
        assert normalizar_cnpj("./-") is None

    def test_formatar_aplica_mascara(self) -> None:
        assert formatar_cnpj("12345678000190") == "12.345.678/0001-90"

    def test_formatar_input_invalido_retorna_como_esta(self) -> None:
        # None vira string vazia
        assert formatar_cnpj(None) == ""
        assert formatar_cnpj("") == ""
        # Tamanho diferente de 14 — retorna como esta (defensivo).
        assert formatar_cnpj("123") == "123"
        # Contem letra — retorna como esta.
        assert formatar_cnpj("1234567800019X") == "1234567800019X"
