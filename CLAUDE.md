# CLAUDE.md — Instruções para o Claude Code

> Este arquivo é lido automaticamente pelo Claude Code em toda sessão dentro desta pasta. Define padrões técnicos, ferramentas permitidas e o que **NÃO** fazer.

---

## Contexto rápido

Este é o **Ranggo**, sistema de PDV para restaurante, single-machine, Windows.

**Leitura obrigatória antes de qualquer alteração:**
- `PROJETO.md` (regras de negócio e identidade visual)
- `CHANGELOG.md` (histórico recente, pra entender o que acabou de ser feito)
- Imagens em `prototipos/` quando a tarefa envolver UI

---

## Stack OBRIGATÓRIA

- **Python 3.11+**
- **Flet** (UI) — não trocar por Tkinter, PyQt, Kivy, etc.
- **SQLAlchemy 2.x** (estilo novo, com `Mapped[...]` e `mapped_column`). **Não** usar o estilo antigo (`Column(...)` direto no atributo de classe sem `Mapped`).
- **SQLite** via `sqlite3` (não usar MySQL, PostgreSQL, etc.).
- **bcrypt** para hash de senha.
- **python-escpos** para impressora térmica.

Bibliotecas adicionais só podem ser introduzidas com confirmação do usuário.

---

## Estrutura de pastas (NÃO violar)

```
oui-chef/
├── PROJETO.md
├── CLAUDE.md
├── CHANGELOG.md
├── requirements.txt
├── main.py
├── config.py
├── prototipos/                  # PNGs das telas (fonte da verdade visual)
├── data/                        # banco em runtime, NÃO versionar conteúdo
├── src/
│   ├── database/
│   │   ├── connection.py
│   │   ├── models/              # 1 arquivo por entidade
│   │   └── seed.py
│   ├── repositories/            # acesso a dados, 1 por entidade
│   ├── services/                # regras de negócio
│   ├── ui/
│   │   ├── app.py
│   │   ├── components/          # botões, inputs, cards reutilizáveis
│   │   ├── views/
│   │   └── theme.py             # cores, fontes, dimensões (espelha PROJETO.md §3)
│   └── utils/
└── tests/
```

**Regra:** view nunca acessa banco direto. Sempre passa por `service`, que usa `repository`.

```
view → service → repository → model
```

---

## Padrões visuais (UI)

### Fonte da verdade

A identidade visual está **inteiramente definida** em `PROJETO.md §3` (Identidade Visual). Cores, fontes, tamanhos, paddings, border-radius — tudo lá.

O arquivo `src/ui/theme.py` deve **espelhar exatamente** o que está em `PROJETO.md §3`. Se houver divergência, o `PROJETO.md` é a fonte da verdade — atualizar o `theme.py`, nunca o contrário.

### Protótipos como referência

Quando for implementar uma tela, **primeiro abrir o protótipo correspondente** em `prototipos/`:

| Tela | Protótipo |
|---|---|
| Login | `prototipos/01-login.png` |
| Dashboard / Home | `prototipos/02-dashboard.png` |
| Listagem de cadastro (genérica) | `prototipos/03-listagem-cadastro.png` |
| Formulário de cadastro (genérico) | `prototipos/04-formulario-cadastro.png` |
| Ficha Técnica do Prato | `prototipos/05-ficha-tecnica.png` |
| PDV / Venda Balcão | `prototipos/06-pdv.png` |
| Modal de Checkout | `prototipos/07-modal-checkout.png` |

### Telas SEM protótipo

Muitas telas do sistema **não terão protótipo dedicado** (ex: cadastro de Mesa, gestão de Comanda, tela de Delivery, telas de Relatório, modais de confirmação, telas de Configuração, gestão de Usuários e Perfis). Para essas:

1. **Identificar o protótipo mais próximo** em estrutura. Exemplo: cadastro de Cliente segue `04-formulario-cadastro.png`. Listagem de Mesas segue `03-listagem-cadastro.png`. Tela de Delivery deriva do PDV (`06-pdv.png`).
2. **Reusar componentes** já criados (botões, inputs, cards, tabelas) — não inventar variantes novas.
3. **Respeitar rigorosamente**:
   - Paleta de cores definida em `PROJETO.md §3.2` (nenhuma cor fora dessa lista).
   - Fonte Inter com os pesos e tamanhos de `PROJETO.md §3.1`.
   - Espaçamento, border-radius e alturas de `PROJETO.md §3.3`.
