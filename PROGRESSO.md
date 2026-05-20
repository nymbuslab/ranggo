# Progresso do Projeto

> Detalhes de implementação ficam em `CLAUDE.md`. Aqui só etapas: feito / fazendo / a fazer.

---

## Em Andamento

_(nada no momento — Fase 0 fechada em 2026-05-20, aguardando início da Fase 1)_

---

## Próximos Passos

### Fase 1 — Autenticação (P0)

- [ ] (P0) Adicionar bcrypt ao `AuthService` (criação de hash e verificação)
- [ ] (P0) `src/repositories/usuario_repository.py` e `src/repositories/perfil_repository.py`
- [ ] (P0) `src/services/auth_service.py` com login/logout e gestão de sessão em memória
- [ ] (P0) Model `Permissao` populado via seed (códigos `aplicar_desconto`, `cancelar_venda`, `editar_cadastros`, etc.)
- [ ] (P0) Seed do usuário Admin inicial (interativo no primeiro boot ou via constante de config)
- [ ] (P0) Tela de Login (`src/ui/views/login_view.py`) — referência `prototipos/01-login.png`
- [ ] (P0) Sistema de roteamento simples no shell (mostrar login vs. shell autenticado)
- [ ] (P0) Conectar item ativo da sidebar à view ativa
- [ ] (P0) Substituir mock "Usuário Padrão / Sem login" pelo usuário da sessão real

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

### Débitos técnicos da Fase 0 (a tratar antes de fechar Fase 1)

- [ ] Limpeza de warnings de lint Markdown em `CLAUDE.md` e `CHANGELOG.md` (combinada com o usuário)
- [ ] Substituir ícone placeholder `ft.Icons.RESTAURANT` por logo SVG de talheres cruzados em `assets/`

---

## Concluído

### Fase 0 — Fundação (2026-05-20)

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
