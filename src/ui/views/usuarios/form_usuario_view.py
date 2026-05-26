"""Formulário de criar/editar usuário — referência ``prototipos/09-formulario-usuario.png``.

A mesma view atende dois modos, distinguidos pelo construtor:

* ``usuario_id=None`` → **modo CRIAR**: campos Senha + Confirmar Senha
  visíveis, login editável, **sem** Switch "Usuário ativo" (criação
  sempre nasce ``ativo=True``).
* ``usuario_id=<int>`` → **modo EDITAR**: sem campos de senha (use o
  modal "Alterar Senha" da lista), login ``disabled`` (chave histórica),
  Switch "Usuário ativo" presente e demais campos pré-preenchidos.

Quando o usuário sendo editado é o próprio usuário logado, o Switch
"Usuário ativo" fica ``disabled`` com tooltip explicativo — defesa em
camadas, já que :meth:`UsuarioService.atualizar` também bloqueia via
:class:`PermissaoNegadaError`.

Layout principal (espelha protótipo 09):
    * Breadcrumb "Configurações / Usuários / Novo|Editar Usuário".
    * Título grande Inter SemiBold 32px (sem subtítulo redundante).
    * Card branco com campos em Column: Nome, Login, Senha+Confirmar
      lado a lado (só criar), Perfil. Switch "Ativo" apenas no editar.
    * Rodapé do card com [Cancelar] + [Criar Usuário | Salvar Alterações].

Callbacks:
    * ``on_voltar`` — clicar em "Cancelar" (sem salvar).
    * ``on_salvar`` — após gravação bem-sucedida.
"""

from __future__ import annotations

import traceback
from typing import Callable

import flet as ft

from src.database.connection import get_session
from src.repositories.perfil_repository import PerfilRepository
from src.services import sessao
from src.services.usuario_service import UsuarioService
from src.ui import components, theme
from src.utils.exceptions import (
    NomeDuplicadoError,
    PermissaoNegadaError,
    SenhaFracaError,
)


