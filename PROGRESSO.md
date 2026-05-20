# Progresso do Projeto

> Detalhes de implementação ficam em `CLAUDE.md`. Aqui só etapas: feito / fazendo / a fazer.

---

## Em Andamento

_(nada no momento — Fase 0 (`v0.1.0`) e rebrand Oui Chef → Ranggo (`v0.1.1`) fechados em 2026-05-20, aguardando início da Fase 1)_

---

## Próximos Passos

### Fase 1 — Autenticação (P0)

- [ ] (P0) `src/repositories/usuario_repository.py` e `src/repositories/perfil_repository.py` no padrão `listar/buscar_por_id/criar/atualizar/deletar`
- [ ] (P0) `src/services/auth_service.py` com bcrypt (hash/verify), login/logout e gestão de sessão em memória
- [ ] (P0) Seed do model `Permissao` com códigos iniciais (`aplicar_desconto`, `cancelar_venda`, `editar_cadastros`, etc.) + usuário Admin inicial
- [ ] (P0) Tela de Login (`src/ui/views/login_view.py`) — referência `prototipos/01-login.png`
- [ ] (P0) Roteamento simples no shell (login vs. shell autenticado) + conectar item ativo da sidebar à view ativa
- [ ] (P0) Substituir mock "Usuário Padrão / Sem login" no topbar pelo usuário da sessão real

### Débitos técnicos da Fase 0 (tratar antes de fechar Fase 1)

- [ ] Limpeza de warnings de lint Markdown em `CLAUDE.md` e `CHANGELOG.md`
- [ ] Substituir ícone placeholder `ft.Icons.RESTAURANT` por logo SVG de talheres cruzados em `assets/`

### Fase 2 — Cadastros (P1)

- [ ] (P1) Componentes reutilizáveis: `DataTableCustom`, `FormularioPadrao`, `ModalConfirmacao`
- [ ] (P1) Cadastro de Categorias (CRUD) — referência `prototipos/03-listagem-cadastro.png` + `04-formulario-cadastro.png`
- [ ] (P1) Cadastro de Insumos (CRUD) com controle de estoque
- [ ] (P1) Cadastro de Produtos (CRUD) — itens de revenda direta
- [ ] (P1) Cadastro de Pratos (CRUD) com Ficha Técnica — referência `prototipos/05-ficha-tecnica.png`
- [ ] (P1) Cadastro de Clientes (CRUD)
- [ ] (P1) Cadastro de Fornecedores (CRUD)

### Fase 3 — Venda Balcão (P1)

- [ ] (P1) Tela PDV (`src/ui/views/pdv_view.py`) — referência `prototipos/06-pdv.png`
- [ ] (P1) Modal de Checkout — referência `prototipos/07-modal-checkout.png`
- [ ] (P1) `src/services/venda_service.py` com lógica de baixa de estoque atômica
- [ ] (P1) Impressão de comprovante e tickets de cozinha/bar via python-escpos

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
