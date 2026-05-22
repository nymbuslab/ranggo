"""Formulário de criar/editar Categoria — Passo 1 da Fase 2.

Referências visuais:
    * ``prototipos/04-formulario-cadastro.png`` (estrutura genérica).
    * Mesmo padrão de :class:`FormUsuarioView`, simplificado: 2 campos.

A mesma view atende dois modos:
    * ``categoria_id=None`` → **modo CRIAR**: sem Switch "Ativa" (criação
      sempre nasce ``ativo=True``).
    * ``categoria_id=<int>`` → **modo EDITAR**: campos pré-preenchidos
      + Switch "Categoria ativa" visível.

Layout:
    * Topbar "Nova Categoria" | "Editar Categoria" (sem acao_direita).
    * Card branco com Nome (obrigatório) + Descrição (opcional, multiline)
      + Switch (modo EDITAR).
    * Rodapé [Cancelar] + [Criar Categoria | Salvar Alterações].

Callbacks:
    * ``on_voltar`` — Cancelar (sem salvar).
    * ``on_salvar`` — após gravação bem-sucedida.
"""

from __future__ import annotations

import traceback
from typing import Callable

import flet as ft

from src.database.connection import get_session
from src.services.categoria_service import CategoriaService
from src.ui import components, theme
from src.utils.exceptions import NomeDuplicadoError


class FormCategoriaView:
    """Formulário CRUD de Categoria (criar/editar)."""

    def __init__(
        self,
        page: ft.Page,
        categoria_id: int | None,
        on_voltar: Callable[[], None],
        on_salvar: Callable[[], None],
    ) -> None:
        """Cria a view.

        Args:
            page: Página Flet onde o form será montado.
            categoria_id: ``None`` para modo CRIAR, ``int`` para EDITAR.
            on_voltar: Callback do botão Cancelar.
            on_salvar: Callback após gravação bem-sucedida.
        """
        self._page = page
        self._categoria_id = categoria_id
        self._modo_criar = categoria_id is None
        self._on_voltar = on_voltar
        self._on_salvar = on_salvar

        # Referências aos controles (preenchidas em build()).
        self._campo_nome: ft.TextField | None = None
        self._campo_descricao: ft.TextField | None = None
        self._switch_ativa: ft.Switch | None = None
        self._texto_erro: ft.Text | None = None

    # ------------------------------------------------------------------
    # Construção
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Constrói a árvore de Controls e retorna o Container raiz."""
        # Factory de TextField com cores forçadas (mata tonalização M3).
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
            hint_text="Digite o nome da categoria",
        )

        self._campo_descricao = _campo(
            label="Descrição",
            hint_text="Descrição opcional, até 500 caracteres",
            multiline=True,
            min_lines=2,
            max_lines=4,
            max_length=500,
        )

        # Switch apenas em modo EDITAR (criação sempre ativa=True).
        if not self._modo_criar:
            self._switch_ativa = ft.Switch(
                label="Categoria ativa",
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

        # Pré-preenche em modo EDITAR (antes do attach à página).
        if not self._modo_criar:
            self._carregar_categoria()

        # Monta lista de campos.
        campos: list[ft.Control] = [self._campo_nome, self._campo_descricao]
        if not self._modo_criar:
            assert self._switch_ativa is not None
            campos.append(self._switch_ativa)
        campos.append(self._texto_erro)

        titulo = "Nova Categoria" if self._modo_criar else "Editar Categoria"
        rotulo_salvar = (
            "Criar Categoria" if self._modo_criar else "Salvar Alterações"
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

    def _carregar_categoria(self) -> None:
        """Pré-preenche os campos a partir do banco em modo EDITAR.

        Edge case impossível em single-machine: se ``buscar_por_id``
        retorna ``None``, loga warning e segue com campos vazios. Salvar
        vai falhar com ``ValueError`` do service e a mensagem aparece
        inline. Não chamamos ``on_voltar`` aqui para evitar recursão
        dentro de ``build`` (duplicaria o shell na page).
        """
        assert self._campo_nome is not None
        assert self._campo_descricao is not None
        assert self._switch_ativa is not None

        with get_session() as session:
            service = CategoriaService(session)
            categoria = service.buscar_por_id(self._categoria_id)  # type: ignore[arg-type]

            if categoria is None:
                print(
                    f"AVISO: FormCategoriaView aberto em modo EDITAR com "
                    f"id={self._categoria_id} inexistente. Form vazio."
                )
                return

            self._campo_nome.value = categoria.nome
            self._campo_descricao.value = categoria.descricao or ""
            self._switch_ativa.value = categoria.ativo

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------

    def _salvar(self, e: ft.ControlEvent) -> None:
        """Valida e grava (criar ou atualizar) a categoria."""
        assert self._campo_nome is not None
        assert self._campo_descricao is not None
        assert self._texto_erro is not None

        # Limpa erro anterior.
        self._texto_erro.value = ""
        self._texto_erro.visible = False

        nome = (self._campo_nome.value or "").strip()
        if not nome:
            self._mostrar_erro("Nome é obrigatório.")
            return

        descricao = (self._campo_descricao.value or "").strip() or None

        # ``ativa`` só existe no modo EDITAR; criação sempre True.
        if self._modo_criar:
            ativa = True
        else:
            assert self._switch_ativa is not None
            ativa = bool(self._switch_ativa.value)

        try:
            with get_session() as session:
                service = CategoriaService(session)
                if self._modo_criar:
                    service.criar(nome, descricao)
                else:
                    service.atualizar(
                        self._categoria_id,  # type: ignore[arg-type]
                        nome,
                        descricao,
                        ativa,
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
        """Exibe ``mensagem`` no Text de erro inline e atualiza a página."""
        assert self._texto_erro is not None
        self._texto_erro.value = mensagem
        self._texto_erro.visible = True
        self._page.update()
