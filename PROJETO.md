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
├── 07-modal-checkout.png
├── 08-listagem-usuarios.png
├── 09-formulario-usuario.png
└── 10-modal-trocar-senha.png
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

### 4.7 Caixa Operacional

Para auditoria contábil e rastreabilidade, **toda venda finalizada é vinculada a um caixa** (turno operacional) aberto por um operador.

**Conceito:**
- **Caixa** = sessão de trabalho no PDV (financeiro), com início (abertura) e fim (fechamento).
- Apenas **um caixa pode estar aberto por vez** (sistema single-machine).
- O caixa é o **único ponto de entrada de dinheiro** do restaurante. Todas as frentes operacionais (comanda, balcão, delivery) convergem para o caixa no momento do pagamento.

**Frentes operacionais vs. Caixa:**

```text
[COMANDA (mesa)]  [BALCÃO (rápido)]  [DELIVERY (telefone)]   ← Frentes de pedido
       \                |                /                       (múltiplas abertas simultâneas)
        \               |               /
         +----------+ + +----------+
                    ▼
                [ CAIXA ]   ← Único ponto de pagamento.
                              Vincula a venda finalizada ao turno aberto.
```

**Estados da venda:**
- `aberta` — pedido em construção (comanda em mesa, delivery em rota, balcão sendo montado).
- `pendente_pagamento` — chegou no caixa, aguarda confirmação.
- `finalizada` — pagamento confirmado. **Único estado que conta no fechamento de caixa.**
- `cancelada` — cancelada antes de finalizar OU estornada após (registra motivo).

**Vinculação `vendas.caixa_id`:** a venda nasce **sem caixa** (na frente operacional). Recebe `caixa_id` apenas ao ser finalizada. Comanda aberta no turno A mas paga no turno B vai pro caixa B (operador que efetivamente recebeu o dinheiro).

**Fluxo do caixa:**
1. **Abertura**: operador faz login → se não há caixa aberto, tela "Abrir Caixa" pede valor inicial em dinheiro (fundo de troco) → caixa criado e vinculado ao usuário.
2. **Durante o turno**: todas as vendas finalizadas pelo operador acumulam no caixa aberto. Sangrias e estornos também.
3. **Fechamento**: operador clica "Fechar Caixa" → sistema mostra resumo por forma de pagamento → pede valor real contado em dinheiro → calcula divergência → registra e faz logout.
4. **Próximo operador**: login → como não há caixa aberto, abre novo caixa.

**Regras de negócio:**

- **R1 — Pendências ao fechar caixa**: se houver comandas, deliveries ou vendas balcão com status `aberta`/`pendente_pagamento`, sistema **alerta** com detalhes (*"Há N comandas (mesa X, mesa Y) e M deliveries (entregador Z). Essas vendas continuarão disponíveis para o próximo operador. Confirmar fechamento?"*) e permite decisão. Se confirmar, fecha caixa; vendas em aberto permanecem disponíveis e serão vinculadas ao próximo caixa que estiver aberto quando finalizadas.

- **R2 — Bloqueio de troca de operador**: se o operador A está com caixa aberto e o operador B (não-Admin) tenta logar, sistema **bloqueia**: *"Caixa aberto pertence a [Nome de A]. Peça que ele feche o caixa antes de continuar."*

- **R3 — Exceção Admin**: se B for Admin, sistema **permite o login** e oferece duas opções: *(a) Forçar fechamento do caixa de [A] e abrir novo caixa em meu nome*; *(b) Cancelar e sair*. Toda forçada é auditada em `caixas.fechamento_admin_id`.

- **R4 — Sem fiado**: toda venda finalizada **obrigatoriamente** teve pagamento confirmado no ato. O sistema **não suporta** "cliente leva agora e paga depois" no MVP.

- **R5 — Cancelamento de venda finalizada**: apenas usuários com perfil **Admin** podem cancelar uma venda já finalizada. Cancelamento exige **motivo obrigatório** registrado em `vendas.motivo_cancelamento`. O cancelamento gera **movimentação reversa de estoque** (devolve insumos/produtos) e contabiliza no fechamento do caixa atual como estorno.

- **R6 — Sangria**: durante o turno, o operador pode retirar dinheiro do caixa (pagar fornecedor, troco emergencial, etc.). Cada sangria exige **motivo obrigatório** e fica registrada em `movimentacao_caixa`. Impacta o cálculo de divergência no fechamento.

- **R7 — Troco em vendas em dinheiro**: vendas com forma de pagamento `dinheiro` registram `valor_pago` (informado pelo operador) e `troco` (calculado: `valor_pago - total`). Ambos persistidos para auditoria.

