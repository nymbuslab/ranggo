# Progresso do Projeto

> **Visão estratégica do projeto (fases, dependências, débitos):** `ROADMAP.md`.
> **Padrões técnicos:** `CLAUDE.md`.
> Aqui só o que está sendo feito agora — próximas 1-3 semanas.

---

## Em Andamento

_Nada em andamento._ Working tree limpo, débitos transversais resolvidos (5 de 6 — só sobra `mypy --strict`, adiado consciente). Aguardando início da **Fase 2 — Cadastros**.

---

## Próximos Passos

### Fase 2 — Cadastros (P1)

- [ ] (P1) Componentes reutilizáveis emergentes: `badge_status`, `linha_tabela`, `selector_data`, etc (adicionar ao `src/ui/components.py` conforme padrões surgem)
- [ ] (P1) Cadastro de Categorias (CRUD) — referência `prototipos/03-listagem-cadastro.png` + `04-formulario-cadastro.png`
- [ ] (P1) Cadastro de Insumos (CRUD) com controle de estoque
- [ ] (P1) Cadastro de Produtos (CRUD) — itens de revenda direta
- [ ] (P1) Cadastro de Pratos (CRUD) com Ficha Técnica — referência `prototipos/05-ficha-tecnica.png`
- [ ] (P1) Cadastro de Clientes (CRUD)
- [ ] (P1) Cadastro de Fornecedores (CRUD)

### Fase 3 — Venda Balcão + Caixa Operacional (P1)

- [ ] (P1) Tela PDV (`src/ui/views/pdv_view.py`) — referência `prototipos/06-pdv.png`
- [ ] (P1) Modal de Checkout — referência `prototipos/07-modal-checkout.png`
- [ ] (P1) `src/services/venda_service.py` com lógica de baixa de estoque atômica (vinculação `vendas.caixa_id` na finalização, status expandido aberta/pendente_pagamento/finalizada/cancelada)
- [ ] (P1) Impressão de comprovante e tickets de cozinha/bar via python-escpos
- [ ] (P1) Models `Caixa` e `MovimentacaoCaixa` + campos novos em `Venda` (caixa_id, valor_pago, troco, status, motivo_cancelamento, finalizada_em) e `Comanda` (garcom_id)
- [ ] (P1) Tela de Abertura de Caixa (valor inicial em dinheiro)
- [ ] (P1) Tela de Fechamento de Caixa (resumo por forma de pagamento + valor real contado + cálculo de divergência + observação obrigatória se quebra — R8)
- [ ] (P1) Tela de Sangria/Suprimento durante o turno com motivo obrigatório (R6)
- [ ] (P1) Bloqueio de troca de operador com caixa aberto (R2) + exceção Admin com fechamento forçado auditado em `caixas.fechamento_admin_id` (R3)
- [ ] (P1) Alerta de pendências (comandas/deliveries em aberto) ao fechar caixa, com confirmação (R1)
- [ ] (P1) Cancelamento de venda finalizada apenas por Admin, com motivo obrigatório e movimentação reversa de estoque (R5)
- [ ] (P1) Controle de troco em vendas em dinheiro: `valor_pago` e `troco` persistidos (R7)
- [ ] (P1) Botão "Fechar Caixa" da sidebar deixa de ser logout simples (placeholder Fase 1) e vira fechamento real de caixa

### Fase 4 — Comandas e Mesas (P2)

- [ ] (P2) Model Mesa e Comanda
- [ ] (P2) Tela de gestão de mesas
- [ ] (P2) Fluxo de comanda (abrir, adicionar itens, fechar)

### Fase 5 — Delivery, Relatórios e NFC-e (P2)

- [ ] (P2) Tela de Delivery derivada do PDV
- [ ] (P2) Relatórios gerenciais (dashboard — referência `prototipos/02-dashboard.png`)
- [ ] (P2) Integração NFC-e via ACBrLibPython

---

## Concluído

### Pós-v0.2.0 — Limpeza de débitos transversais (2026-05-22)

4 commits posteriores à tag `v0.2.0` fechando débitos transversais herdados da Fase 0/1:

- **`af67b44` — `chore(docs)`**: markdownlint zero warnings nos 5 `.md` raiz (criado `.markdownlint.json` + auto-fix + manuais).
- **`15a904f` — `docs`**: comando `markdownlint-cli2` documentado no `CLAUDE.md` (seção "Lint markdown").
- **`ab38786` — `test(usuario)`**: 8 testes pytest do `UsuarioService` cobrindo as 5 regras críticas (login único, senha mínima, perfil válido, auto-desativação, último admin) + `trocar_senha` + `desativar`. Infra em `tests/unit/` (`__init__.py`, `conftest.py` com banco SQLite em memória + fixtures, `pytest.ini`). `pytest==8.3.4` adicionado ao `requirements.txt`.

