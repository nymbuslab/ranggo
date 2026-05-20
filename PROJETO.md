# Ranggo — Sistema de Vendas para Restaurante

> Documento de referência do projeto. Descreve **o que** o sistema faz e **por quê**. Para padrões técnicos e de código, ver `CLAUDE.md`. Para histórico de implementações, ver `CHANGELOG.md`.

---

## 1. Visão Geral

**Ranggo** é um sistema de PDV (Ponto de Venda) para restaurantes, executado **localmente** em um computador Windows (servidor e cliente na mesma máquina), sem dependência de internet ou nuvem.

Inspirado em sistemas como o **Consumer**, foca em três pilares:

1. **Cadastros** completos (clientes, fornecedores, produtos, insumos, categorias, pratos).
2. **Operação de venda** (balcão, comandas/mesas, delivery).
3. **Relatórios** gerenciais.

### Princípios

- **Local-first**: nada de nuvem na v1. O banco é um arquivo SQLite na máquina.
- **Operação rápida**: o caixa precisa fechar uma venda em poucos cliques.
- **Impressão na cozinha** é parte essencial do fluxo, não um adicional.
- **Controle de estoque automático**: cada venda dá baixa em produtos (revenda) e/ou insumos (matérias-primas via ficha técnica).

---

## 2. Stack Técnica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| UI | Flet (baseado em Flutter) |
| Banco de dados | SQLite (arquivo único) |
| ORM | SQLAlchemy 2.x |
| Hash de senha | bcrypt |
| Impressão térmica | python-escpos (ESC/POS, 48 colunas) |
| Empacotamento | `flet pack` → executável `.exe` |
| NFC-e (Fase 5) | ACBrLibPython |

**Decisões importantes:**

- **SQLite e não MySQL**: ambiente single-machine, zero configuração, arquivo único facilita backup.
- **Flet e não Tkinter/PyQt**: equipe já tem familiaridade com Flutter; visual moderno; produtividade alta.
- **python-escpos e não ACBr para impressão de cozinha**: ACBr é para documentos fiscais. Comanda de cozinha é ESC/POS puro.

---

## 3. Identidade Visual

### 3.1 Tipografia

**Fonte única: Inter** (Google Fonts).

Pesos utilizados:
- **Regular (400)** — corpo de texto, descrições, labels secundários.
- **Medium (500)** — labels de campos, textos de tabela, nomes em listagens.
- **SemiBold (600)** — títulos de seção, valores em destaque, botões.
- **Bold (700)** — títulos principais, valores monetários grandes, métricas do dashboard.

Tamanhos padrão:
- Título principal de tela: **24px / SemiBold**
- Título de seção: **18px / SemiBold**
- Subtítulo / Label: **14px / Medium**
- Corpo de texto: **14px / Regular**
- Texto de apoio / Helper: **12px / Regular**
- Valor monetário em destaque: **28px / Bold**

### 3.2 Paleta de Cores

```
PRIMÁRIA       #FF6600   Laranja Ranggo — CTAs, destaques, ativo
SECUNDÁRIA     #0D0D0D   Preto — sidebar, textos principais
TERCIÁRIA      #FFFFFF   Branco — fundo de conteúdo

FUNCIONAIS
SUCESSO        #16A34A   Verde — venda finalizada, estoque ok, margem saudável
ALERTA         #F59E0B   Amarelo — estoque baixo, comanda atrasada
ERRO           #DC2626   Vermelho — falha, estoque crítico, cancelamento
INFO           #2563EB   Azul — informações neutras

CINZAS
CINZA-100      #F5F5F5   Fundo de área de conteúdo, hover sutil
CINZA-200      #E5E5E5   Bordas, divisores
CINZA-400      #A3A3A3   Textos secundários, placeholders
CINZA-600      #525252   Textos de apoio

ESTADOS
HOVER LARANJA  #E55A00   Laranja escurecido para hover de botão primário
LARANJA SUAVE  #FFF1E6   Fundo de item ativo na sidebar, badges informativos
```

### 3.3 Espaçamento e Forma

- **Border-radius padrão**:
  - Inputs / botões: **8px**
  - Cards: **12px**
  - Modais: **16px**
- **Altura de componentes**:
  - Input padrão: **44px**
  - Botão primário: **48px** (56px em CTAs grandes como "Finalizar Venda")
  - Linha de tabela: **60px**
  - Topbar: **64px**
- **Padding interno padrão** de cards: **24px** (32px em formulários).
- **Sidebar fixa**: **240px** de largura.
- **Sem sombras pesadas** — usar elevação muito sutil ou apenas borda cinza #E5E5E5.

### 3.4 Logotipo

