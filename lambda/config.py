"""Lê configurações de variáveis de ambiente, com fallback para segredos.py."""
import os

try:
    import segredos  # arquivo local, fora do git
except ImportError:  # pragma: no cover
    segredos = None


def _get(nome, padrao=""):
    valor = os.environ.get(nome)
    if valor:
        return valor
    if segredos is not None and getattr(segredos, nome, None):
        return getattr(segredos, nome)
    return padrao


LLM_BASE_URL = _get("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
LLM_API_KEY = _get("LLM_API_KEY")
LLM_MODEL = _get("LLM_MODEL", "openai/gpt-oss-120b")
TAVILY_API_KEY = _get("TAVILY_API_KEY")
NOME_USUARIO = _get("NOME_USUARIO")

# A Alexa espera a resposta em ~8 segundos. Deixamos margem.
TEMPO_MAXIMO_TOTAL = float(_get("TEMPO_MAXIMO_TOTAL", "7.0"))
# Quantas mensagens (usuário + assistente) manter como memória da conversa.
MAX_HISTORICO = int(_get("MAX_HISTORICO", "12"))