4. **Estrutura padrão de tela interna do sistema**: sidebar preta 240px à esquerda + topbar 64px com título + área de conteúdo cinza #F5F5F5 com cards brancos border-radius 12px.
5. **Em caso de dúvida sobre layout**, perguntar ao usuário antes de codar. Nunca improvisar uma direção visual nova.

### O que NÃO fazer na UI

- ❌ Hardcodar cor em view — sempre via `theme.py`.
- ❌ Usar fontes diferentes de Inter.
- ❌ Introduzir cores fora da paleta (ex: roxo, rosa).
- ❌ Usar emojis como ícones em produção — usar `flet.Icons` (ex: `ft.Icons.SHOPPING_CART`).
- ❌ Aplicar sombras pesadas. Elevação é dada por borda cinza ou sombra muito sutil.
- ❌ Criar tela "diferente" porque parece mais bonito — consistência > criatividade.
- ❌ Usar textos em inglês na interface. Tudo em PT-BR.

---

## Padrões de código

### Geral
- **Sempre** usar type hints (parâmetros e retorno).
- **Sempre** usar docstrings em funções públicas (estilo Google).
- Nomes em **português** para entidades de domínio (Cliente, Venda, Prato). Nomes técnicos em **inglês** (repository, service, get_by_id).
- Imports organizados: stdlib → terceiros → projeto. Linha em branco entre grupos.
- Não usar `from x import *`.
- Strings: aspas duplas por padrão.
- **Valores monetários**: usar `decimal.Decimal`, nunca `float`. Persistir como `Numeric(10, 2)` no SQLAlchemy.

### SQLAlchemy 2.x (estilo novo)

```python
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import String, Integer, ForeignKey

class Base(DeclarativeBase):
    pass

class Categoria(Base):
    __tablename__ = "categorias"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
```

**SQL puro em `session.execute()` deve ser embrulhado em `sqlalchemy.text()`.** O SQLAlchemy 2.0+ não aceita mais strings cruas — passar uma string direto levanta `ArgumentError`. Exemplo:

```python
from sqlalchemy import text
session.execute(text("PRAGMA foreign_keys"))
```

Para queries ORM normais, continue usando `select(Model)` — só raw SQL precisa do `text()`.

### Flet 0.85.1 — API atual (NÃO usar padrões antigos)

A documentação espalhada na web (e até parte do Context7) ainda mostra exemplos com a API antiga do Flet. Estas migrações foram descobertas no smoke test da Fase 0 ao quebrar em runtime — toda view nova **deve** usar a coluna "Atual":

| Antigo (NÃO usar) | Atual (USAR) | Contexto |
|---|---|---|
| `ft.app(target=...)` | `ft.run(main=...)` | Entry point do app (`ft.app` deprecada desde 0.80.0) |
| `ft.Icon(name=...)` | `ft.Icon(icon=...)` | Parâmetro do widget `Icon` |
| `ft.ElevatedButton(text="X")` | `ft.ElevatedButton(content="X")` | Conteúdo do botão (vale para todos os botões: `FilledButton`, `OutlinedButton`, `TextButton`, etc.) |
| `ft.padding.symmetric(...)` / `ft.padding.only(...)` / `ft.padding.all(...)` | `ft.Padding.symmetric(...)` / `ft.Padding.only(...)` / `ft.Padding.all(...)` | `ft.Padding` agora é **classe** com classmethods, não módulo de funções soltas |
| `ft.border.only(...)` / `ft.border.all(...)` / `ft.border.symmetric(...)` | `ft.Border.only(...)` / `ft.Border.all(...)` / `ft.Border.symmetric(...)` | `ft.Border` agora é **classe** com classmethods |
| `ft.alignment.center` (e demais minúsculos) | `ft.Alignment.CENTER` (enum em `MAIÚSCULAS`) | Alinhamentos viraram enum |
| `ft.icons.X` (minúsculo) | `ft.Icons.X` (maiúsculo) | Enum padronizado |
| `ft.colors.X` (minúsculo) | `ft.Colors.X` (maiúsculo) | Enum padronizado |

**Tipo de ícone:** o valor de `ft.Icons.X` é `ft.IconData` (IntEnum), **não** `str`. Em assinaturas use `icone: ft.IconData`.

**Antes de codar qualquer view nova:** consultar Context7 com query `"flet 0.85 [widget]"` (ex.: `"flet 0.85 TextField"`, `"flet 0.85 DataTable"`) e validar a API exata via probe direto no REPL da venv, porque mesmo o Context7 pode estar parcialmente desatualizado. Padrão recomendado:

```bash
.\.venv\Scripts\python.exe -c "import flet as ft, inspect; print(list(inspect.signature(ft.TextField).parameters.keys())[:10])"
```

