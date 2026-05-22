# Roteiro de Testes Manuais — Fase 1 (Autenticação)

> Roteiro a ser executado MANUALMENTE antes de qualquer release que toque código da Fase 1 (autenticação, sessão, usuários, shell, roteamento). Tempo estimado: 15 minutos.

**Pré-condições:**

- `python main.py` executável.
- Banco `data/ranggo.db` existe (será criado se não existir).
- Usuário `admin` com senha `admin123` existe no banco (seed inicial).

---

## Bloco 1 — Autenticação básica (5 min)

### 1.1 Login bem-sucedido

- [ ] Rodar `python main.py`.
- [ ] Janela abre na tela de Login (maximizada, sem "Working...").
- [ ] Layout: lado esquerdo preto com logo Ranggo, lado direito branco com formulário.
- [ ] Preencher login=`admin` senha=`admin123`. Clicar Entrar.
- [ ] Tela troca pra shell (sidebar preta, topbar branca, conteúdo central com card "Fundação OK").

### 1.2 Login com senha errada

- [ ] Logout via "Fechar Caixa" → Confirmar.
- [ ] Voltar para Login. Login=`admin`, senha=`errada`. Entrar.
- [ ] Erro inline em vermelho: "Login ou senha incorretos."
- [ ] Começar a digitar em qualquer campo: erro some.

### 1.3 Login com usuário inexistente

- [ ] Login=`naoexiste`, senha=`qualquer`. Entrar.
- [ ] Mesmo erro genérico "Login ou senha incorretos." (não revela se é usuário que não existe — defesa contra enumeração).

### 1.4 Campos vazios

- [ ] Submeter formulário vazio.
- [ ] Erro inline: "Preencha login e senha."

### 1.5 Foco automático + Enter no campo senha

- [ ] Reabrir Login (logout). Cursor já deve estar piscando no campo Usuário.
- [ ] Digitar `admin`, Tab, digitar `admin123`, Enter.
- [ ] Login funciona via Enter (sem precisar clicar "Entrar").

---

## Bloco 2 — Sidebar + sessão (3 min)

### 2.1 Sidebar mostra usuário real

- [ ] Logar com admin/admin123.
- [ ] Rodapé da sidebar: avatar circular laranja com "A" branca.
- [ ] Nome principal: "Administrador". Perfil: "Admin".
- [ ] Botão vermelho "Fechar Caixa" logo abaixo.

### 2.2 Item "Usuários" só visível pra Admin

- [ ] Logado como admin: item "Usuários" aparece na sidebar (ícone pessoas).
- [ ] Item "Configurações" aparece também (placeholder Fase 5+).
- [ ] Clicar "Usuários": carrega Lista de Usuários, item destacado em laranja.

### 2.3 Fechar Caixa (logout)

- [ ] Clicar "Fechar Caixa" na sidebar.
- [ ] Dialog modal: "Fechar Caixa" / "Deseja realmente fechar o caixa e sair do sistema?" / [Cancelar] [Fechar Caixa laranja].
- [ ] Fundo do dialog é BRANCO PURO (não tonalizado).
- [ ] Cancelar: dialog fecha, volta pro shell.
- [ ] Repetir, clicar "Fechar Caixa": volta pra tela de Login.
- [ ] Sessão zerada (verificado: dashboard não acessível sem novo login).

---

## Bloco 3 — CRUD de Usuários (5 min)

### 3.1 Lista de Usuários

- [ ] Logar admin, clicar "Usuários".
- [ ] Topbar mostra "Usuários" + botão "+ Novo Usuário" laranja.
- [ ] Tabela com colunas: Usuário, Login, Perfil, Status, Ações.
- [ ] Cada linha: avatar laranja com inicial + 3 botões de ação (editar, trocar senha, bloquear/ativar).
- [ ] Filtro de busca funciona (digitar parte do nome ou login).
- [ ] Toggle "Mostrar inativos" funciona (mostra/oculta usuários ativo=False, linha dimmed quando inativo).

### 3.2 Criar usuário

- [ ] Clicar "+ Novo Usuário".
- [ ] Topbar muda pra "Novo Usuário" (sem botão à direita).
- [ ] Card central 800px com Nome, Login, Senha+Confirmar, Perfil.
- [ ] Campos com largura total do card (Nome, Login, Perfil) / Senha+Confirmar lado a lado.
- [ ] Botões [Cancelar cinza] [Criar Usuário laranja] mesmo tamanho.
- [ ] Tentar criar com senha < 6 chars: erro inline.
- [ ] Tentar criar com login duplicado (`admin`): erro inline.
- [ ] Criar com dados válidos (ex: Carlos/carlos/senha123/Caixa): volta pra lista, Carlos aparece.

### 3.3 Editar usuário

