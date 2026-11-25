"""
Conversa com a mesma lógica da skill, direto no terminal (sem Alexa).
Serve para testar chave da API, modelo, pesquisa e tempo de resposta.

Uso:
    python3 scripts/chat_local.py            # conversa
    python3 scripts/chat_local.py --modelos  # lista os modelos disponíveis na sua chave
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda"))

import config  # noqa: E402
import llm  # noqa: E402


def listar_modelos():
    req = urllib.request.Request(
        f"{config.LLM_BASE_URL}/models",
        headers={"Authorization": f"Bearer {config.LLM_API_KEY}", "User-Agent": "alexa-skill-conversa/1.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        dados = json.loads(resp.read())
    for m in sorted(x["id"] for x in dados.get("data", [])):
        print(m)


def main():
    if "--modelos" in sys.argv:
        listar_modelos()
        return
    print(f"Modelo: {config.LLM_MODEL} @ {config.LLM_BASE_URL}")
    print(f"Pesquisa: {'Tavily' if config.TAVILY_API_KEY else 'Wikipédia'}")
    print("Digite sua mensagem (Ctrl+C ou 'tchau' para sair).\n")
    historico = []
    while True:
        try:
            fala = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not fala:
            continue
        if fala.lower() in {"tchau", "sair"}:
            break
        forcar = fala.lower().startswith(("pesquise ", "pesquisa "))
        t0 = time.monotonic()
        resposta = llm.responder(
            historico,
            fala,
            ao_pesquisar=lambda: print("  (pesquisando...)"),
            forcar_pesquisa=forcar,
        )
        dt = time.monotonic() - t0
        aviso = "  <-- ACIMA DO LIMITE DA ALEXA (8s)!" if dt > 8 else ""
        print(f"Alexa: {resposta}\n  [{dt:.1f}s]{aviso}\n")
        historico += [{"role": "user", "content": fala}, {"role": "assistant", "content": resposta}]


if __name__ == "__main__":
    main()
