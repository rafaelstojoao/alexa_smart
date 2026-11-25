"""Cliente para qualquer API de chat compatível com OpenAI (Groq, Gemini, OpenRouter...)."""
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import config
import pesquisa

FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "pesquisar_web",
            "description": (
                "Pesquisa na internet. Use para notícias, fatos recentes, preços, "
                "resultados de jogos, clima, pessoas, ou qualquer coisa que você não "
                "tenha certeza ou que possa ter mudado depois do seu treinamento."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "Termos de busca curtos e objetivos.",
                    }
                },
                "required": ["consulta"],
            },
        },
    }
]


def _prompt_sistema():
    agora = datetime.now(timezone(timedelta(hours=-3)))  # horário de Brasília
    nome = f" O nome do usuário é {config.NOME_USUARIO}." if config.NOME_USUARIO else ""
    return (
        "Você é uma assistente de voz brasileira, simpática, curiosa e inteligente, "
        "conversando pela Alexa." + nome + "\n"
        f"Agora são {agora:%H:%M} de {agora:%d/%m/%Y} (horário de Brasília).\n"
        "Regras, porque sua resposta será FALADA em voz alta:\n"
        "- Responda em português do Brasil, de forma natural, como numa conversa.\n"
        "- Seja breve: no máximo 3 ou 4 frases, a não ser que peçam detalhes.\n"
        "- Nunca use markdown, listas, asteriscos, emojis, tabelas ou links.\n"
        "- Escreva números e siglas de um jeito fácil de ouvir.\n"
        "- Se precisar de informação atual ou não tiver certeza, use a ferramenta pesquisar_web.\n"
        "- Quando fizer sentido, termine com uma pergunta curta para continuar o papo.\n"
        "- Você lembra do que foi dito antes nesta conversa; use esse contexto."
    )


def _chamar_api(mensagens, timeout, usar_ferramentas=True):
    corpo = {
        "model": config.LLM_MODEL,
        "messages": mensagens,
        "temperature": 0.7,
        "max_tokens": 400,
    }
    # usar_ferramentas: True (LLM decide), "none" (envia tools mas proíbe usar), False (sem tools)
    if usar_ferramentas:
        corpo["tools"] = FERRAMENTAS
        corpo["tool_choice"] = "none" if usar_ferramentas == "none" else "auto"
    if "gpt-oss" in config.LLM_MODEL:
        corpo["reasoning_effort"] = "low"  # pensa menos = responde mais rápido

    req = urllib.request.Request(
        f"{config.LLM_BASE_URL}/chat/completions",
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.LLM_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "alexa-skill-conversa/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", "ignore")[:300]
        raise RuntimeError(f"HTTP {erro.code}: {detalhe}") from erro


def limpar_para_fala(texto):
    """Remove marcações que soariam estranhas na voz."""
    texto = re.sub(r"<think>.*?</think>", "", texto or "", flags=re.S)
    texto = re.sub(r"https?://\S+", "", texto)
    texto = re.sub(r"[*_#`>|]+", "", texto)
    texto = re.sub(r"^\s*[-•]\s*", "", texto, flags=re.M)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def responder(historico, fala_usuario, ao_pesquisar=None, forcar_pesquisa=False):
    """
    historico: lista de {"role": "user"|"assistant", "content": str}
    ao_pesquisar: callback chamado antes de pesquisar (para a Alexa dizer "deixa eu ver...")
    Retorna o texto da resposta (já limpo para fala).
    """
    if not config.LLM_API_KEY:
        return "A chave da LLM não está configurada. Veja o arquivo segredos exemplo no projeto."

    inicio = time.monotonic()

    def restante():
        return config.TEMPO_MAXIMO_TOTAL - (time.monotonic() - inicio)

    mensagens = [{"role": "system", "content": _prompt_sistema()}]
    mensagens += historico[-config.MAX_HISTORICO:]
    mensagens.append({"role": "user", "content": fala_usuario})

    # Pesquisa forçada (intent "pesquise sobre ..."): busca direto, sem esperar a LLM decidir.
    if forcar_pesquisa:
        if ao_pesquisar:
            ao_pesquisar()
        resultado = pesquisa.pesquisar(fala_usuario, timeout=min(3.0, restante() - 2.5))
        mensagens[-1]["content"] = (
            f"{fala_usuario}\n\nResultados da pesquisa na web:\n{resultado}\n\n"
            "Responda com base nesses resultados."
        )
        msg = _chamar_api(mensagens, timeout=max(1.5, restante()), usar_ferramentas=False)
        return limpar_para_fala(msg.get("content"))

    msg = _chamar_api(mensagens, timeout=max(1.5, restante() - 0.5))

    chamadas = msg.get("tool_calls") or []
    if not chamadas:
        return limpar_para_fala(msg.get("content"))

    # A LLM pediu para pesquisar.
    if ao_pesquisar:
        ao_pesquisar()
    mensagens.append(
        {"role": "assistant", "content": msg.get("content") or "", "tool_calls": chamadas}
    )
    for chamada in chamadas[:2]:
        try:
            args = json.loads(chamada["function"].get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        consulta = args.get("consulta") or fala_usuario
        resultado = pesquisa.pesquisar(consulta, timeout=max(1.0, min(3.0, restante() - 2.5)))
        mensagens.append(
            {"role": "tool", "tool_call_id": chamada["id"], "content": resultado}
        )

    final = _chamar_api(mensagens, timeout=max(1.5, restante()), usar_ferramentas="none")
    return limpar_para_fala(final.get("content"))