class FormUsuarioView:
    """Formulário CRUD de usuário (criar/editar)."""

    def __init__(
        self,
        page: ft.Page,
        usuario_id: int | None,
        on_voltar: Callable[[], None],
        on_salvar: Callable[[], None],
    ) -> None:
        """Cria a view.

        Args:
            page: Página Flet onde o form será montado.
            usuario_id: ``None`` para modo CRIAR, ``int`` para EDITAR.
            on_voltar: Callback do botão Cancelar (sem salvar).
            on_salvar: Callback após gravação bem-sucedida.
        """
        self._page = page
        self._usuario_id = usuario_id
        self._modo_criar = usuario_id is None
        self._on_voltar = on_voltar
        self._on_salvar = on_salvar

        # Referências aos controles (preenchidas em build()).
        self._campo_nome: ft.TextField | None = None
        self._campo_login: ft.TextField | None = None
        self._campo_perfil: ft.Dropdown | None = None
        self._campo_senha: ft.TextField | None = None
        self._campo_confirmar: ft.TextField | None = None
        self._switch_ativo: ft.Switch | None = None
        self._texto_erro: ft.Text | None = None

    # ------------------------------------------------------------------
    # Construção
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Constrói a árvore de Controls e retorna o Container raiz."""
        # Carrega opções de Perfil para o Dropdown.
        with get_session() as session:
            perfis = PerfilRepository(session).listar()
        opcoes_perfil = [
            ft.DropdownOption(key=str(p.id), text=p.nome) for p in perfis
        ]
        valor_perfil_default = str(perfis[0].id) if perfis else None

        # Cores forçadas: Material 3 tonaliza fill/border via
        # ``color_scheme_seed`` por baixo dos panos. ``filled=False`` +
        # ``bgcolor=COR_TERCIARIA`` + bordas explícitas (#E5E5E5 → #FF6600
        # no foco) garantem o look "branco + cinza + laranja vivo".
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

        # --- Campos --- (sem width fixo: cada um ocupa 100% do card)
        self._campo_nome = _campo(
            label="Nome",
            hint_text="Digite o nome completo",
        )

        self._campo_login = _campo(
            label="Login",
            hint_text="Ex: joaosilva",
            disabled=not self._modo_criar,
            tooltip=(
                None
                if self._modo_criar
                else "Login não pode ser alterado (chave histórica)."
            ),
        )

        self._campo_perfil = ft.Dropdown(
            label="Perfil",
            hint_text="Selecione um perfil",
            options=opcoes_perfil,
            value=valor_perfil_default,
            border_radius=theme.BORDER_RADIUS_INPUT,
            border_color=theme.COR_CINZA_200,
            focused_border_color=theme.COR_PRIMARIA,
            filled=False,
            bgcolor=theme.COR_TERCIARIA,
            text_size=theme.FONTE_TAMANHO_CORPO,
        )

        if self._modo_criar:
            # ``expand=1`` aplicado pelo :func:`components.campo_linha_dupla`
            # ao montar a Row — não precisa setar aqui.
            self._campo_senha = _campo(
                label="Senha",
                password=True,
                can_reveal_password=True,
            )
            self._campo_confirmar = _campo(
                label="Confirmar Senha",
                password=True,
                can_reveal_password=True,
            )

        # Switch apenas no modo EDITAR. No modo CRIAR a criação assume
        # sempre ``ativo=True`` (não há motivo legítimo para nascer
        # desativado — desativar é uma ação posterior).
        if not self._modo_criar:
            self._switch_ativo = ft.Switch(
                label="Usuário ativo",
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

        # Pré-preenche em modo EDITAR (antes de attach à página, então
        # não precisa page.update — valores entram no estado inicial).
        if not self._modo_criar:
            self._carregar_usuario()

        # Enter como Tab — mitigacao do bug Tab-escapa-pra-sidebar
        # (limitacao Flet 0.85.1 sem tabindex; ver CLAUDE.md
        # "Pegadinhas Flet 0.85.1"). focus() eh coroutine async —
        # usar helper que retorna async handler. Lambda sync NAO
        # funciona. Dropdown nao aceita on_submit; eh o fim natural
        # da cadeia em modo EDITAR.
        if self._modo_criar:
            assert self._campo_senha is not None
            assert self._campo_confirmar is not None
            self._campo_nome.on_submit = components.proximo_campo(
                self._campo_login
            )
            self._campo_login.on_submit = components.proximo_campo(
                self._campo_senha
            )
            self._campo_senha.on_submit = components.proximo_campo(
                self._campo_confirmar
            )
            # Ultimo TextField confirma o form (Criar Usuario).
            # _salvar eh sync, nao precisa ser handler async.
            self._campo_confirmar.on_submit = self._salvar
        else:
            # Em editar, Login eh disabled e Dropdown.focus() do
            # Material nao aceita foco programatico fiavelmente (bug
            # Flutter #131120 — foco escapa pra sidebar via reading-
            # order). Como Perfil raramente muda em edicao, Enter no
            # Nome confirma o form direto. Consistente com 'ultimo
            # campo encadeavel salva' em outros forms.
            # Ver CLAUDE.md secao 'Pegadinhas Flet 0.85.1'.
            self._campo_nome.on_submit = self._salvar

        # --- Monta a lista de campos a passar para components.card_form ---
        campos: list[ft.Control] = [self._campo_nome, self._campo_login]

        if self._modo_criar:
            campos.append(
                components.campo_linha_dupla(
                    self._campo_senha,
                    self._campo_confirmar,
                )
            )

        campos.append(self._campo_perfil)

        if not self._modo_criar:
            assert self._switch_ativo is not None
            campos.append(self._switch_ativo)

        # Erro inline (visible=False enquanto não há erro).
        campos.append(self._texto_erro)

        # --- Título via topbar do shell + card via card_form ---
        # Topbar carrega o título (chrome consistente entre views).
        # Card_form é apenas o corpo cinza com o card branco centralizado.
        titulo = "Novo Usuário" if self._modo_criar else "Editar Usuário"
        rotulo_salvar = "Criar Usuário" if self._modo_criar else "Salvar Alterações"

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

    def _carregar_usuario(self) -> None:
        """Pré-preenche os campos a partir do banco em modo EDITAR.

        **Edge case impossível na prática:** se ``buscar_por_id`` retorna
        ``None`` (usuário deletado entre a lista carregar e o form abrir),
        loga um aviso e segue com campos vazios. Clicar em Salvar vai
        falhar via :class:`ValueError` do service e a mensagem aparece
        inline. Em single-machine sem concorrência, esse path nunca
        deveria executar — não invocamos ``on_voltar`` aqui para evitar
        recursão dentro de ``build`` (que duplicaria o shell na page).
        """
        assert self._campo_nome is not None
        assert self._campo_login is not None
        assert self._campo_perfil is not None
        assert self._switch_ativo is not None

        with get_session() as session:
            service = UsuarioService(session)
            usuario = service.buscar_por_id(self._usuario_id)  # type: ignore[arg-type]

            if usuario is None:
                print(
                    f"AVISO: FormUsuarioView aberto em modo EDITAR com "
                    f"id={self._usuario_id} inexistente. Form vazio."
                )
                return

            self._campo_nome.value = usuario.nome
            self._campo_login.value = usuario.login
            self._campo_perfil.value = str(usuario.perfil_id)
            self._switch_ativo.value = usuario.ativo

            # Defesa em camadas: se o usuário sendo editado é o próprio
            # logado, desabilita o Switch para não permitir nem tentar.
            # O service também protege via PermissaoNegadaError.
            atual = sessao.usuario_atual()
            if atual is not None and atual.id == usuario.id:
                self._switch_ativo.disabled = True
                self._switch_ativo.tooltip = (
                    "Você não pode desativar a própria conta. "
                    "Peça a outro Admin."
                )

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------

    def _salvar(self, e: ft.ControlEvent) -> None:
        """Valida e grava (criar ou atualizar) o usuário."""
        assert self._campo_nome is not None
        assert self._campo_login is not None
        assert self._campo_perfil is not None
        assert self._texto_erro is not None

        # Limpa erro anterior antes de revalidar.
        self._texto_erro.value = ""
        self._texto_erro.visible = False

        nome = (self._campo_nome.value or "").strip()
        if not nome:
            self._mostrar_erro("Nome é obrigatório.")
            return

        try:
            perfil_id = int(self._campo_perfil.value or "")
        except ValueError:
            self._mostrar_erro("Selecione um perfil.")
            return

        # ``ativo`` só existe no modo EDITAR; no modo CRIAR sempre True.
        if self._modo_criar:
            ativo = True
        else:
            assert self._switch_ativo is not None
            ativo = bool(self._switch_ativo.value)

        try:
            with get_session() as session:
                service = UsuarioService(session)
                if self._modo_criar:
                    login = (self._campo_login.value or "").strip()
                    senha = self._campo_senha.value or ""  # type: ignore[union-attr]
                    confirmar = self._campo_confirmar.value or ""  # type: ignore[union-attr]
                    if not login:
                        self._mostrar_erro("Login é obrigatório.")
                        return
                    if senha != confirmar:
                        self._mostrar_erro("Senhas não conferem.")
                        return
                    service.criar(nome, login, senha, perfil_id)
                else:
                    service.atualizar(self._usuario_id, nome, perfil_id, ativo)  # type: ignore[arg-type]
        except NomeDuplicadoError as ex:
            self._mostrar_erro(str(ex))
            return
        except SenhaFracaError as ex:
            self._mostrar_erro(str(ex))
            return
        except PermissaoNegadaError as ex:
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
