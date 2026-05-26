"""Formulario de criar/editar Fornecedor — Passo 3 da Fase 2.

Referencias visuais:
    * ``prototipos/04-formulario-cadastro.png`` (estrutura generica).
    * Mesmo padrao de :class:`FormCategoriaView`, ampliado: 5 campos
      verticais (Nome, CNPJ, Telefone, Contato, Observacoes).

A mesma view atende dois modos:
    * ``fornecedor_id=None`` → **modo CRIAR**: sem Switch "Ativo"
      (criacao sempre nasce ``ativo=True``).
    * ``fornecedor_id=<int>`` → **modo EDITAR**: campos pre-preenchidos
      + Switch "Fornecedor ativo" visivel.

Estrategia de CNPJ (decisao Fase 2):
    * Usuario digita com ou sem mascara — ambos aceitos.
    * NAO formatamos enquanto digita (gera bugs com cursor position).
    * No submit: normaliza via ``utils.cnpj.normalizar_cnpj``.
    * Em modo EDITAR: pre-preenche formatado via
      ``utils.cnpj.formatar_cnpj``.

Layout:
    * Topbar "Novo Fornecedor" | "Editar Fornecedor" (sem acao_direita).
    * Card branco com 5 campos verticais + Switch (modo EDITAR).
    * Rodape [Cancelar] + [Criar Fornecedor | Salvar Alteracoes].

Callbacks:
    * ``on_voltar`` — Cancelar (sem salvar).
    * ``on_salvar`` — apos gravacao bem-sucedida.
"""

from __future__ import annotations

import traceback
from typing import Callable

import flet as ft

from src.database.connection import get_session
from src.services.fornecedor_service import FornecedorService
from src.ui import components, theme
from src.utils.cnpj import formatar_cnpj
from src.utils.exceptions import NomeDuplicadoError


