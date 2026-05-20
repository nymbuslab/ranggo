"""Configurações globais do Ranggo.

Apenas constantes — sem lógica. Reflete PROJETO.md §8.
"""

# ---------- Banco de dados ----------
# Caminho relativo à raiz do projeto. A pasta data/ é versionada (via .gitkeep),
# mas o arquivo .db NÃO é (ver .gitignore).
DB_PATH = "data/ranggo.db"

# ---------- Impressora térmica (ESC/POS) ----------
# Tipo de conexão da impressora: "usb" | "network" | "serial".
IMPRESSORA_TIPO = "usb"
# IDs USB padrão Epson TM-T20X. Ajustar conforme o modelo real instalado.
IMPRESSORA_VENDOR_ID = 0x04B8   # Epson
IMPRESSORA_PRODUCT_ID = 0x0E15  # TM-T20X
# Largura em colunas do papel térmico (48 = bobina 80mm padrão).
IMPRESSORA_COLUNAS = 48

# ---------- Dados da empresa ----------
# Aparecem em cupons, comprovantes e tickets de preparo.
EMPRESA_NOME = "Ranggo"
EMPRESA_CNPJ = ""
EMPRESA_ENDERECO = ""

# ---------- Numeração sequencial ----------
# Valores iniciais quando o banco está vazio. A partir daí cada nova
# comanda/venda recebe MAX(numero) + 1.
COMANDA_NUMERO_INICIAL = 1
VENDA_NUMERO_INICIAL = 1

# ---------- Desenvolvimento ----------
# Controla o eco de SQL no console pelo SQLAlchemy.
SQL_ECHO: bool = True  # True em desenvolvimento; False em produção/empacotado.
