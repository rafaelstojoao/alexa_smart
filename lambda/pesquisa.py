"""Pesquisa na web: Tavily (se houver chave) ou Wikipédia em português (grátis, sem chave)."""
import json
import urllib.parse
import urllib.request

import config

USER_AGENT = "alexa-skill-conversa/1.0"


def _http_json(url, dados=None, timeout=3.0, headers=None):
    cabecalhos = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        cabecalhos.update(headers)
    corpo = None
    if dados is not None:
        corpo = json.dumps(dados).encode("utf-8")
        cabecalhos["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=corpo, headers=cabecalhos)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _tavily(consulta, timeout):
    dados = _http_json(
        "https://api.tavily.com/search",
        {
            "query": consulta,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 4,
        },
        timeout=timeout,
        headers={"Authorization": f"Bearer {config.TAVILY_API_KEY}"},
    )
    partes = []
    if dados.get("answer"):
        partes.append(f"Resumo: {dados['answer']}")
    for r in dados.get("results", [])[:4]:
        partes.append(f"- {r.get('title', '')}: {r.get('content', '')[:500]}")
    return "\n".join(partes)


def _wikipedia(consulta, timeout):
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": consulta,
            "srlimit": 3,
            "format": "json",
        }
    )
    busca = _http_json(f"https://pt.wikipedia.org/w/api.php?{params}", timeout=timeout)
    resultados = busca.get("query", {}).get("search", [])
    if not resultados:
        return ""
    partes = []
    for r in resultados[:2]:
        titulo = urllib.parse.quote(r["title"].replace(" ", "_"))
        try:
            resumo = _http_json(
                f"https://pt.wikipedia.org/api/rest_v1/page/summary/{titulo}",
                timeout=timeout,
            )
            partes.append(f"- {r['title']}: {resumo.get('extract', '')[:800]}")
        except Exception:
            continue
    return "\n".join(partes)


def pesquisar(consulta, timeout=3.0):
    """Retorna um texto com os resultados, ou mensagem de erro amigável para a LLM."""
    try:
        if config.TAVILY_API_KEY:
            texto = _tavily(consulta, timeout)
        else:
            texto = _wikipedia(consulta, timeout)
        return texto or "Nenhum resultado encontrado."
    except Exception as erro:  # rede, timeout, cota etc.
        return f"A pesquisa falhou ({type(erro).__name__}). Responda com o que você sabe e avise que não conseguiu confirmar."
