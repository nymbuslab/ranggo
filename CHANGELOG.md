# Changelog

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## Tipos de mudança

- **Added** — para novas funcionalidades.
- **Changed** — para mudanças em funcionalidades existentes.
- **Deprecated** — para funcionalidades que serão removidas em versões futuras.
- **Removed** — para funcionalidades removidas.
- **Fixed** — para correção de bugs.
- **Security** — para correção de vulnerabilidades.

---

## [Unreleased]

### Pausado

- Desenvolvimento em Flet 0.85.1 pausado após Passo 3 da Fase 2 (commit `80745f2`). Razão: bugs estruturais do Flet em funções básicas (Tab traversal, Material Dropdown focus) acumulam débito técnico em cada novo cadastro.
- Migração para PySide6 iniciada no projeto separado **ranggoV2**.
- Tag `v0.2.5-flet-final` cravada como checkpoint do estado final do Flet (caso a migração seja revertida).

### Added

#### Fase 2 — Cadastros (em andamento — Passos 1-3 de 10)

- **Fornecedor (CRUD completo, Passo 3/10)** — terceiro cadastro da Fase 2.
  - Model: `id`, `nome` (`String(150)` NOT NULL, **não-unique** — fornecedores podem ter nomes homônimos, decisão Fase 2 #9), `cnpj` (`String(14)` UNIQUE quando preenchido, nullable — SQLite permite múltiplos NULLs em UNIQUE naturalmente), `telefone` (`String(30)` opcional), `contato` (`String(100)` opcional), `observacoes` (`String(1000)` opcional), `ativo` (default `True`), timestamps. Sem endereço. Sem email (decisão Fase 2 #6). Registrado em `src/database/models/__init__.py`.
  - `src/utils/cnpj.py` — helpers puros: `normalizar_cnpj()` (remove máscara, retorna 14 dígitos ou `None`) e `formatar_cnpj()` (aplica máscara `XX.XXX.XXX/XXXX-XX`, defensivo: retorna input como está se inválido). NÃO valida algoritmo dos dígitos verificadores (decisão MVP).
  - `FornecedorRepository` — CRUD padrão + `buscar_por_cnpj(cnpj_normalizado)` (sem `buscar_por_nome` — nome não é unique).
  - `FornecedorService` — regras: nome obrigatório (`strip`), CNPJ normalizado para 14 dígitos puros antes de salvar, `ValueError` se CNPJ tem dígitos mas ≠ 14, UNIQUE de CNPJ via `NomeDuplicadoError` reutilizado (mensagem exibe CNPJ formatado), `atualizar` exclui o próprio id da verificação UNIQUE (permite editar mantendo próprio CNPJ), soft delete via `desativar()`.
  - `ListaFornecedoresView` — 6 colunas (NOME com avatar+nome, CNPJ formatado, TELEFONE, CONTATO, STATUS verde/cinza, AÇÕES editar/desativar). Busca local case-insensitive em **nome OU CNPJ** — input normalizado antes de comparar com `cnpj` do banco (usuário digitando "12.345" acha "12345678000190"). Toggle "Mostrar inativos". Estado-vazio adaptativo: "Nenhum fornecedor cadastrado." se lista vazia, "Nenhum fornecedor encontrado." se filtro sem resultado. Ícone `LOCAL_SHIPPING_OUTLINED`.
  - `FormFornecedorView` — 5 campos verticais: Nome obrigatório, CNPJ (max 18, aceita máscara), Telefone (max 30, livre sem normalização), Contato (max 100), Observações (multiline, `max_lines=4`, `max_length=1000`). CNPJ **não é formatado enquanto digita** (evita bugs de cursor) — normalizado só no submit. Em modo EDITAR: CNPJ pré-preenchido formatado via `formatar_cnpj()`. Switch "Fornecedor ativo" só em editar.
  - Dialog de Desativar com botão **laranja** (categoria, fornecedor, cliente — soft delete não é destrutivo-irreversível, regra cravada).
  - Sidebar: subitem "Fornecedores" agora aponta para view real (`view_id="cadastros_fornecedores_lista"`). `_VIEWS_CADASTROS` ganhou as 2 entradas novas. Novo estado de módulo `_form_fornecedor_id`. `_build_item_cadastros` ganhou o ramo para destacar "Fornecedores" quando view-filha (lista OU form) está ativa.
  - 11 testes pytest em 3 classes: `TestCriar` (só nome / completo com CNPJ mascarado normalizado / nome vazio / 2 sem CNPJ não conflita / CNPJ duplicado com mensagem formatada), `TestAtualizar` (manter próprio CNPJ OK / roubar CNPJ alheio erro), `TestUtilCnpj` (normaliza mascarado / normaliza vazio→None inclui "./-" / formata 14 dígitos / formata defensivo). Total geral: **25 passed**.

#### Enter como Tab nos forms (mitigação de bug UX transversal)

- **Bug descoberto e mitigado durante validação visual do Passo 3** — Tab key nos campos de form do shell escapa para a sidebar antes de ir para o próximo campo. Causa: Flet 0.85.1 não tem `tabindex` nem `FocusScope`/`FocusTraversalPolicy`; ordem de Tab segue `ReadingOrderTraversalPolicy` do Flutter (geometria visual + ordem da widget tree). Sidebar como primeiro filho de `Row[sidebar, conteúdo]` fica antes na cadeia. Bug afeta TODOS os forms do shell (Categoria, Usuário, Fornecedor); Login é imune por estar fora do shell.
- **Mitigação adotada**: usar **Enter** como navegação entre campos via `on_submit`. Operador de PDV espera Enter como "próximo" (idiomático em sistemas legados). Tab continua escapando, mas é aceitável — Tab é comportamento de dev/power user, não operador.
- Aplicado em 4 forms:
  - `LoginView` (`src/ui/views/login_view.py`): Usuário → Senha → `_tentar_login()`.
  - `FormUsuarioView` (`src/ui/views/usuarios/form_usuario_view.py`): modo CRIAR encadeia Nome → Login → Senha → Confirmar → `_salvar`; modo EDITAR pula Login disabled e vai Nome → Perfil (Dropdown, fim da cadeia).
  - `FormCategoriaView` (`src/ui/views/cadastros/form_categoria_view.py`): Nome → Descrição (multiline; Enter na multiline insere quebra de linha, fim natural).
  - `FormFornecedorView` (`src/ui/views/cadastros/form_fornecedor_view.py`): Nome → CNPJ → Telefone → Contato → `_salvar` (Observações multiline fora da cadeia).
- `TextField.on_submit` recebe `lambda e, p=próximo: p.focus()` — o default-arg `p=` captura referência defensivamente (evita bug clássico de closure).
- **Solução definitiva adiada (Fase 5+/pós-MVP)**: `ft.KeyboardListener` envolvendo o card do form, captura manual de Tab e `field.focus()` programático. Requer POC porque `KeyDownEvent` em Flet 0.85.1 não expõe `prevent_default()` — risco de flicker em paralelo ao traversal default do Flutter. Documentado em `CLAUDE.md` ("Pegadinhas Flet 0.85.1") e em `ROADMAP.md` ("Melhorias futuras (pós-MVP)" da Fase 2).

- **Categoria (CRUD completo, Passo 1/10)** — primeiro cadastro da Fase 2.
  - Model: `id`, `nome` (`String(100)` UNIQUE), `descricao` (`String(500)` opcional), `ativo` (default `True`), `criado_em`, `atualizado_em` (com `onupdate=func.now()`). Registrado em `src/database/models/__init__.py`.
  - `CategoriaRepository` — CRUD puro (`listar`, `buscar_por_id`, `buscar_por_nome`, `criar`, `atualizar`, `deletar`) seguindo padrão do `UsuarioRepository`.
  - `CategoriaService` — regras: nome obrigatório (após `strip`), nome UNIQUE (`NomeDuplicadoError` em conflito), soft delete via `desativar()` (chama `atualizar` com `ativo=False`), `atualizar` permite manter o próprio nome (só bloqueia conflito real).
  - `ListaCategoriasView` — tabela custom com avatar+nome, descrição truncada (>60 chars com "…"), badge "Ativa/Inativa" (paleta green-100/700 + cinza), ações por linha (editar lápis, toggle bloquear/ativar laranja). Busca local case-insensitive. Toggle "Mostrar inativas" (default OFF). Estado-vazio com ícone `LABEL_OUTLINE` + "Nenhuma categoria encontrada." Linhas inativas com `opacity=0.6`.
  - `FormCategoriaView` — criar/editar via parâmetro `categoria_id`. Nome obrigatório + Descrição (multiline, `max_lines=4`, `max_length=500`, opcional). Switch "Categoria ativa" só no modo EDITAR. Botões via `components.botao_secundario`/`botao_primario`.
  - Dialog de Desativar com botão **laranja** (não vermelho) — Categoria não é destrutivo-irreversível (regra cravada: vermelho reservado para Desativar Usuário, Excluir, Cancelar Venda).
  - 6 testes pytest em 3 classes: `TestCriar` (válido / nome duplicado / nome vazio), `TestAtualizar` (conflito com outra / manter próprio nome), `TestDesativar`. Total geral: 14 passed.
- **Accordion "Cadastros" na sidebar** (emergiu durante Passo 1):
  - `_SUBITENS_CADASTROS` — 8 entradas (Categorias funcional + 7 placeholders aguardando Passos 3-8).
  - `_VIEWS_CADASTROS: frozenset` — usado para destacar item pai quando view-filha está ativa.
  - `_cadastros_expandido: bool` + `_form_categoria_id: int | None` — novo estado de módulo.
  - Helpers: `_toggle_cadastros`, `_build_item_cadastros` (retorna `[pai]` ou `[pai, ...subitens]`), `_build_subitem_cadastros` (estilo menor — ícone 16, texto 13, indent 32), `_build_item_menu_com_trailing` (chevron parametrizável: `>` ou `▾` baseado em `_cadastros_expandido`).
  - **Auto-expansão**: navegar para qualquer view de `_VIEWS_CADASTROS` expande o accordion automaticamente.
  - Visível a TODOS os perfis (Admin, Gerente, Caixa) — decisão cravada na Fase 2 (cadastros são operação diária).
  - Estado resetado no logout.
- **Lista somente-leitura de Unidades de Medida (Passo 2/10)** — `ListaUnidadesMedidaView` sem CRUD.
  - **Decisão arquitetural**: UM continua sendo cadastro fixo conforme cravado na Fase 0. Vê-se mas não se manipula via UI. Documentado no item 2.1 do ROADMAP.
  - Banner cinza informativo permanente no topo: "As unidades de medida são padronizadas pelo sistema. Se houver necessidade de unidade customizada, será disponibilizada em Configurações > Sistema em versão futura." Sinaliza escape válvula planejada (Fase 5+).
  - Tabela com 2 colunas (NOME, SÍMBOLO), 5 linhas seedadas (Grama, Litro, Mililitro, Quilograma, Unidade) ordenadas alfabeticamente por `descricao`. Avatar laranja com inicial + nome + `sigla` em coluna própria. Zebra striping. Rodapé "Total: 5 unidades".
  - Acesso a dados via `get_session` direto (sem `Service` nem `Repository` próprios — não há regra de negócio para encapsular).
- **Roteamento estendido**:
  - `_navegar(page, nova_view, form_id=None)` aceita `form_id` genérico (roteia para `_form_usuario_id` ou `_form_categoria_id` conforme `nova_view`).
  - 3 ramos novos em `_build_conteudo`: `cadastros_categorias_lista`, `cadastros_categorias_form`, `cadastros_unidades_lista`.

### Changed

- `_ITENS_MENU` em `src/ui/app.py`: item "Cadastros" hardcoded **removido** (agora tratado fora do loop padrão pela função `_build_item_cadastros`, que constrói item pai + subitens conforme `_cadastros_expandido`).
- `_build_item_menu`: removida lógica especial de chevron para "Cadastros" (agora é responsabilidade do `_build_item_menu_com_trailing`).
- `ROADMAP.md`: 12 decisões da Fase 2 cravadas (`9e9f323`); Decisão 1 sobre UM revertida (`c9bd051`) — UM volta a ser cadastro fixo, com item 2.1 documentando razões. Parágrafo final de "escape válvula planejada" adicionado na 2.1 (`5fc4358`).

---

## [0.2.0] - 2026-05-22 — Fase 1: Autenticação

### Added

#### Camada de autenticação e sessão

- `UsuarioRepository` e `PerfilRepository` (CRUD padrão + `buscar_por_login`/`buscar_por_nome`/`listar_ativos`).
- 6 subclasses de `RanggoError`: `AutenticacaoError` (com `LoginInvalidoError`, `UsuarioInativoError`, `PermissaoNegadaError`) e `ValidacaoError` (com `NomeDuplicadoError`, `SenhaFracaError`).
- `AuthService` com bcrypt: `criar_hash` (política ≥6 chars), `verificar_senha` (timing-attack resistant via `bcrypt.checkpw`), `autenticar` (mensagem genérica pra evitar enumeração de logins).
- `src/services/sessao.py` — singleton em memória do usuário logado (`iniciar/encerrar/usuario_atual/esta_logado/requer_perfil`), thread-safe via `threading.Lock`.
- Seed expandido: 3 permissões iniciais (`cadastrar_usuario`, `acessar_relatorios`, `aplicar_desconto`) + amarrações (Admin=todas, Gerente=2, Caixa=0) + usuário Admin (`admin`/`admin123`, hash via `AuthService`). Idempotente.

#### UI da autenticação

- `LoginView` fiel a `prototipos/01-login.png` (50/50 preto/branco, formulário 400px, erro inline em vermelho, foco automático, Enter submete, callback `on_login_success` agnóstico).
- Roteamento Login ↔ Shell em `src/ui/app.py` via `_renderizar(page)` baseado em `sessao.esta_logado()`.
- Sidebar mostra usuário real da sessão: avatar circular laranja com inicial do nome + nome completo + perfil. Eager-load de `perfil` via `joinedload` em `buscar_por_login` evita `DetachedInstanceError`.
- Botão "Fechar Caixa" da sidebar funciona como logout (placeholder — vira fechamento real de caixa na Fase 3).

#### CRUD de Usuários

- `UsuarioService` com regras de negócio: validação de login único, senha mínima 6 chars, perfil válido; soft delete (`ativo=False`); guarda de **auto-desativação** (usuário não pode desativar a própria conta); guarda do **último Admin ativo** (não deixa sistema sem admin); `trocar_senha` via `AuthService.criar_hash`.
- `ListaUsuariosView` — tabela custom com avatar+nome, login, perfil, badge de status (verde "Ativo" / cinza "Inativo"), 3 ações por linha (editar, trocar senha, ativar/desativar). Busca local case-insensitive em nome/login e toggle "Mostrar inativos". Linha de usuário inativo com `opacity=0.6`.
- `FormUsuarioView` — mesma view atende criar e editar (modo via parâmetro `usuario_id`). No modo CRIAR: Senha + Confirmar Senha lado a lado. No modo EDITAR: sem senha, Switch "Usuário ativo" presente, login `disabled` (chave histórica). Guarda visual de auto-desativação: Switch `disabled` com tooltip se editando o próprio admin logado.
- Modal "Alterar Senha" inline na lista — box informativo do usuário alvo + 2 campos password com `can_reveal_password` + helper text "≥6 caracteres" + SnackBar verde de sucesso.
- Item "Usuários" da sidebar visível SÓ pra perfil Admin (filtragem em `_build_sidebar`).
- Roteamento interno no shell: estado global `_view_atual` + `_form_usuario_id` controla área central. `_navegar(page, view, id)` atualiza estado e re-renderiza. Estado resetado em logout (sempre volta pra Dashboard).

#### Bônus arquitetural emergido durante a fase

- `src/ui/components.py` — camada de componentes UI padronizados:
  - `topbar(titulo, acao_direita?)` — header consistente do shell (branco, border-bottom, 80px, padding 32/16, título 28px). **Regra obrigatória**: toda view do shell renderiza como primeiro elemento do Column raiz.
  - `card_form(campos, botoes, largura=800)` — container centralizado de formulário (sem título — título é do topbar). Column interna com `horizontal_alignment=STRETCH` (campos preenchem 100% da largura).
  - `botao_primario` / `botao_secundario` / `botao_perigo` / `botao_sucesso` — factory de botões padronizados (mesma forma, varia só cor).
  - `dialog_confirmacao(...)` — Dialog modal com fundo branco puro (mata tonalização Material 3) + botões via componentes (`_botao_por_cor` despacha conforme `cor_botao_confirmar`).
  - `snackbar_erro` / `snackbar_sucesso` — feedback via `page.show_dialog`.
  - `campo_linha_dupla(esquerda, direita)` — Row 50/50 com `expand=1` em ambos.
  - `cabecalho_pagina` [DEPRECATED] — alias temporário de `topbar`.

#### Protótipos

- `prototipos/08-listagem-usuarios.png` (Stitch) — referência da lista.
- `prototipos/09-formulario-usuario.png` (Stitch) — referência do form criar/editar.
- `prototipos/10-modal-trocar-senha.png` (Stitch) — referência do modal "Alterar Senha".

#### Documentação

- `tests/teste_manual_fase1.md` — roteiro de 20 testes E2E manuais (5 blocos: autenticação básica, sidebar+sessão, CRUD, troca de perfil, robustez). ~15 min de execução.
- `CLAUDE.md` ganhou seção "Componentes UI padronizados — REGRA OBRIGATÓRIA" com 8 regras absolutas cravadas (topbar consistente, modais branco puro, cores semânticas de botões, pares de botões mesmo componente, TextField expand=True, forms centralizados horizontal, hierarquia topbar vs card_form, lista vs form vs dashboard) + 4 pegadinhas Flet 0.85.1 documentadas (Material 3 tonalização, API SnackBar, `can_reveal_password` width, `Column` default CENTER) + razão filosófica.
- Tabela de migrations Flet 0.85.1 no CLAUDE.md ganhou `Padding/Border/Alignment` como classes (não módulos).

### Changed

- Sidebar rodapé: mock "Usuário Padrão / Sem login" substituído por dados reais da sessão (avatar circular laranja com inicial do `usuario.nome`).
- Botão "Fechar Caixa" da sidebar virou handler real (dialog de confirmação + logout + volta pra Login), deixando de ser placeholder visual.
- `_build_topbar` antigo (64px, hardcoded com bell + Nova Venda) removido de `app.py`. Substituído por `components.topbar` (80px, parametrizada, sem bell).
- `_ITENS_MENU` de `app.py` ganhou `view_id` por item (3-tupla) — itens "vivos" (`Dashboard`, `Usuários`) têm view_id; placeholders das fases futuras têm `None` e ficam clicáveis sem efeito.
- Lambdas no loop de construção do sidebar capturam `view_id` via default-arg para evitar bug clássico de closure de loop.

### Fixed

- `DetachedInstanceError` no acesso a `usuario.perfil.nome` na sidebar pós-login. **Causa**: `LoginView._tentar_login` faz `with get_session() as session: auth.autenticar(...)` — o objeto `Usuario` retornado fica detached quando a session fecha. **Solução**: eager-load do relationship `perfil` via `joinedload(Usuario.perfil)` em `UsuarioRepository.buscar_por_login` (único caller que entrega `Usuario` destinado a viver fora da session ativa).
- API SnackBar do Flet 0.85.1: `page.snack_bar = sb; sb.open = True; page.update()` **não existe** nesta versão (atributo `snack_bar` ausente em `Page`). `SnackBar` herda de `DialogControl` — uso correto: `page.show_dialog(ft.SnackBar(...))`. Documentado no `CLAUDE.md` e centralizado em `components.snackbar_erro`/`snackbar_sucesso`.
- Material 3 do Flet tonalizava AlertDialogs com fundo rose/peach claro quando `bgcolor` não era explicitamente setado. **Solução**: forçar `bgcolor=COR_TERCIARIA` em todos os dialogs (centralizado em `components.dialog_confirmacao`).
- Material 3 tonalizava TextFields (fill claro) quando `filled` não era explicitamente `False`. **Solução**: forçar `filled=False` + `bgcolor=COR_TERCIARIA` + bordas explícitas (`border_color=COR_CINZA_200`, `focused_border_color=COR_PRIMARIA`) em todos os campos de form.
- Campos do form ocupavam só ~50% da largura do card. **Causa**: `Column` default tem `horizontal_alignment=CENTER`, não `STRETCH`. `expand=True` em filho de Column é main-axis (vertical), não cross-axis (horizontal). **Solução**: setar `horizontal_alignment=ft.CrossAxisAlignment.STRETCH` na Column interna do card.
- Cores semânticas de botões em dialogs: padrão é **laranja** (`COR_PRIMARIA`) para ações neutras/positivas (Confirmar, Salvar, Ativar, **Fechar Caixa** — só logout); **vermelho** (`COR_ERRO`) é reservado a ações destrutivas irreversíveis (Desativar, Excluir); **verde** (`COR_SUCESSO`) é reservado para finalizar transação no PDV (Fase 3). Antes "Ativar usuário" usava verde e "Fechar Caixa" usava vermelho — corrigido.

### Technical

- ~13 commits durante a Fase 1 (do commit `a45591a` ao `3348dc1`).
- 10 protótipos no Google Stitch versionados (`01-login` até `10-modal-trocar-senha`).

---

## [0.1.x] - 2026-05-20 — Notas operacionais (rebrand + shutdown)

### Fixed

- **Shutdown limpo robusto** (bug "Working..." na 2ª execução). Versão final após 4 iterações:
  - **Causa raiz**: Flet 0.85.1 cria `flet.exe` netos que se desvinculam do parent Python, ficando como top-level invisíveis a `psutil.Process.children(recursive=True)`. Acumulam como zumbis e bloqueiam a próxima execução em "Working...".
  - **Iterações descartadas**: (1) só `engine.dispose() + page.window.destroy() + os._exit(0)` com `prevent_close=False` — handler nunca recebia CLOSE porque o X fechava a janela direto. (2) `prevent_close=True` sem matar `flet.exe` — handler rodava mas `flet.exe` órfão acumulava. (3) `psutil.children(recursive=True).kill()` — pegava só 1 processo por ciclo enquanto o sistema acumulava vários zumbis. (4) `page.window.destroy()` chamado sincronamente — é coroutine `async` em 0.85.1, gera `RuntimeWarning: coroutine 'Window.destroy' was never awaited` e não tem efeito real.
  - **Solução final**: `page.window.prevent_close = True` + handler `_on_window_event` que faz `engine.dispose()` → kill global de TODOS os `flet.exe` via `psutil.process_iter(["name"])` → `os._exit(0)`. **Sem** `page.window.destroy()` — matar o `flet.exe` (que É o renderer Flutter) já fecha a janela.
  - **Rede de segurança**: `atexit.register(_cleanup_on_exit)` em `main.py` repete a mesma lógica (dispose + kill global) para cobrir saídas que não passam pelo handler (exceção no startup, Ctrl+C).
  - **Pegadinha de ambiente**: o projeto tem 2 venvs (`.venv` e `.venv-1`); `psutil` precisa estar em ambas, senão o handler quebra silenciosamente com `ModuleNotFoundError` em runtime.
  - **Validação**: 5 ciclos consecutivos `python main.py` → fechar pelo X → relançar sem espera. Todos abrem em <3s, `Get-Process -Name flet` retorna vazio entre ciclos.

- **Maximize confiável no boot**:
  - **Causa**: `page.window.maximized = True` aplicado ANTES do primeiro `page.update()` é inconfiável no Flet 0.85.1 — ora abre a janela default com "Working..." pendurado (usuário tem que maximizar à mão), ora abre ocupando até a área da taskbar do Windows (cortando o rodapé do conteúdo).
  - **Tentativa descartada**: forçar `width`/`height` via `ctypes.windll.user32.GetSystemMetrics` — `SM_CXSCREEN`/`SM_CYSCREEN` retornam a tela inteira incluindo a taskbar, então o rodapé continuava cortado.
  - **Solução**: setar dimensões iniciais conservadoras (1280×720), executar `_renderizar(page)`, e SÓ ENTÃO aplicar `page.window.maximized = True` + `page.update()`. O Flutter recalcula a área útil corretamente após o primeiro render.

### Added

- `psutil==7.2.2` em `requirements.txt` — necessário para o kill global de `flet.exe` no shutdown e no `atexit`.
- `ROADMAP.md` criado como fonte única de futuro estratégico do projeto. Documenta as 6 fases com objetivo de negócio, escopo, decisões cravadas, decisões em aberto, critérios de "pronto" e débitos previstos.
- **Documentação de Caixa Operacional** (§4.7): regras de abertura/fechamento, vinculação `vendas.caixa_id` na finalização, sangria, bloqueio de troca de operador com exceção Admin, sem fiado, cancelamento por Admin com motivo, controle de troco, quebra de caixa com observação obrigatória.
- **Documentação de Comissão de garçom** (§4.8): débito técnico Fase 6+, provisão `comandas.garcom_id` nullable desde Fase 4.
- Modelo de dados expandido: tabelas `caixas` e `movimentacao_caixa`. Campos novos em `vendas` (caixa_id, valor_pago, troco, status expandido, motivo_cancelamento, finalizada_em) e `comandas` (garcom_id).
- Roadmap atualizado: Fase 3 expandida (Caixa); Fase 5 expandida (segurança); nova Fase 6 (pós-MVP).
- Glossário atualizado com 6 termos.

### Changed

- **Rebrand do projeto**: "Oui Chef" → "Ranggo". Toda documentação, código, assets e nomes técnicos atualizados. Identidade visual (cores, tipografia, layout) mantida.
- Logo SVG real adicionada em `assets/logo/logo.svg` (substituindo placeholder `ft.Icons.RESTAURANT`).
- Ícone da janela configurado via `assets/logo/logo.ico`.
- Exceção raiz renomeada: `OuiChefError` → `RanggoError` (em `src/utils/exceptions.py`).
- Banco de dados: caminho atualizado para `data/ranggo.db` (banco antigo `data/ouichef.db` fica órfão; seed é idempotente e recria o estado em qualquer banco vazio).
- Pasta-raiz do projeto renomeada de `oui_cheff/` para `ranggo/`.

### Changed (lição operacional do rebrand)

- `CLAUDE.md`: nova subseção **"Flet — processos zumbis em debug"** documentando que interromper o Python parent (Ctrl+C, kill abrupto) sem fechar a janela pelo X deixa o cliente Flutter (`flet.exe`) vivo. Múltiplos zumbis causam travamento no splash "Working...". Inclui comandos PowerShell de diagnóstico (`Get-Process flet,python`) e limpeza (`Stop-Process -Name flet -Force`). Descoberto durante smoke tests iterativos do rebrand: o sintoma parecia bug de código mas era subprocesso órfão.

### Changed (ponte documental Fase 0 → Fase 1)

- `CLAUDE.md`: nova subseção **"Flet 0.85.1 — API atual"** dentro de "Padrões de código", com tabela das 6 migrações descobertas no smoke test da Fase 0 (`ft.app` → `ft.run`, `Icon(name=)` → `Icon(icon=)`, `ElevatedButton(text=)` → `ElevatedButton(content=)`, `padding/border/alignment` viraram classes em vez de módulos, ícones/cores em maiúsculas).
- `CLAUDE.md`: tipo de ícone documentado como `ft.IconData` (IntEnum), não `str`.
- `CLAUDE.md`: recomendação de validar API via Context7 + probe REPL antes de codar qualquer view nova.

---

## [0.1.0] - 2026-05-20 — Fase 0: Fundação

### Added

#### Planejamento e documentação

- Documentação inicial do projeto: `PROJETO.md`, `CLAUDE.md`, `CHANGELOG.md`.
- Definição de stack: Python 3.11+, Flet, SQLAlchemy 2.x, SQLite, python-escpos, bcrypt.
- Roadmap dividido em 6 fases (Fundação, Autenticação, Cadastros, Venda Balcão, Comandas/Mesas, Delivery+Relatórios+NFC-e).
- Modelo de dados conceitual com distinção entre Produto, Insumo e Prato (via ficha técnica).

#### Identidade visual

- Tipografia definida: Inter (Regular 400, Medium 500, SemiBold 600, Bold 700) com tamanhos padronizados.
- Paleta de cores completa: primária #FF6600, secundária #0D0D0D, terciária #FFFFFF + funcionais (sucesso #16A34A, alerta #F59E0B, erro #DC2626, info #2563EB) + cinzas + estados.
- Padrões de espaçamento e forma: border-radius (8px inputs/botões, 12px cards, 16px modais), alturas de componentes, sidebar 240px, sem sombras pesadas.
- Logotipo definido: ícone de talheres cruzados (garfo + colher) em laranja primária + wordmark "Oui Chef" em Inter Bold.

#### Protótipos

- Prompts de prototipagem para Google Stitch (7 telas principais): Login, Dashboard, Listagem de Cadastro, Formulário de Cadastro, Ficha Técnica, PDV/Venda Balcão, Modal de Checkout.
- Convenção de pasta `prototipos/` como fonte da verdade visual do projeto.
- Orientação para telas sem protótipo dedicado: derivar dos protótipos existentes mantendo paleta, fonte e componentes padronizados.
- Protótipos gerados, revisados e aprovados:
  - `01-login.png` — tela de login com layout 50/50.
  - `02-dashboard.png` — dashboard com métricas, gráficos e alertas de estoque (regerado com labels em PT-BR e pratos brasileiros típicos no Top 5).
  - `03-listagem-cadastro.png` — listagem genérica com filtros e paginação.
  - `04-formulario-cadastro.png` — formulário genérico em seções.
  - `05-ficha-tecnica.png` — ficha técnica com análise financeira em tempo real.
  - `06-pdv.png` — PDV em 3 colunas (categorias, produtos, comanda).
  - `07-modal-checkout.png` — modal de finalização de venda com formas de pagamento.

#### Decisões de domínio

- **Pratos não têm estoque próprio.** Em listagens, exibem "Ilimitado". O controle real é feito via insumos da ficha técnica (baixa proporcional à quantidade vendida).
- **Numeração sequencial** independente para Comandas (`comandas.numero`) e Vendas (`vendas.numero`), visível no PDV, impressão e relatórios.
- **Desconto manual** suportado na venda, com permissão específica (`aplicar_desconto`) e auditoria.
- **Valores monetários** persistidos como `Numeric(10, 2)` no banco e manipulados como `decimal.Decimal` no código (proibido uso de `float`).

#### Estrutura técnica

- `requirements.txt` com versões fixadas: `flet==0.85.1`, `SQLAlchemy==2.0.49`, `bcrypt==4.3.0`, `python-escpos==3.1`.
- `.gitignore` cobrindo Python, venv, SQLite (com WAL/SHM), Flet build, IDEs, OSes e caches.
- `config.py` na raiz com `DB_PATH`, configs de impressora térmica, dados de empresa, numeração sequencial inicial e `SQL_ECHO`.
- Estrutura de pastas `src/{database,repositories,services,ui,utils}/` + `tests/` + `data/` (versionada via `.gitkeep`).

#### Camada de dados

- `src/database/models/base.py`: `Base(DeclarativeBase)` com `MetaData` configurada com `naming_convention` oficial (pk/fk/uq/ck/ix) — constraints recebem nomes determinísticos.
- `__repr__` herdado na `Base` que itera colunas mapeadas; `__repr_exclude__` mascara campos sensíveis como `<oculto>`.
- Models da Fase 0: `Usuario`, `Perfil`, `Permissao`, `UnidadeMedida` + tabela de associação `perfil_permissoes` (Core `Table` com `ON DELETE CASCADE`).
- `src/database/connection.py`: engine SQLite com `StaticPool`, `check_same_thread=False`, listener `PRAGMA foreign_keys=ON` em cada conexão, `SessionLocal` com `expire_on_commit=False`, context manager `get_session()` (commit/rollback/close) e `init_db()` idempotente.
- `src/database/seed.py`: `popular_dados_iniciais()` idempotente — insere apenas registros faltantes; preserva customizações em linhas já existentes. Seeda 5 unidades de medida (UN, KG, G, L, ML) e 3 perfis (Admin, Gerente, Caixa).

#### Camada de UI

- `src/ui/theme.py`: fonte única de verdade visual no código, espelhando exatamente `PROJETO.md §3`. Constantes de cor, tipografia (família, pesos, tamanhos) e espaçamento (border-radius, alturas, paddings, sidebar). Função `build_flet_theme()` retorna `ft.Theme` com `font_family="Inter"`, `color_scheme_seed=COR_PRIMARIA`, `use_material3=True`, `visual_density=COMFORTABLE`.
- `src/ui/app.py`: `main(page)` que aplica tema, configura janela (1280×720 mínimo, maximizada) e monta o shell — sidebar 240px preta com logo + 9 itens de menu (Dashboard ativo) + rodapé com user mockado e botão "Finalizar Turno"; topbar 64px branca com título e botão "+ Nova Venda"; área de conteúdo cinza com card central "Fundação OK".
- Tipo correto adotado para ícones: `ft.IconData` (não `str`) — `ft.Icons.X` retorna IntEnum.
- `src/utils/exceptions.py`: hierarquia raiz `OuiChefError(Exception)` + roteiro comentado das subclasses por fase futura.

#### Bootstrap (último passo)

- `main.py` na raiz como entry point: orquestra `init_db()` → `popular_dados_iniciais()` → `ft.app(target=...)`.
- Wrapper `_ui_main_com_assets(page)` que registra fontes Inter via `page.fonts` antes da UI montar.
- Pasta `assets/fonts/` versionada com Inter VariableFont (regular + itálico, SIL OFL).
- Tratamento de erro fail-fast no startup: qualquer falha em `init_db`/`seed` aborta com `sys.exit(1)` e imprime traceback.

### Changed

- `CLAUDE.md`: regra documentada na seção SQLAlchemy 2.x — SQL puro em `session.execute()` exige `sqlalchemy.text()`. Strings cruas não são mais aceitas no 2.0+.

---

## Modelo para próximas entradas

<!--
## [0.1.0] - AAAA-MM-DD
### Added
- Descrição clara da funcionalidade no infinitivo ou particípio.

### Changed
- O que mudou e por quê.

### Fixed
- Bug X causava Y; corrigido ajustando Z.
-->