Se uma view quebrar com `TypeError: unexpected keyword argument` ou `AttributeError: module 'flet.X' has no attribute 'Y'`, é quase certo padrão antigo — consultar a tabela acima ou fazer o probe.

### Verificação de API do Flet 0.85.1

Context7 está desatualizado para Flet (indexa até 0.84.0 e ainda mostra padrões antigos como `page.on_window_event` e `page.window_prevent_close`).

**Fonte de verdade**: probe direto na venv com:

```python
import flet as ft
print(dir(ft.Window))            # atributos de page.window
print(dir(ft.WindowEvent))       # campos do evento
print(list(ft.WindowEventType))  # membros do enum
```

Use Context7 como complemento, não como autoridade. Quando houver conflito entre Context7 e probe, probe vence.

### Shutdown limpo (Flet 0.85.1)

O app deve sair imediatamente ao fechar pelo X, sem deixar processo zumbi.

**Implementação obrigatória:**

- `src/ui/app.py`: handler `page.window.on_event` que chama `engine.dispose()` + `page.window.destroy()` + `os._exit(0)`.
- `main.py`: `atexit.register(engine.dispose)` como rede de segurança (cobre caminhos de saída que não passam pelo handler — exceção no startup, kill externo).
- Razão de `os._exit(0)` em vez de `sys.exit(0)`: ao fechar pela X, o `ft.run()` demora ~2s para retornar enquanto o subprocesso Flutter (`flet.exe`) desmonta gracefully. Esse delay segura SQLite locks e portas internas — a próxima execução trava em "Working...". `os._exit(0)` força saída imediata, dispensando o cleanup gradual do Flutter.

**Validação:** 5 ciclos `python main.py` → fechar pelo X → `python main.py` sem espera, todos abrindo em < 3 segundos. Se algum falhar, NÃO declarar resolvido — investigar (talvez seja necessário marcar threads do Flet como daemon, ou outro caminho).

**Não fazer:** `Ctrl+C` no terminal durante debug normal. O handler de `CLOSE` cobre o caminho do `X`; `Ctrl+C` mata o Python parent sem disparar o evento, deixando potencial zumbi do `flet.exe`. O `atexit` em `main.py` reduz o risco mas não elimina.

### Repositórios — assinatura padrão

```python
class CategoriaRepository:
    def __init__(self, session: Session) -> None: ...
    def listar(self) -> list[Categoria]: ...
    def buscar_por_id(self, id: int) -> Categoria | None: ...
    def criar(self, dados: dict) -> Categoria: ...
    def atualizar(self, id: int, dados: dict) -> Categoria: ...
    def deletar(self, id: int) -> None: ...
```

### Services — regras de negócio
- Recebem `Session` no construtor.
- Validam dados ANTES de chamar o repository.
- Levantam exceções de domínio próprias (`EstoqueInsuficienteError`, `LoginInvalidoError`).
- Não conhecem Flet — nunca importam `flet`.

### UI / Flet
- Cada view em um arquivo separado dentro de `src/ui/views/`.
- Componentes reutilizáveis em `src/ui/components/`.
- Cores e fontes vêm de `src/ui/theme.py` — **não** hardcodar cor em view.
- View dispara service e mostra resultado/erro; não contém lógica de negócio.

### Tratamento de erros
- Exceções de domínio em `src/utils/exceptions.py`.
- View captura exceção do service e mostra dialog/snackbar.
- Nunca deixar `except: pass` silencioso.

---

## Regras de domínio importantes (resumo)

Estas são regras que o Claude Code deve **lembrar sempre** ao implementar features:

1. **Pratos não têm estoque próprio.** O `estoque_atual` de um prato não existe na tabela. Em listagens, exibir "Ilimitado". A baixa de estoque ao vender um prato é feita nos **insumos** da ficha técnica (multiplicando a quantidade do insumo pela quantidade do prato vendido).

