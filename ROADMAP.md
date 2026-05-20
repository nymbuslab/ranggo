# Roadmap do Ranggo

> Visão estratégica do projeto: onde estamos, para onde vamos, e por quê.
>
> **Outras referências:**
> - O QUE/COMO funciona: ver `PROJETO.md`.
> - PADRÕES técnicos: ver `CLAUDE.md`.
> - O QUE estou fazendo agora: ver `PROGRESSO.md`.
> - O QUE já foi feito: ver `CHANGELOG.md`.

---

## Estado Atual

**Versão:** v0.1.1 (Fase 0 + rebrand concluídos)
**Em andamento:** Fase 1 — Autenticação
**Última atualização:** 2026-05-20

---

## Visão Geral das Fases

| Fase | Tema | Status | Tag prevista |
|---|---|---|---|
| 0 | Fundação | ✅ Concluída | v0.1.0 + v0.1.1 |
| 1 | Autenticação | 🔄 Em andamento | v0.2.0 |
| 2 | Cadastros | 🔜 Próxima | v0.3.0 |
| 3 | Venda Balcão + Caixa Operacional | 🔜 | v0.4.0 |
| 4 | Comandas e Mesas | 🔜 | v0.5.0 |
| 5 | Delivery, Relatórios, NFC-e, Segurança expandida | 🔜 | v0.6.0 |
| 6 | Pós-MVP (comissão, melhorias orgânicas) | 🔜 | v1.0.0 |

**Convenção de versionamento:** cada fase fecha em uma minor (`v0.X.0`). Patches (`v0.X.Y`) são correções entre fases (ex: rebrand, fix de bug crítico).

---

## Fase 0 — Fundação ✅

**Tag:** `v0.1.0` (Fundação) + `v0.1.1` (rebrand Oui Chef → Ranggo).

**Objetivo de negócio:** ter o esqueleto técnico funcional rodando — banco, shell visual, identidade visual, bootstrap — antes de qualquer feature.

**Escopo entregue:**

- Stack fixada: Python 3.12 + Flet 0.85.1 + SQLAlchemy 2.0.49 + SQLite + bcrypt + python-escpos.
- Identidade visual completa (cores, tipografia Inter, espaçamento).
- 7 protótipos no Google Stitch.
- Estrutura de pastas (`src/`, `database/`, `repositories/`, `services/`, `ui/`).
- Models de fundação: `Usuario`, `Perfil`, `Permissao`, `perfil_permissoes`, `UnidadeMedida`.
- `connection.py` com PRAGMA FK on, naming convention determinística.
- `seed.py` idempotente (UnidadeMedida + Perfis).
- `theme.py` espelhando identidade visual.
- Shell visual (sidebar + topbar + card "Fundação OK").
- `main.py` com bootstrap completo + shutdown limpo (handler de close + `os._exit`).
- Rebrand para Ranggo + logo SVG/ICO.

**Decisões consolidadas durante a fase:** ver `PROJETO.md §3` (identidade visual) e `§4.4–4.5` (numeração, desconto).

---

## Fase 1 — Autenticação 🔄

**Tag prevista:** `v0.2.0`.

**Objetivo de negócio:** restringir acesso ao sistema — só usuários cadastrados podem operar. Base pra qualquer feature subsequente (toda venda terá `usuario_id`).

**Escopo:**

- Repositories `UsuarioRepository` e `PerfilRepository`.
- Subclasses de `RanggoError` para autenticação e validação.
- `AuthService` com bcrypt (hash, verify, autenticar).
- Módulo singleton `sessao.py` para usuário logado em memória.
- Seed expandido: 3 permissões conhecidas + usuário Admin inicial (`admin` / `admin123`).
- Tela de Login fiel ao `prototipos/01-login.png`.
- Roteamento Login ↔ Shell em `app.py`.
- Refatorar sidebar para mostrar usuário real da sessão.
- CRUD de Usuários (lista + formulário, restrito a Admin).
- Botão "Fechar Caixa" funciona como logout simples (placeholder — vira fechamento real na Fase 3).

**Decisões cravadas (não revisitar nesta fase):**

- Política de senha: mínimo 6 caracteres (sem regras de complexidade).
- "Esqueci minha senha": link visível mas desabilitado, com tooltip explicativo.
- Bloqueio após tentativas erradas: postergado para Fase 5.
- Trocar senha no primeiro login: postergado para Fase 5.
- Permissões granulares: só perfil agora; emergem orgânicas conforme features chegam.
- Estado de sessão: módulo singleton (`src/services/sessao.py`), não atributo de `page`.

**Critérios de "pronto":**

1. ✅ Login com `admin`/`admin123` funciona.
2. ✅ Tela de Login fiel ao protótipo (validação visual).
3. ✅ Após login, shell mostra "Admin" e perfil "Admin" no rodapé da sidebar.
4. ✅ Clicar "Fechar Caixa" desloga e volta à tela de Login.
5. ✅ Admin consegue criar novo usuário pela tela de Usuários.
6. ✅ Logar com usuário recém-criado funciona.
7. ✅ Usuário com perfil != Admin não vê o item "Usuários" no menu.
8. ✅ `python main.py` 5 ciclos seguidos sem regressão de shutdown.