- [ ] Clicar lápis na linha do Carlos.
- [ ] Topbar muda pra "Editar Usuário".
- [ ] Campos pré-preenchidos. Login DISABLED com tooltip "chave histórica".
- [ ] SEM campos de senha.
- [ ] Switch "Usuário ativo" presente.
- [ ] Botões [Cancelar cinza] [Salvar Alterações laranja].
- [ ] Mudar nome pra "Carlos Editado", Salvar. Volta pra lista.

### 3.4 Editar o próprio admin

- [ ] Clicar lápis na linha do Administrador.
- [ ] Switch "Usuário ativo" DISABLED com tooltip "Você não pode desativar a própria conta. Peça a outro Admin."
- [ ] Cancelar (sem alterar).

### 3.5 Trocar senha de outro usuário

- [ ] Clicar chave na linha de qualquer usuário.
- [ ] Modal "Alterar Senha" abre com fundo BRANCO PURO.
- [ ] Box informativo: "Usuário: Nome (login)".
- [ ] 2 campos password com olho de revelar.
- [ ] Helper text: "A senha deve conter no mínimo 6 caracteres."
- [ ] Tentar com senhas diferentes: erro inline.
- [ ] Tentar com senha < 6 chars: erro inline.
- [ ] Tentar com senhas iguais e válidas: SnackBar verde "Senha de 'Nome' atualizada."

### 3.6 Desativar usuário (soft delete)

- [ ] Clicar bloqueio na linha do Carlos (ou outro não-admin).
- [ ] Dialog "Desativar usuário" fundo BRANCO PURO, botão [Desativar VERMELHO].
- [ ] Confirmar: linha some (default oculta inativos).
- [ ] Ligar toggle "Mostrar inativos": Carlos aparece dimmed com badge cinza "Inativo" + ícone toggle vira PLAY_CIRCLE.
- [ ] Clicar PLAY_CIRCLE na linha do Carlos.
- [ ] Dialog "Ativar usuário" fundo BRANCO PURO, botão [Ativar LARANJA] (não verde).
- [ ] Confirmar: Carlos volta a Ativo.

### 3.7 Tentar desativar o último admin

- [ ] Clicar bloqueio na linha do Administrador.
- [ ] Confirmar no dialog.
- [ ] SnackBar VERMELHO: "Nao eh possivel desativar o ultimo Admin ativo do sistema."
- [ ] Admin continua ativo.

---

## Bloco 4 — Trocar de perfil (2 min)

### 4.1 Login como não-Admin

- [ ] Fechar Caixa (logout). Login como joao/senha123 (perfil Caixa).
- [ ] Sidebar NÃO mostra item "Usuários" (só admin tem).
- [ ] Item "Configurações" continua visível (placeholder).
- [ ] Rodapé: avatar com "J", nome "Joao Silva", perfil "Caixa".

### 4.2 Login como inativo

- [ ] Logout. Tentar logar com usuário inativo (criar/desativar antes se não houver).
- [ ] Erro inline: "Conta desativada. Contate o administrador."

---

## Bloco 5 — Robustez (3 min)

### 5.1 Topbar consistente

- [ ] Logar admin. Trocar entre Dashboard / Usuários / Novo Usuário / Editar Usuário.
- [ ] Topbar deve ser visualmente IDÊNTICA em todas (fundo branco, altura, padding). Só muda título e botão à direita.
- [ ] Botões "+ Nova Venda" (Dashboard) e "+ Novo Usuário" (Usuários) têm MESMO tamanho/padding.

### 5.2 Shutdown limpo (CRÍTICO)

- [ ] Rodar `python main.py`.
- [ ] Logar.
- [ ] Fechar pelo X (NÃO via Fechar Caixa).
- [ ] Esperar < 3 segundos pro processo encerrar.
- [ ] Em outro terminal: `Get-Process -Name flet -ErrorAction SilentlyContinue` deve retornar VAZIO.
- [ ] Repetir 5 vezes seguidas. NENHUMA deve travar em "Working..." ou demorar > 3 s.

### 5.3 Banco persistente

- [ ] Criar um usuário novo (ex: teste_persistencia).
- [ ] Fechar app pelo X.
- [ ] Abrir app de novo. Logar.
- [ ] Verificar que teste_persistencia ainda existe na lista.

---

## Resultado

Marcar abaixo após rodar:

- Data da execução: ____/____/______
- Bloco 1 (Autenticação básica): ___/5 testes OK
- Bloco 2 (Sidebar + sessão): ___/3 testes OK
- Bloco 3 (CRUD de Usuários): ___/7 testes OK
- Bloco 4 (Trocar de perfil): ___/2 testes OK
- Bloco 5 (Robustez): ___/3 testes OK
- **TOTAL: ___/20 testes OK**

Se 20/20: Fase 1 válida, pode taggar.
Se < 20: investigar falhas antes de tag/release.
