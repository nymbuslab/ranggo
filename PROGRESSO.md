# Progresso do Projeto

> **Visão estratégica do projeto (fases, dependências, débitos):** `ROADMAP.md`.
> **Padrões técnicos:** `CLAUDE.md`.
> Aqui só o que está sendo feito agora — próximas 1-3 semanas.

---

## Em Andamento

**Checkpoint salvo em 2026-05-20 12:15**

### Feito nesta sessão
- Higiene do PROGRESSO.md: removidas menções obsoletas ao rename da pasta `oui_cheff/`, checkpoint atualizado com tags `v0.1.0` + `v0.1.1` (commit `1e833cf`).
- Documentação de **Caixa Operacional** (§4.7 com R1–R8), **Comissão de Garçom** débito Fase 6+ (§4.8), modelo de dados expandido (tabelas `caixas` + `movimentacao_caixa`, campos novos em `vendas` e `comandas`), roadmap, glossário (commit `e914b82`).
- **Fix do bug "Working..."** resolvido na raiz: handler `page.window.on_event` (CLOSE) com `engine.dispose()` + `page.window.destroy()` + `os._exit(0)` em `src/ui/app.py`; `atexit.register(engine.dispose)` em `main.py`. Validado em 5 ciclos consecutivos sem espera (média 1.21s vs ~5-10s antes). Regra antiga de cleanup manual removida do `CLAUDE.md` (commit `3e7594d`).
- Criação do **`ROADMAP.md`** como fonte única de futuro estratégico (309 linhas, 6 fases com objetivo/escopo/decisões cravadas/critérios de pronto/débitos). `PROJETO.md §7` enxugado para resumo + link. `CLAUDE.md` ganha `ROADMAP.md` na leitura obrigatória + tabela de divisão de responsabilidade entre `.md`s. `PROGRESSO.md` com nova nota de cabeçalho (commit `487036d`).

### Próximo passo
- **Passo 1 de 10 da Fase 1**: criar `src/repositories/usuario_repository.py` e `src/repositories/perfil_repository.py` no padrão `listar/buscar_por_id/criar/atualizar/deletar` (assinatura do `CLAUDE.md`), com métodos extras `UsuarioRepository.buscar_por_login(login: str)` e `PerfilRepository.buscar_por_nome(nome: str)`. Zero código de UI ou service nesta etapa.

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
