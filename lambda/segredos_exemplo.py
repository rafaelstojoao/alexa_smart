# Copie este arquivo para "segredos.py" (na mesma pasta) e preencha.
# O segredos.py está no .gitignore e não vai para o GitHub.
# Variáveis de ambiente com o mesmo nome têm prioridade sobre este arquivo.

# --- LLM (qualquer API compatível com OpenAI) ---
# Groq (grátis, muito rápido -> recomendado por causa do limite de 8s da Alexa)
LLM_BASE_URL = "https://api.groq.com/openai/v1"
LLM_API_KEY = "gsk_COLE_SUA_CHAVE_AQUI"
LLM_MODEL = "openai/gpt-oss-120b"

# Alternativa: Google Gemini (grátis via AI Studio)
# LLM_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
# LLM_API_KEY = "COLE_SUA_CHAVE_DO_AI_STUDIO"
# LLM_MODEL = "gemini-3.5-flash"   # confira o nome atual na lista de modelos

# Alternativa: OpenRouter (modelos terminados em ":free")
# LLM_BASE_URL = "https://openrouter.ai/api/v1"
# LLM_API_KEY = "sk-or-..."
# LLM_MODEL = "algum-modelo:free"

# --- Pesquisa na web (opcional) ---
# Tavily tem plano grátis mensal. Sem chave, a skill usa a Wikipédia.
TAVILY_API_KEY = ""

# --- Personalização ---
NOME_USUARIO = ""   # ex.: "Rafael" — a assistente vai te chamar pelo nome