2. **Numeração sequencial de Comandas e Vendas.** Cada uma tem campo `numero` independente, gerado em ordem crescente. Exibir esse número no PDV (#1244), na impressão e nos relatórios.

3. **Destino de preparo dita a impressão.** Ao finalizar uma venda, agrupar itens por `destino_preparo`:
   - Itens com `cozinha` → ticket pra cozinha.
   - Itens com `bar` → ticket pro bar.
   - Itens com `nenhum` → não imprimir ticket de preparo (entrega direta).
   Comprovante de venda é separado e contém todos os itens.

4. **Desconto.** Aplicado no fechamento da venda. Apenas usuários com permissão `aplicar_desconto` podem usar. O `total` da venda é sempre `subtotal - desconto`. Registrar em `movimentacao_estoque` o motivo "venda" e em logs de auditoria o desconto aplicado e o usuário.

5. **Valores monetários sempre em Decimal**, nunca em float. Operações de cálculo devem usar `decimal.Decimal` ou `quantize()` pra evitar erros de ponto flutuante.

6. **Toda venda finalizada gera movimentação de estoque automaticamente** (saída). Operação atômica em transação — se a baixa falhar (estoque insuficiente), a venda não pode ser registrada.

---

## O que NÃO fazer (geral)

- ❌ Inventar bibliotecas, métodos ou parâmetros. Em dúvida, perguntar.
- ❌ Mudar a stack sem confirmação.
- ❌ Pular camadas (view → repository direto).
- ❌ Hardcodar valores que deveriam estar em `config.py` (caminho do banco, IDs de impressora, etc.).
- ❌ Criar tabelas via SQL puro — usar Models do SQLAlchemy.
- ❌ Commitar o arquivo `data/ranggo.db`.
- ❌ Implementar mais de uma feature por vez sem o usuário pedir.
- ❌ Reescrever código existente "para melhorar" sem ser pedido.
- ❌ Esquecer de atualizar o `CHANGELOG.md` ao concluir uma feature relevante.
- ❌ Usar `float` para dinheiro.

---

## Fluxo de trabalho esperado

1. **Antes de começar uma tarefa:**
   - Ler `PROJETO.md` (seção relevante).
   - Ler os últimos itens do `CHANGELOG.md`.
   - Se for tarefa de UI, abrir o protótipo correspondente em `prototipos/` (ou identificar o protótipo de referência se a tela não tiver um próprio).
2. **Planejar antes de codar**: explicar o que vai fazer, esperar o "ok".
3. **Implementar em pequenos passos**, mostrando o que mudou.
4. **Testar manualmente** ou orientar o usuário a testar.
5. **Atualizar o `CHANGELOG.md`** ao concluir.

---

## Atualização do CHANGELOG.md

Toda implementação relevante deve ser registrada. Padrão **Keep a Changelog**:

- **Added** — funcionalidade nova.
- **Changed** — mudança em funcionalidade existente.
- **Deprecated** — funcionalidade marcada para remoção.
- **Removed** — funcionalidade removida.
- **Fixed** — correção de bug.
- **Security** — correção de segurança.

Toda mudança vai primeiro em `[Unreleased]`. Quando uma fase fecha, vira uma versão (`[0.1.0] - 2026-MM-DD`).

**Exemplo de entrada:**
```markdown
## [Unreleased]
### Added
- Cadastro de categorias (CRUD completo) com validação de nome único.
- Componente reutilizável `DataTableCustom` para listagens.
```

NÃO registrar:
- Pequenos ajustes de formatação.
- Renomeação interna de variáveis.
- Correção de typo em comentário.

---

## Convenções de commit (quando o usuário usar git)

Padrão **Conventional Commits**:

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `refactor:` refatoração sem mudança de comportamento
- `docs:` documentação
- `chore:` build, deps, configuração
- `test:` testes

Escopo opcional entre parênteses: `feat(cadastros): adiciona CRUD de categorias`.

---

## Empacotamento final

- **Não usar PyInstaller direto.** Usar `flet pack main.py --name "Ranggo" --icon assets/logo/logo.ico`.
- Antes de empacotar: rodar o projeto em modo dev, validar, então empacotar.
- O `.exe` final acompanha a pasta `data/` (ou cria no primeiro uso).

---

## Evolução futura: Skill de UI personalizada

Quando o projeto atingir a Fase 2 (vários CRUDs implementados) e os padrões de componentes Flet estiverem maduros, vale criar uma skill personalizada em `.claude/skills/oui-chef-ui/SKILL.md` documentando:

- Como construir um formulário padrão.
- Como construir uma listagem padrão com filtros e paginação.
- Como construir um modal.
- Snippets de Flet para componentes comuns.

Isso vai economizar muito contexto em sessões futuras. Não é necessário pra Fase 0 e Fase 1.

---

## Em caso de dúvida

**SEMPRE perguntar** em vez de assumir. Especialmente quando:
- A tarefa pode ser interpretada de duas formas.
- Falta informação de regra de negócio.
- Surgir necessidade de uma biblioteca nova.
- Houver conflito entre `PROJETO.md` e o pedido atual do usuário.
- A tela a ser implementada não tem protótipo dedicado e não está claro de qual derivar.