**Débitos previstos para outras fases:**

- Reset de senha (Fase 4 ou 5, conforme demanda real).
- Política de força de senha (Fase 5).
- 2FA opcional para Admin (Fase 5).
- Sessão persistente entre reinícios (Fase 5+, se virar requisito).

---

## Fase 2 — Cadastros 🔜

**Tag prevista:** `v0.3.0`.

**Objetivo de negócio:** cadastrar tudo o que será vendido. Sem isso, Fase 3 (venda) não tem o que vender.

**Escopo:**

- Categorias.
- Unidades de medida (já seedada na Fase 0 — só CRUD aqui se necessário).
- Produtos (revenda — Coca, cerveja).
- Insumos (matérias-primas — arroz, carne).
- Pratos (preparados — marmitex).
- Ficha Técnica (composição de pratos com insumos).
- Clientes (com endereço, para futuro delivery).
- Fornecedores.

**Referências de UI:** `prototipos/03-listagem-cadastro.png` (genérica), `04-formulario-cadastro.png` (genérico), `05-ficha-tecnica.png` (específico).

**Decisões em aberto:**

- Como tratar produtos vendidos a peso (granel) vs. unidade? Provavelmente atributo `vendido_por_unidade: bool`.
- Ficha técnica permite múltiplos preparos do mesmo prato (variação tamanho P/M/G)? Adiado — começa com 1:1 prato↔ficha.
- Histórico de preço de custo de insumo? Adiado para Fase 5+.

**Critérios de "pronto":**

1. ✅ Cadastro funcional dos 7 modelos acima.
2. ✅ Ficha técnica calcula custo automático do prato.
3. ✅ Tela de produtos mostra estoque atual; pratos mostram "Ilimitado".
4. ✅ Validações de FK funcionam (não dá pra excluir categoria com produtos vinculados).

---

## Fase 3 — Venda Balcão + Caixa Operacional 🔜

**Tag prevista:** `v0.4.0`.

**Objetivo de negócio:** o sistema vira PDV — registra venda, dá baixa em estoque, fecha caixa.

**Escopo de Venda:**

- PDV (`prototipos/06-pdv.png`): grid de produtos, carrinho, formas de pagamento.
- Modal de checkout (`prototipos/07-modal-checkout.png`).
- Numeração sequencial de venda.
- Impressão de tickets de cozinha/bar (python-escpos).
- Baixa de estoque automática (produtos diretos; pratos via ficha técnica).
- Desconto manual com permissão.
- Controle de troco (em vendas em dinheiro).
- Cancelamento de venda finalizada (Admin com motivo obrigatório).

**Escopo de Caixa Operacional** (detalhes em `PROJETO.md §4.7`):

- Tabela `caixas` + estados expandidos em `vendas`.
- Tela de Abertura de Caixa (valor inicial).
- Tela de Fechamento de Caixa (resumo + divergência + observação se quebra).
- Tela de Sangria/Suprimento durante o turno.
- Regras R1–R8 cravadas (`PROJETO.md §4.7`).
- Botão "Fechar Caixa" da sidebar deixa de ser logout simples e vira fechamento real.

**Decisões em aberto:**

- Tickets de cozinha: 1 ticket por prato ou agrupado por venda? Provavelmente agrupado.
- Sangria com aprovação de Admin ou liberada pro operador? Inclinação: liberada com motivo + auditoria.

**Critérios de "pronto":**

1. ✅ Operador abre caixa com valor inicial, vende, fecha caixa com resumo.
2. ✅ Vendas finalizadas dão baixa em estoque (insumos via ficha técnica).
3. ✅ Tickets de cozinha imprimem agrupados pelo destino (`cozinha`/`bar`).
4. ✅ Cancelamento de venda restaura estoque.
5. ✅ Troca de operador bloqueia se há caixa aberto (com exceção Admin).
6. ✅ Sangria registrada impacta cálculo de divergência.

---

## Fase 4 — Comandas e Mesas 🔜

**Tag prevista:** `v0.5.0`.

**Objetivo de negócio:** suportar atendimento de mesa — pedido aberto que acumula itens e fecha no caixa.

**Escopo:**

- Cadastro de mesas (número, capacidade).
- Abertura/fechamento de comanda vinculada a mesa.
- Adicionar itens em comanda aberta.
- Numeração sequencial de comanda.
- Transferência de comanda entre mesas.
- Divisão de conta (rateio entre N pessoas).
- Campo `garcom_id` em `comandas` (provisão para Fase 6+).

**Decisões em aberto:**

- Divisão de conta: igual entre todos ou seletiva (cada pessoa escolhe o que paga)? Sugestão: começar com igual; seletiva vira refinamento.
- Tempo máximo de comanda aberta? Sem limite no MVP.
- "Couvert" / taxa de serviço: campo separado em `vendas`? Adiado para Fase 5.