**Débitos transversais**: 5 de 6 resolvidos (lint MD, logo SVG, ICO multi-res, push remote, pytest). Sobra apenas `mypy --strict` (decisão adiada consciente para Fase 6+). Working tree limpo, pronto para Fase 2.

### Fase 1 — Autenticação (10/10 passos) (2026-05-22)

**Tag:** `v0.2.0`. Total de commits da fase: ~13 (do commit `a45591a` ao `3348dc1`).

- [x] **Passo 1 — repositories** (`d8c1677`): `UsuarioRepository` + `PerfilRepository` com CRUD padrão do CLAUDE.md + métodos `buscar_por_login` (case-sensitive, usado no AuthService), `listar_ativos` (filtra `ativo=True`) e `buscar_por_nome` (resolve `perfil_id` no seed).
- [x] **Passos 2+3 — exceções + AuthService** (`b14f600`): 6 exceções de Fase 1 (`AutenticacaoError` + 3 subs, `ValidacaoError` + 2 subs); `AuthService.criar_hash` (bcrypt + política ≥6 chars), `verificar_senha` (bcrypt.checkpw, timing-attack resistant), `autenticar` (busca → senha → ativo, mensagem genérica para evitar enumeração).
- [x] **Passo 4 — sessão singleton** (`85e4b9f`): `src/services/sessao.py` com `iniciar/encerrar/usuario_atual/esta_logado/requer_perfil`, thread-safe via `threading.Lock`, crítica curta no `requer_perfil` para evitar lazy-load do SQLAlchemy segurando o lock.
- [x] **Passo 5 — seed expandido** (`28c324d`): 3 permissões (`cadastrar_usuario/acessar_relatorios/aplicar_desconto`) + amarrações (Admin=todas, Gerente=2, Caixa=0) + usuário Admin (`admin`/`admin123`, hash via AuthService), tudo idempotente.
- [x] **Passo 6 — LoginView** (`a45591a`): tela fiel a `prototipos/01-login.png` (50/50 preto/branco, formulário 400px), erro inline em vermelho, foco automático, Enter submete, callback `on_login_success` (view agnóstica sobre pós-login). 2 pegadinhas Flet 0.85.1 documentadas no CLAUDE.md (`can_reveal_password` expande largura, `Column(tight=True)` desabilita alignment).
- [x] **Passo 7 — roteamento + bugfix consolidado** (`047c70a`): `main()` virou dispatcher Login↔Shell via `_renderizar(page)`; botão "Fechar Caixa" com `AlertDialog` usando `page.show_dialog/pop_dialog` (API correta do Flet 0.85.1). Diagnóstico exaustivo do bug "Working..." (4 iterações até identificar que `prevent_close=True` é obrigatório + kill global de `flet.exe` via `psutil.process_iter` + remover `page.window.destroy()` async). Maximize confiável aplicando `maximized=True` pós-render. `psutil==7.2.2` adicionado em `requirements.txt` + em `.venv` e `.venv-1`. CLAUDE.md enxugado de 420→384 linhas, CHANGELOG.md ganhou detalhamento técnico das 4 iterações.
- [x] **Passo 8 — sidebar com usuário real** (`d6a037d`): rodapé da sidebar passa a refletir `sessao.usuario_atual().nome` + `perfil.nome` (avatar circular laranja com inicial). Eager-load do `perfil` via `joinedload` em `UsuarioRepository.buscar_por_login` para evitar `DetachedInstanceError` no shell.
- [x] **Passo 9.1 — UsuarioService** (`c3bd7d0`): regras de negócio (login único, senha mínima, perfil válido, soft delete via `ativo=False`, guarda de auto-desativação, guarda do último Admin ativo, `trocar_senha` via `AuthService.criar_hash`). Sanity check com 13 asserts validados.
- [x] **Passo 9.2 — ListaUsuariosView** (`55a9aa6`): tabela custom (avatar+nome, login, perfil, badge status, 3 ações por linha) com busca local case-insensitive em nome/login e toggle "Mostrar inativos". `prototipos/08-listagem-usuarios.png` versionado (`07a9744`) + tree dos `.md` atualizada (`850b93a`).
- [x] **Passo 9.3 — FormUsuarioView + roteamento no shell + components.py** (`3348dc1`): `FormUsuarioView` (modo criar/editar via `usuario_id`), modal "Alterar Senha" inline, roteamento real no shell (`_view_atual` + `_navegar`), item "Usuários" condicional ao perfil Admin. **Bônus arquitetural emergido**: criação de `src/ui/components.py` (camada de componentes UI padronizados — `topbar`, `card_form`, `botao_primario/secundario/perigo/sucesso`, `dialog_confirmacao`, `snackbar_erro/sucesso`, `campo_linha_dupla`) + 8 regras absolutas de design cravadas no CLAUDE.md. Protótipos `09-formulario-usuario.png` e `10-modal-trocar-senha.png` versionados (`04fc285`).
- [x] **Passo 10 — fechamento da Fase 1** (este commit): roteiro de testes E2E manuais em `tests/teste_manual_fase1.md` (20 testes), atualização de `PROGRESSO.md`/`CHANGELOG.md`/`ROADMAP.md`, tag `v0.2.0`.

