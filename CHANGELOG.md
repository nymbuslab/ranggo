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

### Fixed
- Bug do "Working..." na segunda execução: resolvido na raiz com handler de `page.window.on_event` (CLOSE) chamando `engine.dispose()` + `page.window.destroy()` + `os._exit(0)`, mais `atexit.register(engine.dispose)` em `main.py` como rede de segurança. Substitui a regra antiga de cleanup manual de `flet.exe` no `CLAUDE.md`. Validado em 5 ciclos consecutivos sem espera (média de 1.21s por janela vs ~5-10s antes).

### Added
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