O símbolo do Ranggo é um **ícone de talheres cruzados** (garfo + colher) na cor laranja primária (#FF6600), acompanhado do wordmark "Ranggo" em Inter Bold branco (sobre fundo escuro) ou preto (sobre fundo claro).

### 3.5 Protótipos

Os protótipos foram gerados no **Google Stitch**. Eles ficam em `prototipos/` na raiz do projeto:

```
prototipos/
├── 01-login.png
├── 02-dashboard.png
├── 03-listagem-cadastro.png
├── 04-formulario-cadastro.png
├── 05-ficha-tecnica.png
├── 06-pdv.png
└── 07-modal-checkout.png
```

**Regra fundamental**: quando uma tela ainda não tem protótipo, ela deve ser construída **derivando dos padrões já estabelecidos** nos protótipos existentes e nesta seção de identidade visual. Não inventar paleta, não introduzir fontes novas, não criar tipos de componentes diferentes dos que já existem nas telas prototipadas.

---

## 4. Conceitos de Negócio

### 4.1 Produto vs Insumo vs Prato

Distinção fundamental do sistema:

- **Produto**: item de **revenda**, vendido como veio do fornecedor. Tem estoque próprio em **unidades**.
  *Exemplos: Coca-Cola lata, cerveja Heineken long neck, água mineral, salgadinho de pacote.*

- **Insumo**: **matéria-prima** usada na produção de pratos. Tem estoque em **unidade de medida** (kg, g, L, ml).
  *Exemplos: arroz cru (kg), feijão (kg), óleo (L), carne moída (kg).*

- **Prato**: item **preparado/montado** a partir de insumos. Tem preço de venda. **Não tem estoque próprio** — a baixa acontece nos insumos via **ficha técnica**. Em listagens, o estoque de pratos aparece como **"Ilimitado"**.
  *Exemplo: Marmitex Mista (composta por 0.3kg de arroz, 0.1kg de feijão, 0.2kg de carne, etc.).*

### 4.2 Ficha Técnica

Tabela de ligação entre **prato** e **insumos** com a quantidade de cada insumo necessária para preparar uma unidade do prato.

Permite:
- Cálculo automático de **custo** do prato.
- Baixa automática de estoque dos insumos ao vender.
- Análise de margem (custo vs preço de venda).
- Relatório de "preciso comprar".

### 4.3 Destino de Preparo

Cada produto/prato tem uma flag `destino_preparo`:

- `cozinha` — vai pro ticket impresso na cozinha (ex: marmitex, lanche).
- `bar` — vai pro ticket impresso no bar (ex: drinks preparados).
- `nenhum` — entrega direta, não imprime ticket de preparo (ex: refrigerante de lata, salgadinho).

Ao fechar a venda, o sistema agrupa os itens por destino e imprime um ticket separado para cada um.

### 4.4 Numeração Sequencial

- **Comandas** têm campo `numero` sequencial, visível no PDV e na impressão. Reinicia anualmente (ou nunca, configurável).
- **Vendas** têm campo `numero` sequencial próprio, independente da comanda, usado para identificação no cupom e em relatórios.

### 4.5 Desconto

A venda suporta **desconto manual** aplicado pelo operador (apenas perfis com permissão de desconto). Campo `desconto: Decimal` na tabela `vendas`. O total registrado é sempre `subtotal - desconto`. Auditável via relatórios.

### 4.6 Fluxo de Venda Padrão

1. Operador seleciona itens no PDV (balcão, comanda ou delivery).
2. Operador clica em **Checkout / Finalizar**.
3. Sistema gera **tickets de preparo** (cozinha/bar) e imprime.
4. Operador confirma forma de pagamento (com desconto opcional).
5. Sistema **registra a venda** com número sequencial (status: finalizada).
6. Sistema **dá baixa no estoque** (produtos diretamente; pratos via ficha técnica).
7. Imprime comprovante de venda (opcional).

---

## 5. Módulos do Sistema

### 5.1 Cadastros

- **Usuários e Perfis**: Admin, Gerente, Caixa. Cada perfil tem permissões granulares.
- **Categorias**: agrupamento de produtos/pratos (Bebidas, Pratos Executivos, Sobremesas...).
- **Unidades de Medida**: UN, KG, G, L, ML (cadastro fixo, criado no seed).
- **Produtos**: itens de revenda.
- **Insumos**: matérias-primas.
- **Pratos**: itens preparados.
- **Ficha Técnica**: composição de cada prato.
- **Clientes**: pessoa física, com endereço (para delivery).
- **Fornecedores**: empresas que fornecem produtos/insumos.

### 5.2 Vendas

- **Venda Balcão**: cliente pede, paga e leva. Fluxo mais rápido.
- **Comandas / Mesas**: conta aberta vinculada a uma mesa, identificada por número sequencial. Permite adicionar itens ao longo do tempo, fechar com divisão de conta.
- **Delivery**: vinculado a um cliente cadastrado, com endereço, taxa de entrega e status (pendente, em rota, entregue).

### 5.3 Relatórios (Fase 5)

- Vendas por período.
- Vendas por categoria/prato/produto.
- Produtos/insumos mais vendidos.
- Estoque atual e abaixo do mínimo.
- Faturamento por forma de pagamento.
- Descontos aplicados (auditoria).

---

## 6. Modelo de Dados (visão lógica)

```
usuarios ──┐
           └─→ vendas (operador)
perfis ──→ usuarios
permissoes ──→ perfis (N:N)

categorias ──┐
             ├─→ produtos
             └─→ pratos

unidades_medida ──→ insumos
unidades_medida ──→ produtos (para os que são vendidos a peso)

pratos ──┬─→ ficha_tecnica ←─┬── insumos
         │                    │
         └─→ venda_itens ←────┤
                              │
produtos ─────→ venda_itens ──┘

vendas ──┬─→ venda_itens
         ├─→ cliente (opcional, obrigatório em delivery)
         └─→ comanda (opcional)

mesas ──→ comandas ──→ comanda_itens

movimentacao_estoque ──→ produtos / insumos
                     (registra TODA entrada e saída)
```

### Tabelas principais

| Tabela | Campos-chave |
|---|---|
| `usuarios` | id, nome, login, senha_hash, perfil_id, ativo |
| `perfis` | id, nome (Admin/Gerente/Caixa) |
| `permissoes` | id, codigo, descricao |
| `perfil_permissoes` | perfil_id, permissao_id |
| `categorias` | id, nome, tipo (produto/prato/ambos) |
| `unidades_medida` | id, sigla, descricao |
| `produtos` | id, nome, categoria_id, unidade_id, preco_venda, custo, estoque_atual, estoque_minimo, destino_preparo, ativo |
| `insumos` | id, nome, unidade_id, estoque_atual, estoque_minimo, custo_medio, ativo |
| `pratos` | id, nome, categoria_id, preco_venda, destino_preparo, ativo |
| `ficha_tecnica` | id, prato_id, insumo_id, quantidade |
| `clientes` | id, nome, telefone, cpf, endereco, bairro, cidade, observacoes |
| `fornecedores` | id, razao_social, cnpj, telefone, email, endereco |
| `mesas` | id, numero, capacidade, status |
| `comandas` | id, **numero** (sequencial), mesa_id, cliente_id, status (aberta/fechada), aberta_em, fechada_em, usuario_id |
| `comanda_itens` | id, comanda_id, produto_id/prato_id, quantidade, preco_unitario, observacao |
| `vendas` | id, **numero** (sequencial), tipo (balcao/comanda/delivery), comanda_id, cliente_id, usuario_id, subtotal, **desconto**, total, forma_pagamento, status, criada_em |
| `venda_itens` | id, venda_id, produto_id/prato_id, quantidade, preco_unitario, subtotal |
| `movimentacao_estoque` | id, tipo (entrada/saida), produto_id/insumo_id, quantidade, motivo, venda_id, data, usuario_id |

---

## 7. Roadmap

### Fase 0 — Fundação
Setup do projeto, estrutura de pastas, conexão SQLAlchemy, criação de tabelas, tema Flet (com as cores e fontes definidas em §3), shell da aplicação.

### Fase 1 — Autenticação
Login (baseado em `prototipos/01-login.png`), hash de senha, sessão, CRUD de usuários, perfis e permissões, middleware de acesso.

### Fase 2 — Cadastros
Categorias → Unidades → Produtos → Insumos → Pratos → Ficha Técnica → Clientes → Fornecedores. Listagens baseadas em `prototipos/03-listagem-cadastro.png` e formulários em `prototipos/04-formulario-cadastro.png`. Ficha técnica baseada em `prototipos/05-ficha-tecnica.png`.

### Fase 3 — MVP Venda Balcão
PDV (baseado em `prototipos/06-pdv.png`), carrinho, formas de pagamento (modal em `prototipos/07-modal-checkout.png`), fechamento com numeração sequencial de venda, impressão de tickets de cozinha/bar, baixa de estoque, desconto manual.

### Fase 4 — Comandas e Mesas
Cadastro de mesas, abertura/fechamento de comanda com numeração sequencial, transferência, divisão de conta.

### Fase 5 — Delivery, Relatórios, NFC-e
Fluxo de delivery, relatórios gerenciais, emissão de NFC-e via ACBr.

---

## 8. Configurações do Ambiente

Arquivo `config.py` na raiz centraliza:

```python
DB_PATH = "data/ranggo.db"

# Impressora
IMPRESSORA_TIPO = "usb"          # "usb" | "network" | "serial"
IMPRESSORA_VENDOR_ID = 0x04b8    # Epson
IMPRESSORA_PRODUCT_ID = 0x0e15   # TM-T20X
IMPRESSORA_COLUNAS = 48

# Empresa
EMPRESA_NOME = "Ranggo"
EMPRESA_CNPJ = ""
EMPRESA_ENDERECO = ""

# Numeração
COMANDA_NUMERO_INICIAL = 1
VENDA_NUMERO_INICIAL = 1
```

---

## 9. Glossário

- **PDV**: Ponto de Venda.
- **Comanda**: conta aberta vinculada a uma mesa, acumula itens até o fechamento. Identificada por número sequencial.
- **Ficha técnica**: receita do prato; lista de insumos e quantidades.
- **ESC/POS**: protocolo padrão de impressoras térmicas (Epson Standard Code).
- **NFC-e**: Nota Fiscal de Consumidor Eletrônica.
- **Destino de preparo**: para onde o item vai depois do pedido (cozinha, bar, ou direto pro cliente).
- **Estoque "Ilimitado"**: rótulo usado em listagens para pratos, que não têm estoque próprio (controle real é via insumos da ficha técnica).