- **R8 — Quebra de caixa**: divergência negativa (dinheiro físico < esperado) é permitida mas **exige observação obrigatória** em `caixas.observacao` no momento do fechamento.

**Implementação:** o conceito de Caixa entra na **Fase 3** junto com Venda Balcão. Na Fase 1 (Autenticação), o botão "Fechar Caixa" funciona apenas como logout simples (placeholder visual). Estados expandidos de `vendas` e tabela `caixas` são criados na Fase 3.

### 4.8 Comissão de Garçom (débito técnico — Fase 6+)

O sistema deverá, em fase futura, calcular comissão de garçom por venda. As regras concretas serão definidas após 1-2 meses de operação real do MVP, capturando as práticas reais do restaurante (% fixo ou variável, base de cálculo, atribuição em balcão/delivery, forma de pagamento — sangria do caixa ou acumulação mensal).

**Provisão estrutural (Fase 4):** o model `Comanda` já será criado com campo nullable `garcom_id` (FK para `usuarios`), permitindo registrar quem atendeu a mesa sem ainda calcular comissão. Isso evita migration dolorosa quando a Fase 6+ chegar.

Nada de UI relacionada a comissão é construído antes da definição completa das regras.

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
         ├─→ comanda (opcional)
         └─→ caixa (preenchido na finalização)

mesas ──→ comandas ──→ comanda_itens
usuarios ──→ comandas (garcom_id, nullable — provisão Fase 6+)

caixas ──┬─→ vendas (toda venda finalizada vinculada ao caixa do operador)
         └─→ movimentacao_caixa (sangria / suprimento)
usuarios ──→ caixas (operador que abriu + fechamento_admin_id auditado)

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
| `caixas` | id, **numero** (sequencial), usuario_id (FK), abertura_em, valor_inicial, fechamento_em (nullable), valor_final_dinheiro (nullable), valor_final_sistema (nullable), divergencia (nullable), observacao (nullable), fechamento_admin_id (FK usuarios, nullable) |
| `comandas` | id, **numero** (sequencial), mesa_id, cliente_id, garcom_id (FK usuarios, nullable), status (aberta/fechada), aberta_em, fechada_em, usuario_id |
| `comanda_itens` | id, comanda_id, produto_id/prato_id, quantidade, preco_unitario, observacao |
| `vendas` | id, **numero** (sequencial), caixa_id (FK, nullable — preenchido na finalização), tipo (balcao/comanda/delivery), comanda_id (nullable), cliente_id (nullable), usuario_id (operador), subtotal, **desconto**, total, forma_pagamento, valor_pago (nullable — dinheiro), troco (nullable — dinheiro), status (aberta/pendente_pagamento/finalizada/cancelada), motivo_cancelamento (nullable), criada_em, finalizada_em (nullable) |
| `venda_itens` | id, venda_id, produto_id/prato_id, quantidade, preco_unitario, subtotal |
| `movimentacao_estoque` | id, tipo (entrada/saida), produto_id/insumo_id, quantidade, motivo, venda_id, data, usuario_id |
| `movimentacao_caixa` | id, caixa_id (FK), tipo (sangria/suprimento), valor, motivo, criada_em, usuario_id (FK) |

---

## 7. Roadmap

O roadmap detalhado das fases está em `ROADMAP.md`, que é a fonte única de verdade sobre o futuro do projeto. Resumo:

- **Fase 0** — Fundação ✅
- **Fase 1** — Autenticação 🔄
- **Fase 2** — Cadastros 🔜
- **Fase 3** — Venda Balcão + Caixa Operacional 🔜
- **Fase 4** — Comandas e Mesas 🔜
- **Fase 5** — Delivery, Relatórios, NFC-e, Segurança expandida 🔜
- **Fase 6** — Pós-MVP (comissão, melhorias orgânicas) 🔜

Estado atual, dependências, critérios de "pronto" e decisões em aberto: ver `ROADMAP.md`.

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
- **Caixa Operacional**: turno de trabalho de um operador no PDV, com abertura (valor inicial) e fechamento (cálculo de divergência). Toda venda finalizada é vinculada a um caixa.
- **Sangria**: retirada de dinheiro do caixa durante o turno, com motivo registrado.
- **Suprimento**: entrada de dinheiro no caixa durante o turno (ex.: reforço de troco), com motivo registrado.
- **Quebra de caixa**: divergência negativa entre dinheiro físico contado e valor esperado pelo sistema no fechamento.
- **Fechamento administrativo**: fechamento forçado de caixa alheio por Admin, registrado em auditoria.
- **Pendência**: comanda aberta, delivery em rota ou venda balcão em construção — não impede fechamento de caixa, mas gera alerta.