class FormFornecedorView:
    """Formulario CRUD de Fornecedor (criar/editar)."""

    def __init__(
        self,
        page: ft.Page,
        fornecedor_id: int | None,
        on_voltar: Callable[[], None],
        on_salvar: Callable[[], None],
    ) -> None:
        """Cria a view.

        Args:
            page: Pagina Flet onde o form sera montado.
            fornecedor_id: ``None`` para modo CRIAR, ``int`` para EDITAR.
            on_voltar: Callback do botao Cancelar.
            on_salvar: Callback apos gravacao bem-sucedida.
        """
        self._page = page
        self._fornecedor_id = fornecedor_id
        self._modo_criar = fornecedor_id is None
        self._on_voltar = on_voltar
        self._on_salvar = on_salvar

        # Referencias aos controles (preenchidas em build()).
        self._campo_nome: ft.TextField | None = None
        self._campo_cnpj: ft.TextField | None = None
        self._campo_telefone: ft.TextField | None = None
        self._campo_contato: ft.TextField | None = None
        self._campo_observacoes: ft.TextField | None = None
        self._switch_ativo: ft.Switch | None = None
        self._texto_erro: ft.Text | None = None

    # ------------------------------------------------------------------
    # Construcao
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Constroi a arvore de Controls e retorna o Container raiz."""
        # Factory de TextField com cores forcadas (mata tonalizacao M3).
        def _campo(**kwargs) -> ft.TextField:
            return ft.TextField(
                border_radius=theme.BORDER_RADIUS_INPUT,
                border_color=theme.COR_CINZA_200,
                focused_border_color=theme.COR_PRIMARIA,
                filled=False,
                bgcolor=theme.COR_TERCIARIA,
                text_size=theme.FONTE_TAMANHO_CORPO,
                **kwargs,
            )

        self._campo_nome = _campo(
            label="Nome",
            hint_text="ex: Distribuidora ABC",
            max_length=150,
        )

        self._campo_cnpj = _campo(
            label="CNPJ",
            hint_text="00.000.000/0000-00",
            max_length=18,
        )

        self._campo_telefone = _campo(
            label="Telefone",
            hint_text="ex: (11) 9 9999-9999",
            max_length=30,
        )

        self._campo_contato = _campo(
            label="Contato",
            hint_text="ex: João (vendedor)",
            max_length=100,
        )

        self._campo_observacoes = _campo(
            label="Observações",
            hint_text="Observações adicionais (max 1000 caracteres)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            max_length=1000,
        )

        # Switch apenas em modo EDITAR (criacao sempre ativo=True).
        if not self._modo_criar:
            self._switch_ativo = ft.Switch(
                label="Fornecedor ativo",
                value=True,
                active_color=theme.COR_PRIMARIA,
            )

        self._texto_erro = ft.Text(
            value="",
            color=theme.COR_ERRO,
            size=theme.FONTE_TAMANHO_CORPO,
            weight=ft.FontWeight.W_500,
            visible=False,
        )

        # Pre-preenche em modo EDITAR (antes do attach a pagina).
        if not self._modo_criar:
            self._carregar_fornecedor()

        # Enter como Tab — mitigacao do bug Tab-escapa-pra-sidebar
        # (limitacao Flet 0.85.1, ver CLAUDE.md "Pegadinhas Flet 0.85.1").
        # Observacoes eh multiline e fica fora da cadeia (Enter insere
        # quebra de linha). Contato eh o ultimo TextField encadeavel —
        # confirma o form (esperado: Enter no ultimo campo = Salvar).
        # focus() eh coroutine async — usar helper que retorna async
        # handler. Lambda sync NAO funciona. _salvar eh sync, ok direto.
        self._campo_nome.on_submit = components.proximo_campo(
            self._campo_cnpj
        )
        self._campo_cnpj.on_submit = components.proximo_campo(
            self._campo_telefone
        )
        self._campo_telefone.on_submit = components.proximo_campo(
            self._campo_contato
        )
        self._campo_contato.on_submit = self._salvar

        # Monta lista de campos (todos verticais — form mais alto que largo).
        campos: list[ft.Control] = [
            self._campo_nome,
            self._campo_cnpj,
            self._campo_telefone,
            self._campo_contato,
            self._campo_observacoes,
        ]
        if not self._modo_criar:
            assert self._switch_ativo is not None
            campos.append(self._switch_ativo)
        campos.append(self._texto_erro)

        titulo = "Novo Fornecedor" if self._modo_criar else "Editar Fornecedor"
        rotulo_salvar = (
            "Criar Fornecedor" if self._modo_criar else "Salvar Alterações"
        )

        return ft.Column(
            controls=[
                components.topbar(titulo),
                components.card_form(
                    campos=campos,
                    botoes=[
                        components.botao_secundario(
                            "Cancelar",
                            lambda e: self._on_voltar(),
                        ),
                        components.botao_primario(
                            rotulo_salvar,
                            self._salvar,
                        ),
                    ],
                ),
            ],
            spacing=0,
            expand=True,
        )

    # ------------------------------------------------------------------
    # Carga (modo EDITAR)
    # ------------------------------------------------------------------

    def _carregar_fornecedor(self) -> None:
        """Pre-preenche os campos a partir do banco em modo EDITAR.

        Edge case impossivel em single-machine: se ``buscar_por_id``
        retorna ``None``, loga warning e segue com campos vazios. Salvar
        vai falhar com ``ValueError`` do service e a mensagem aparece
        inline. Nao chamamos ``on_voltar`` aqui para evitar recursao
        dentro de ``build`` (duplicaria o shell na page).
        """
        assert self._campo_nome is not None
        assert self._campo_cnpj is not None
        assert self._campo_telefone is not None
        assert self._campo_contato is not None
        assert self._campo_observacoes is not None
        assert self._switch_ativo is not None

        with get_session() as session:
            service = FornecedorService(session)
            fornecedor = service.buscar_por_id(self._fornecedor_id)  # type: ignore[arg-type]

            if fornecedor is None:
                print(
                    f"AVISO: FormFornecedorView aberto em modo EDITAR com "
                    f"id={self._fornecedor_id} inexistente. Form vazio."
                )
                return

            self._campo_nome.value = fornecedor.nome
            # Exibe CNPJ formatado para o usuario.
            self._campo_cnpj.value = formatar_cnpj(fornecedor.cnpj)
            self._campo_telefone.value = fornecedor.telefone or ""
            self._campo_contato.value = fornecedor.contato or ""
            self._campo_observacoes.value = fornecedor.observacoes or ""
            self._switch_ativo.value = fornecedor.ativo

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------

    def _salvar(self, e: ft.ControlEvent) -> None:
        """Valida e grava (criar ou atualizar) o fornecedor."""
        assert self._campo_nome is not None
        assert self._campo_cnpj is not None
        assert self._campo_telefone is not None
        assert self._campo_contato is not None
        assert self._campo_observacoes is not None
        assert self._texto_erro is not None

        # Limpa erro anterior.
        self._texto_erro.value = ""
        self._texto_erro.visible = False

        nome = (self._campo_nome.value or "").strip()
        if not nome:
            self._mostrar_erro("Nome é obrigatório.")
            return

        # Service cuida de normalizar/validar tamanho de CNPJ.
        cnpj = self._campo_cnpj.value or None
        telefone = (self._campo_telefone.value or "").strip() or None
        contato = (self._campo_contato.value or "").strip() or None
        observacoes = (self._campo_observacoes.value or "").strip() or None

        # ``ativo`` so existe no modo EDITAR; criacao sempre True.
        if self._modo_criar:
            ativo = True
        else:
            assert self._switch_ativo is not None
            ativo = bool(self._switch_ativo.value)

        try:
            with get_session() as session:
                service = FornecedorService(session)
                if self._modo_criar:
                    service.criar(
                        nome=nome,
                        cnpj=cnpj,
                        telefone=telefone,
                        contato=contato,
                        observacoes=observacoes,
                    )
                else:
                    service.atualizar(
                        self._fornecedor_id,  # type: ignore[arg-type]
                        nome,
                        cnpj,
                        telefone,
                        contato,
                        observacoes,
                        ativo,
                    )
        except NomeDuplicadoError as ex:
            self._mostrar_erro(str(ex))
            return
        except ValueError as ex:
            self._mostrar_erro(str(ex))
            return
        except Exception as ex:
            traceback.print_exc()
            self._mostrar_erro(f"Erro inesperado: {ex}")
            return

        self._on_salvar()

    def _mostrar_erro(self, mensagem: str) -> None:
        """Exibe ``mensagem`` no Text de erro inline e atualiza a pagina."""
        assert self._texto_erro is not None
        self._texto_erro.value = mensagem
        self._texto_erro.visible = True
        self._page.update()
