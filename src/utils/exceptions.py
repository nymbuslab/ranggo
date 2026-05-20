"""Exceções de domínio do Ranggo.

Centraliza a hierarquia de erros de negócio do sistema. Toda exceção
levantada por um service deve herdar de :class:`RanggoError`, de modo
que a camada de UI possa capturar de forma uniforme e exibir mensagens
ao operador (dialog/snackbar) sem precisar conhecer cada subtipo.

Regras:
    * Services levantam exceções desta hierarquia — nunca ``Exception``
      genérica.
    * Repositories podem deixar vazar erros do SQLAlchemy; o service
      os converte para erros de domínio quando apropriado.
    * UI captura :class:`RanggoError` e mostra ``str(erro)`` ao usuário.
"""


class RanggoError(Exception):
    """Exceção raiz para todos os erros de domínio do Ranggo.

    Subclasses devem ser criadas em cada fase do roadmap, conforme
    novas regras de negócio forem implementadas. Esta classe não deve
    ser levantada diretamente — sempre use uma subclasse específica.
    """


# ---------------------------------------------------------------------------
# Fase 1 — Autenticação
# ---------------------------------------------------------------------------


class AutenticacaoError(RanggoError):
    """Erro durante o processo de autenticação ou autorização.

    Classe base para erros relacionados a login, sessão e permissões.
    Não levantar diretamente — usar uma das subclasses específicas.
    """


class LoginInvalidoError(AutenticacaoError):
    """Login ou senha incorretos.

    Levantada pelo ``AuthService.autenticar()`` quando o login não
    existe ou a senha não bate com o hash armazenado. Mensagem genérica
    para o usuário final — não revelar qual dos dois estava errado,
    para não facilitar enumeração de logins válidos.
    """


class UsuarioInativoError(AutenticacaoError):
    """Tentativa de login com usuário marcado como inativo (``ativo=False``).

    Levantada pelo ``AuthService.autenticar()`` após validação
    bem-sucedida de login + senha, quando o campo ``ativo`` do usuário
    está ``False``. Permite à UI exibir mensagem específica ("conta
    desativada — fale com o administrador") em vez do genérico de
    credenciais inválidas.
    """


class PermissaoNegadaError(AutenticacaoError):
    """Usuário autenticado tenta ação que seu perfil não autoriza.

    Ex.: Caixa tenta acessar a tela de Usuários (restrita a Admin) ou
    aplicar desconto sem a permissão ``aplicar_desconto``. Usada pela
    UI para bloquear navegação ou ações específicas, e pelos services
    como guarda em pontos sensíveis.
    """


class ValidacaoError(RanggoError):
    """Erro de validação de dados de entrada.

    Classe base para falhas de regra de formato/consistência detectadas
    por services antes de persistir. Não levantar diretamente — usar
    uma das subclasses específicas.
    """


class NomeDuplicadoError(ValidacaoError):
    """Tentativa de criar entidade com campo único já existente.

    Ex.: criar usuário com ``login`` que já existe, criar perfil com
    ``nome`` já cadastrado. O service deve validar antes de chamar
    ``repository.criar()`` para evitar depender de ``IntegrityError``
    do SQLAlchemy como mecanismo de controle.
    """


class SenhaFracaError(ValidacaoError):
    """Senha não atende à política mínima.

    Política da Fase 1: mínimo de 6 caracteres (sem outras regras).
    Vai endurecer na Fase 5 (segurança expandida) — letras + números,
    bloqueio de senhas óbvias, etc. Levantada pelo ``AuthService`` ao
    cadastrar ou trocar senha.
    """


# ---------------------------------------------------------------------------
# Hierarquia futura prevista (roteiro — adicionar conforme cada fase)
# ---------------------------------------------------------------------------
#
# Fase 2 — Cadastros:
#   (ValidacaoError já implementada na Fase 1)
#       class ReferenciaInvalidaError(ValidacaoError): ...
#   class FichaTecnicaError(RanggoError): ...
#       class InsumoJaNaFichaError(FichaTecnicaError): ...
#
# Fase 3 — Venda Balcão / PDV:
#   class EstoqueError(RanggoError): ...
#       class EstoqueInsuficienteError(EstoqueError): ...
#   class VendaError(RanggoError): ...
#       class CarrinhoVazioError(VendaError): ...
#       class DescontoNaoPermitidoError(VendaError): ...
#   class ImpressaoError(RanggoError): ...
#       class ImpressoraIndisponivelError(ImpressaoError): ...
#
# Fase 4 — Comandas e Mesas:
#   class ComandaError(RanggoError): ...
#       class ComandaJaFechadaError(ComandaError): ...
#       class MesaOcupadaError(ComandaError): ...
#
# Fase 5 — Delivery / Relatórios / NFC-e:
#   class DeliveryError(RanggoError): ...
#       class EnderecoIncompletoError(DeliveryError): ...
#   class FiscalError(RanggoError): ...
#       class NFCeEmissaoError(FiscalError): ...
#
# ---------------------------------------------------------------------------
