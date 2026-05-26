"""Service de gestao de Fornecedores.

Camada de regras de negocio sobre :class:`Fornecedor`. Centraliza tudo
que o repository (burro) nao pode decidir sozinho:

* Validacao de nome obrigatorio (nao-vazio apos ``strip``).
* Normalizacao de CNPJ (remove mascara, armazena 14 digitos puros).
* Validacao de tamanho do CNPJ (se preenchido, deve ter 14 digitos —
  algoritmo dos digitos verificadores NAO eh validado, decisao MVP).
* Validacao de CNPJ UNIQUE quando preenchido (vazio nunca conflita —
  fornecedor sem CNPJ eh aceito; multiplos sem CNPJ tambem).
* Nome NAO eh unico (decisao Fase 2 #9 — fornecedores podem ter nomes
  homonimos como "Distribuidora Sao Paulo").
* **Soft delete**: desativar eh ``ativo=False``, nunca ``DELETE`` fisico.

Service **nao** conhece Flet/UI e **nao** comita: a :class:`Session` eh
injetada pelo caller, que tambem eh responsavel por
``commit``/``rollback`` (normalmente via ``with get_session() as session``).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.fornecedor import Fornecedor
from src.repositories.fornecedor_repository import FornecedorRepository
from src.utils.cnpj import formatar_cnpj, normalizar_cnpj
from src.utils.exceptions import NomeDuplicadoError


class FornecedorService:
    """Service para gestao de Fornecedores.

    Aplica regras de negocio:
        * Nome obrigatorio (nao-vazio apos ``strip``).
        * CNPJ normalizado (so digitos) e UNIQUE quando preenchido.
        * CNPJ com 14 digitos (apos normalizar) — se nao bater, erro.
        * Soft delete via ``ativo=False`` (nunca hard delete via UI).
    """

    def __init__(self, session: Session) -> None:
        """Recebe a :class:`Session` usada por todas as operacoes.

        Args:
            session: Sessao SQLAlchemy ativa, gerenciada pelo caller.
        """
        self._session = session
        self._repo = FornecedorRepository(session)

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def listar(self, incluir_inativos: bool = False) -> list[Fornecedor]:
        """Lista fornecedores ordenados por nome.

        Args:
            incluir_inativos: Se ``True``, retorna inclusive os com
                ``ativo=False``. Default ``False`` — listagem normal de
                operacao esconde inativos, e a UI controla via toggle.

        Returns:
            Lista de :class:`Fornecedor`.
        """
        stmt = select(Fornecedor).order_by(Fornecedor.nome)
        if not incluir_inativos:
            stmt = stmt.where(Fornecedor.ativo.is_(True))
        return list(self._session.execute(stmt).scalars().all())

    def buscar_por_id(self, fornecedor_id: int) -> Fornecedor | None:
        """Busca fornecedor por id (retorna ``None`` se nao existir)."""
        return self._repo.buscar_por_id(fornecedor_id)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _limpar_opcional(valor: str | None) -> str | None:
        """Strip + colapsa string vazia para ``None`` (campos opcionais)."""
        if valor is None:
            return None
        limpo = valor.strip()
        return limpo if limpo else None

    def _validar_e_normalizar_cnpj(self, cnpj_raw: str | None) -> str | None:
        """Normaliza CNPJ e valida tamanho (14 digitos quando preenchido).

        Returns:
            ``None`` se input vazio/None; string de 14 digitos puros caso
            contrario.

        Raises:
            ValueError: Se input tem digitos mas nao soma 14 apos
                normalizar.
        """
        normalizado = normalizar_cnpj(cnpj_raw)
        if normalizado is None:
            return None
        if len(normalizado) != 14:
            raise ValueError("CNPJ deve ter 14 digitos.")
        return normalizado

    # ------------------------------------------------------------------
    # Criacao
    # ------------------------------------------------------------------

    def criar(
        self,
        nome: str,
        cnpj: str | None = None,
        telefone: str | None = None,
        contato: str | None = None,
        observacoes: str | None = None,
    ) -> Fornecedor:
        """Cria novo fornecedor.

        Validacoes (na ordem):
            1. Nome obrigatorio (apos ``strip``).
            2. CNPJ: se preenchido, normalizar e validar 14 digitos.
            3. CNPJ: se preenchido, validar UNIQUE.

        Args:
            nome: Nome do fornecedor (obrigatorio, sera trim).
            cnpj: CNPJ opcional, aceita com ou sem mascara. Sera
                normalizado para 14 digitos puros antes de salvar.
            telefone: Telefone opcional (livre, sem normalizacao).
            contato: Pessoa de contato opcional.
            observacoes: Texto livre opcional.

        Returns:
            :class:`Fornecedor` criado.

        Raises:
            ValueError: Se ``nome`` vazio apos ``strip`` OU CNPJ tem
                digitos mas nao soma 14.
            NomeDuplicadoError: Se ja existe fornecedor com esse CNPJ
                (so verifica quando CNPJ preenchido).
        """
        nome = nome.strip()
        if not nome:
            raise ValueError("Nome eh obrigatorio.")

        cnpj_normalizado = self._validar_e_normalizar_cnpj(cnpj)

        if cnpj_normalizado is not None:
            existente = self._repo.buscar_por_cnpj(cnpj_normalizado)
            if existente is not None:
                raise NomeDuplicadoError(
                    f"Ja existe um fornecedor com CNPJ "
                    f"{formatar_cnpj(cnpj_normalizado)}."
                )

        return self._repo.criar({
            "nome": nome,
            "cnpj": cnpj_normalizado,
            "telefone": self._limpar_opcional(telefone),
            "contato": self._limpar_opcional(contato),
            "observacoes": self._limpar_opcional(observacoes),
            "ativo": True,
        })

    # ------------------------------------------------------------------
    # Atualizacao
    # ------------------------------------------------------------------

    def atualizar(
        self,
        fornecedor_id: int,
        nome: str,
        cnpj: str | None,
        telefone: str | None,
        contato: str | None,
        observacoes: str | None,
        ativo: bool,
    ) -> Fornecedor:
        """Atualiza dados do fornecedor.

        Args:
            fornecedor_id: Id do fornecedor a atualizar.
            nome: Novo nome (sera trim).
            cnpj: Novo CNPJ (sera normalizado; vazio vira ``None``).
            telefone: Novo telefone (sera trim; vazio vira ``None``).
            contato: Novo contato (sera trim; vazio vira ``None``).
            observacoes: Novas observacoes (sera trim; vazio vira ``None``).
            ativo: Novo status.

        Returns:
            :class:`Fornecedor` atualizado.

        Raises:
            ValueError: Se ``fornecedor_id`` nao existe, ``nome`` vazio,
                ou CNPJ tem digitos mas nao soma 14.
            NomeDuplicadoError: Se ja existe OUTRO fornecedor com esse
                CNPJ (so verifica quando CNPJ preenchido).
        """
        nome = nome.strip()
        if not nome:
            raise ValueError("Nome eh obrigatorio.")

        fornecedor = self._repo.buscar_por_id(fornecedor_id)
        if fornecedor is None:
            raise ValueError(f"Fornecedor id={fornecedor_id} nao encontrado.")

        cnpj_normalizado = self._validar_e_normalizar_cnpj(cnpj)

        # Conflito de CNPJ — excluindo o proprio fornecedor.
        if cnpj_normalizado is not None:
            existente = self._repo.buscar_por_cnpj(cnpj_normalizado)
            if existente is not None and existente.id != fornecedor_id:
                raise NomeDuplicadoError(
                    f"Ja existe outro fornecedor com CNPJ "
                    f"{formatar_cnpj(cnpj_normalizado)}."
                )

        return self._repo.atualizar(fornecedor_id, {
            "nome": nome,
            "cnpj": cnpj_normalizado,
            "telefone": self._limpar_opcional(telefone),
            "contato": self._limpar_opcional(contato),
            "observacoes": self._limpar_opcional(observacoes),
            "ativo": ativo,
        })

    def desativar(self, fornecedor_id: int) -> None:
        """Soft delete: marca ``ativo=False`` preservando o registro.

        Atalho para o botao "Desativar" da listagem. Fornecedor nao tem
        regras de guarda como Usuario — eh so flag de status.

        Args:
            fornecedor_id: Id do fornecedor a desativar.

        Raises:
            ValueError: Se ``fornecedor_id`` nao existe.
        """
        fornecedor = self._repo.buscar_por_id(fornecedor_id)
        if fornecedor is None:
            raise ValueError(f"Fornecedor id={fornecedor_id} nao encontrado.")
        self.atualizar(
            fornecedor_id,
            fornecedor.nome,
            fornecedor.cnpj,
            fornecedor.telefone,
            fornecedor.contato,
            fornecedor.observacoes,
            False,
        )