**Critérios de "pronto":**

1. ✅ Garçom abre comanda na mesa 5, adiciona 3 itens.
2. ✅ Cliente pede a conta no caixa → operador fecha comanda → pagamento normal.
3. ✅ Mesa pode ter comanda transferida pra outra.
4. ✅ Conta pode ser dividida entre 3 pessoas.

---

## Fase 5 — Delivery, Relatórios, NFC-e, Segurança expandida 🔜

**Tag prevista:** `v0.6.0`.

**Objetivo de negócio:** fechar funcionalidades operacionais (delivery, relatórios) + endurecer segurança (NFC-e + autenticação robusta).

**Escopo de Delivery:**

- Pedido vinculado a Cliente com endereço.
- Status (pendente, em rota, entregue, cancelado).
- Atribuição de entregador.
- Taxa de entrega.

**Escopo de Relatórios:**

- Vendas por período/categoria/prato.
- Top produtos mais vendidos.
- Estoque atual e abaixo do mínimo.
- Faturamento por forma de pagamento.
- Auditoria de descontos aplicados.
- Histórico de caixas fechados.

**Escopo de NFC-e:**

- Integração com ACBrLibPython.
- Configuração de certificado digital + CSC do estado.
- Emissão de NFC-e ao fechar venda (opcional, conforme regime fiscal).
- Contingência e reenvio.

**Escopo de Segurança expandida:**

- Política de senha forte (mínimo 8, com regras).
- Bloqueio após N tentativas falhadas.
- Troca de senha obrigatória no primeiro login.
- 2FA opcional para Admin.
- Reset de senha pelo Admin.

**Decisões em aberto:**

- Integração com aplicativo de delivery externo (iFood, Uber Eats)? Adiado para Fase 6+.
- Relatórios exportáveis em PDF/Excel? Adiado para Fase 6+.
- NFC-e contingência offline? Confirmar com contador/usuário.

**Critérios de "pronto":**
Documentados quando a fase iniciar (escopo amplo demais para cravar hoje).

---

## Fase 6 — Pós-MVP 🔜

**Tag prevista:** `v1.0.0` (marco de "sistema completo").

**Objetivo de negócio:** absorver aprendizados de operação real e implementar features que não cabiam no caminho crítico.

**Escopo provável (a refinar conforme operação real):**

- **Comissão de garçom** (detalhes em `PROJETO.md §4.8`).
- Integração com apps de delivery externos.
- Relatórios exportáveis (PDF/Excel).
- Histórico de preço de custo de insumos.
- Variações de prato (P/M/G).
- Backup automático do banco.
- Melhorias orgânicas baseadas em feedback de uso real.

**Decisão estratégica:** Fase 6 só começa após 1-2 meses de operação real do MVP (Fases 0-5 instaladas e usadas). Sem isso, qualquer escopo aqui é especulação.

---

## Débitos Técnicos Transversais

Tarefas pequenas que não pertencem a nenhuma fase específica, mas precisam ser endereçadas em algum momento:

- [ ] Lint markdown em `CLAUDE.md` e `CHANGELOG.md` (warnings de espaçamento, language em code fences, etc).
- [ ] Logo SVG real na sidebar (✅ resolvido na v0.1.1).
- [ ] ICO multi-resolução para empacotamento (✅ resolvido — 16/32/48/256 em `assets/logo/`).
- [ ] Push do repositório para remote (GitHub privado ou similar) — sem isso, projeto não tem backup.
- [ ] Configurar pytest + primeiros testes unitários (decisão adiada — sem usuário ainda, prioridade baixa).
- [ ] Validação de força do tipo `mypy --strict` (decisão adiada).

---

## Decisões Estratégicas em Aberto

Decisões grandes que não foram tomadas e podem impactar o roadmap:

- **Multi-empresa**: o sistema vai atender mais de um restaurante no futuro (versão SaaS)? Hoje a arquitetura é single-tenant. Mudar requer rework significativo.
- **Versão mobile/garçom**: comanda mobile pro garçom anotar na mesa? Hoje é só PDV no caixa. Mudar requer arquitetura cliente/servidor.
- **Modo offline-first com sync**: hoje é só local. Versão que sincroniza com nuvem? Possível Fase 7+.
- **Integração com balança eletrônica**: produtos vendidos a peso (granel)? Hoje só unidade. Fase 6+ se virar demanda real.

---

## Convenções deste documento

- **Status:** ✅ Concluído / 🔄 Em andamento / 🔜 Planejado / ❌ Cancelado.
- **Tags git** seguem [SemVer](https://semver.org/lang/pt-BR/): MAJOR.MINOR.PATCH.
- Quando uma fase fecha, atualizar status para ✅ e mover detalhes para `CHANGELOG.md`.
- Decisões em aberto que viram cravadas: mover para `PROJETO.md` (regras de negócio) ou `CLAUDE.md` (padrões técnicos).
