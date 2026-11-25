"""Skill Alexa de conversa livre com LLM grátis + pesquisa na web."""
import logging
import random
from xml.sax.saxutils import escape

from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.dispatch_components import (
    AbstractExceptionHandler,
    AbstractRequestHandler,
)
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.utils import get_slot_value, is_intent_name, is_request_type
from ask_sdk_model.services.directive import Header, SendDirectiveRequest, SpeakDirective

import config
import llm

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REPROMPTS = [
    "Pode falar, estou ouvindo.",
    "Quer conversar sobre mais alguma coisa?",
    "E aí, o que mais?",
]
DESPEDIDAS = {
    "tchau", "até logo", "até mais", "falou", "chega", "pode parar", "obrigado tchau",
    "obrigada tchau", "encerrar", "sair", "boa noite tchau", "é só isso", "só isso",
}
FRASES_PESQUISANDO = [
    "Deixa eu pesquisar isso.",
    "Um segundinho, vou dar uma olhada.",
    "Vou procurar pra você.",
]


def _ssml(texto):
    return escape(texto[:6000])


def _historico(handler_input):
    return handler_input.attributes_manager.session_attributes.setdefault("historico", [])


def _salvar_turno(handler_input, fala, resposta):
    hist = _historico(handler_input)
    hist.append({"role": "user", "content": fala})
    hist.append({"role": "assistant", "content": resposta})
    del hist[: max(0, len(hist) - config.MAX_HISTORICO)]


def _resposta_progressiva(handler_input, frase):
    """Faz a Alexa falar algo enquanto a resposta final ainda está sendo gerada."""
    try:
        request_id = handler_input.request_envelope.request.request_id
        servico = handler_input.service_client_factory.get_directive_service()
        servico.enqueue(
            SendDirectiveRequest(
                header=Header(request_id=request_id),
                directive=SpeakDirective(speech=f"<speak>{escape(frase)}</speak>"),
            )
        )
    except Exception as erro:  # não é crítico
        logger.warning("Resposta progressiva falhou: %s", erro)


def _conversar(handler_input, fala, forcar_pesquisa=False):
    rb = handler_input.response_builder
    if not fala:
        return rb.speak("Não peguei o que você disse. Pode repetir?").ask(
            "Pode repetir?"
        ).response

    if fala.lower().strip(" .!?") in DESPEDIDAS:
        return rb.speak("Foi ótimo conversar com você. Até mais!").set_should_end_session(
            True
        ).response

    try:
        resposta = llm.responder(
            _historico(handler_input),
            fala,
            ao_pesquisar=lambda: _resposta_progressiva(
                handler_input, random.choice(FRASES_PESQUISANDO)
            ),
            forcar_pesquisa=forcar_pesquisa,
        )
    except Exception as erro:
        logger.exception("Erro na LLM: %s", erro)
        resposta = ""
        texto_erro = str(erro)
        if "429" in texto_erro:
            fala_erro = "Atingi o limite grátis da inteligência artificial por agora. Tenta de novo em um minutinho."
        elif "timed out" in texto_erro.lower() or "timeout" in texto_erro.lower():
            fala_erro = "Demorei demais pra pensar nessa. Pode perguntar de novo, talvez de um jeito mais curto?"
        else:
            fala_erro = "Tive um problema pra falar com o meu cérebro na nuvem. Tenta de novo?"
        return rb.speak(fala_erro).ask(random.choice(REPROMPTS)).response

    if not resposta:
        resposta = "Hmm, fiquei sem palavras. Pode reformular?"
    _salvar_turno(handler_input, fala, resposta)

    # ask() mantém o microfone aberto: você responde SEM dizer "Alexa".
    return rb.speak(_ssml(resposta)).ask(random.choice(REPROMPTS)).response


class LaunchHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        nome = f", {config.NOME_USUARIO}" if config.NOME_USUARIO else ""
        saudacao = random.choice(
            [
                f"Oi{nome}! Sobre o que vamos conversar hoje?",
                f"E aí{nome}! Pode perguntar qualquer coisa.",
                f"Olá{nome}! Estou pronta pra conversar. O que manda?",
            ]
        )
        return handler_input.response_builder.speak(saudacao).ask(
            "Pode falar, estou ouvindo."
        ).response


class ConversaHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ConversaIntent")(handler_input)

    def handle(self, handler_input):
        return _conversar(handler_input, get_slot_value(handler_input, "texto"))


class PesquisaHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("PesquisaIntent")(handler_input)

    def handle(self, handler_input):
        consulta = get_slot_value(handler_input, "consulta")
        return _conversar(handler_input, consulta, forcar_pesquisa=True)


class AjudaHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        texto = (
            "É só conversar comigo normalmente, sem precisar dizer Alexa. "
            "Pode perguntar qualquer coisa, pedir explicações, ou dizer pesquise sobre, "
            "e o assunto, para eu buscar na internet. Para sair, diga tchau."
        )
        return handler_input.response_builder.speak(texto).ask("O que você quer saber?").response


class FallbackHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak(
            "Não entendi direito. Pode falar de outro jeito?"
        ).ask("Pode repetir?").response


class SairHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.StopIntent")(handler_input) or is_intent_name(
            "AMAZON.CancelIntent"
        )(handler_input) or is_intent_name("AMAZON.NavigateHomeIntent")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Até mais! Foi bom conversar.").set_should_end_session(
            True
        ).response


class SessaoEncerradaHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        logger.info("Sessão encerrada: %s", handler_input.request_envelope.request.reason)
        return handler_input.response_builder.response


class ErroHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.exception("Erro não tratado: %s", exception)
        return handler_input.response_builder.speak(
            "Ops, algo deu errado. Tenta de novo?"
        ).ask("Pode repetir?").response


sb = CustomSkillBuilder(api_client=DefaultApiClient())
for h in (
    LaunchHandler(),
    ConversaHandler(),
    PesquisaHandler(),
    AjudaHandler(),
    SairHandler(),
    FallbackHandler(),
    SessaoEncerradaHandler(),
):
    sb.add_request_handler(h)
sb.add_exception_handler(ErroHandler())

lambda_handler = sb.lambda_handler()