### Fase 1 — Autenticação (passos 1-7 de 10) (2026-05-20)

_Histórico parcial preservado por referência cronológica. Passos 8-10 acima._

### Rebrand Oui Chef → Ranggo + correção do zumbi Flet (2026-05-20)

**Tag:** `v0.1.1`

- [x] Rebrand completo em 4 commits: docs `.md`, refactor de código+assets, rename físico da pasta (`oui_cheff/` → `ranggo/`, commit `9eb1ded`), docs Flet API migrations
- [x] Logo SVG laranja real adicionada em `assets/logo/` e plugada no shell (`page.window.icon` + `ft.Image` na sidebar)
- [x] Renomeação `OuiChefError` → `RanggoError` em `src/utils/exceptions.py` (classe + roteiro futuro)
- [x] Diagnóstico do bug "Working..." infinito: era processo zumbi `flet.exe` de smoke tests anteriores, não bug de código
- [x] Regra de cleanup de zumbis Flet documentada no `CLAUDE.md` (Stop-Process + diagnóstico via Get-Process)

### Fase 0 — Fundação (2026-05-20)

**Tag:** `v0.1.0`

- [x] Documentação inicial: `PROJETO.md`, `CLAUDE.md`, `CHANGELOG.md`
- [x] Stack definida e fixada: Python 3.12, Flet 0.85.1, SQLAlchemy 2.0.49, bcrypt 4.3.0, python-escpos 3.1
- [x] Roadmap dividido em 6 fases documentado em PROJETO.md
- [x] Modelo de dados conceitual definido (Produto, Insumo, Prato via ficha técnica)
- [x] Identidade visual completa: tipografia Inter, paleta de cores, espaçamentos, border-radius
- [x] Logotipo definido (talheres cruzados em laranja + wordmark Inter Bold)
- [x] 7 protótipos de tela gerados, revisados e aprovados
- [x] Decisões de domínio registradas (estoque via insumos, numeração sequencial, desconto com permissão, Decimal para dinheiro)
- [x] Estrutura de pastas criada (`src/database/`, `src/repositories/`, `src/services/`, `src/ui/`, `src/utils/`, `data/`, `assets/`, `tests/`)
- [x] `requirements.txt` com versões fixadas (`==`)
- [x] `.gitignore` cobrindo Python, venv, SQLite, Flet build, IDEs, OS
- [x] `config.py` com `DB_PATH`, impressora, empresa, numeração inicial e `SQL_ECHO`
- [x] `src/utils/exceptions.py` com `RanggoError` raiz + roteiro futuro
- [x] `src/database/models/base.py` com `Base(DeclarativeBase)`, naming convention oficial e `__repr_exclude__`
- [x] Models Fase 0: `Usuario`, `Perfil`, `Permissao`, `perfil_permissoes` (Core Table com ON DELETE CASCADE), `UnidadeMedida`
- [x] `src/database/connection.py` com `StaticPool`, `check_same_thread=False`, listener `PRAGMA foreign_keys=ON`, `expire_on_commit=False`, `get_session()` e `init_db()` idempotente
- [x] `src/database/seed.py` idempotente: 5 unidades + 3 perfis, preserva customizações
- [x] `src/ui/theme.py` espelhando PROJETO.md §3 (cores, tipografia, dimensões) + `build_flet_theme()` com Material 3
- [x] `src/ui/app.py` com shell visual (sidebar 240px preta + topbar 64px branca + área cinza com card "Fundação OK")
- [x] Fonte Inter VariableFont (regular + itálico, SIL OFL) versionada em `assets/fonts/`
- [x] `main.py` na raiz: orquestra `init_db()` → `popular_dados_iniciais()` → `ft.run(...)` com fail-fast e traceback
- [x] CLAUDE.md atualizado com regra obrigatória do `sqlalchemy.text()` para SQL puro
