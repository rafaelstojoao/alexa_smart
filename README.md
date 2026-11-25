# Modo Conversa — Skill Alexa com LLM grátis

Uma skill da Alexa em português que conversa com você usando um modelo de linguagem grátis (Groq, Gemini ou OpenRouter). Ela:

- **mantém a conversa aberta**: depois de cada resposta o microfone continua ligado e você responde **sem dizer "Alexa"**;
- **lembra do contexto** da conversa (últimas 12 mensagens);
- **pesquisa na internet** quando precisa: a própria LLM decide, ou você pede com "pesquise sobre…";
- diz "deixa eu pesquisar…" enquanto busca, para não ficar em silêncio.

```
Você:  Alexa, abre modo conversa
Alexa: Oi! Sobre o que vamos conversar hoje?
Você:  Quem foi Santos Dumont?                    ← sem "Alexa"
Alexa: Foi um inventor brasileiro... Quer saber do 14-bis?
Você:  Quero                                      ← sem "Alexa"
Alexa: ...
Você:  Tchau
```

---

## 1. Antes de começar: o que é possível (e o que não é)

| Desejo | Realidade |
|---|---|
| Não falar "Alexa" toda hora | ✅ **Dentro da skill**, sim. Depois de cada resposta o microfone fica aberto uns **8 segundos**. Se você ficar calado, ela repete a pergunta ("Pode falar…") e espera mais 8 s. Depois disso a sessão fecha e você precisa dizer **"Alexa, abre modo conversa"** de novo. **Não dá** para deixar o microfone aberto para sempre: é uma regra da Amazon. |
| Respostas inteligentes | ✅ A LLM responde tudo. O prompt pede respostas curtas, boas para ouvir. |
| Pesquisas atuais | ✅ Com Tavily (grátis, com chave) ou Wikipédia (grátis, sem chave). |
| Respostas demoradas e profundas | ⚠️ A Alexa **corta a resposta se ela demorar mais de ~8 segundos**. Por isso o padrão é o Groq, que é muito rápido. |
| Falar a primeira frase sem o nome da skill | ❌ Para usar a skill você precisa invocá-la. Atalho: crie uma **Rotina** no app Alexa (ex.: "Alexa, vamos conversar" → abre a skill). Veja a seção 8. |
| Alexa entende 100% da fala livre | ⚠️ A Alexa foi feita para comandos, não para fala livre. Usamos um truque (um slot que captura tudo) que funciona bem, mas às vezes ela corta um pedaço da frase ou confunde com "parar". |

> **E a Alexa+?** A Amazon tem uma Alexa nova, com IA generativa, sendo lançada aos poucos em alguns países. Se ela já estiver no seu Echo, talvez você nem precise desta skill. Esta skill funciona em qualquer Echo e te dá controle total sobre o modelo, a personalidade e a pesquisa.

---

## 2. Estrutura do projeto

```
alexaskill/
├── lambda/                      ← código que roda na nuvem
│   ├── lambda_function.py       ← handlers da Alexa (abrir, conversar, pesquisar, sair)
│   ├── llm.py                   ← fala com a LLM; prompt; laço de pesquisa (tool calling)
│   ├── pesquisa.py              ← pesquisa web: Tavily ou Wikipédia
│   ├── config.py                ← lê as chaves (variáveis de ambiente ou segredos.py)
│   ├── segredos_exemplo.py      ← modelo do arquivo de chaves
│   └── requirements.txt
├── skill-package/
│   ├── skill.json               ← manifesto (nome, descrição, país)
│   └── interactionModels/custom/pt-BR.json   ← modelo de interação (o que a Alexa entende)
└── scripts/
    └── chat_local.py            ← testa a conversa no terminal, sem Alexa
```

---

## 3. Contas e chaves (tudo grátis)

### 3.1 Amazon Developer (obrigatório)
1. Acesse <https://developer.amazon.com/alexa/console/ask>.
2. Entre com **a mesma conta Amazon do seu Echo**. Isso é importante: é assim que a skill aparece no seu dispositivo sem publicar.

### 3.2 LLM grátis (escolha um)

| Provedor | Por que | Onde pegar a chave | `LLM_BASE_URL` |
|---|---|---|---|
| **Groq** (recomendado) | Muito rápido, cabe nos 8 s da Alexa. Plano grátis sem cartão. | <https://console.groq.com/keys> | `https://api.groq.com/openai/v1` |
| **Google Gemini** | Plano grátis generoso, bom em português. Os dados do plano grátis podem ser usados pelo Google. | <https://aistudio.google.com/apikey> | `https://generativelanguage.googleapis.com/v1beta/openai` |
| **OpenRouter** | Vários modelos `:free`. Mais lento e instável. | <https://openrouter.ai/keys> | `https://openrouter.ai/api/v1` |

**Nomes de modelos mudam com frequência.** Para ver os modelos que a sua chave tem agora, rode:
```bash
python3 scripts/chat_local.py --modelos
```
Escolha um modelo que **aceite tool calling** (chamada de ferramentas), senão a pesquisa automática não funciona. O padrão do projeto é `openai/gpt-oss-120b` no Groq. Se ele estiver lento, teste `openai/gpt-oss-20b` ou um modelo Llama/Qwen da lista.

Os limites grátis (requisições por minuto e por dia) variam por modelo. Para uso pessoal, sobra.

### 3.3 Pesquisa na web (opcional)
- **Tavily**: <https://app.tavily.com>. Plano grátis com cota mensal, resultados de notícias e fatos atuais.
- **Sem chave**: a skill usa a **Wikipédia em português**. Funciona para fatos e biografias, mas não para notícias de hoje.

---

## 4. Testar no computador primeiro (5 minutos)

Teste a conversa no terminal **antes** de mexer na Alexa. Assim você confirma que a chave, o modelo e a velocidade estão ok.

```bash
cp lambda/segredos_exemplo.py lambda/segredos.py
# edite lambda/segredos.py e cole sua chave em LLM_API_KEY

python3 scripts/chat_local.py
```

O script mostra quanto tempo cada resposta levou. Se passar de **8 s**, a Alexa vai falhar: troque por um modelo mais rápido.

> O `segredos.py` está no `.gitignore`. **Nunca suba suas chaves para o GitHub.**

---

## 5. Criar a skill na Alexa (Alexa-hosted, grátis, sem conta AWS)

### 5.1 Criar
1. No console: **Create Skill**.
2. **Name**: `Modo Conversa`. **Primary locale**: **Portuguese (BR)**.
3. **Experience**: *Other*. **Model**: **Custom**. **Hosting**: **Alexa-hosted (Python)**. Região: *US East (N. Virginia)*, que tem menor latência para o Brasil.
4. Template: **Start from Scratch**. Clique em **Create Skill** e espere ~1 minuto.

### 5.2 Modelo de interação (o que a Alexa entende)
1. Aba **Build** → menu esquerdo **Interaction Model** → **JSON Editor**.
2. Apague tudo e cole o conteúdo de [skill-package/interactionModels/custom/pt-BR.json](skill-package/interactionModels/custom/pt-BR.json).
3. **Save** e depois **Build skill**. Espere aparecer "Build Successful".

O que tem nele:
- **Nome de invocação**: `modo conversa` (troque se quiser; precisa ter 2 palavras ou mais e não pode ter "Alexa").
- **`ConversaIntent`** com o slot `{texto}` do tipo `TEXTO_LIVRE`. É o truque do **"pega-tudo"**: como a Alexa aceita valores fora da lista em slots personalizados, qualquer frase cai aqui e vai para a LLM. Os ~55 exemplos ensinam a Alexa que o slot pode ter frases longas e variadas.
- **`PesquisaIntent`** ("pesquise sobre…", "procure…", "notícias sobre…"): força uma busca na web.
- **`AMAZON.StopIntent`** com "tchau", "chega", "até mais" para sair.

### 5.3 Código
1. Aba **Code**.
2. Substitua o conteúdo de `lambda_function.py` e `requirements.txt` pelos arquivos deste repositório.
3. Crie os arquivos `llm.py`, `pesquisa.py` e `config.py` (botão de novo arquivo, dentro da pasta `lambda`) e cole o conteúdo.
4. Crie **`segredos.py`** e cole suas chaves (como no `segredos_exemplo.py`).
   *Skills Alexa-hosted não deixam configurar variáveis de ambiente pelo console. Por isso usamos esse arquivo. O código no console é privado e fica só na sua conta.*
5. **Save** e depois **Deploy**.

### 5.4 Testar no simulador
1. Aba **Test** → mude "Off" para **Development**.
2. Digite ou fale: `abre modo conversa`, depois `por que o céu é azul`, depois `me conta mais`.
3. Se der erro: aba **Code** → **CloudWatch Logs** mostra o motivo (chave errada, modelo inexistente, timeout…).

### 5.5 Usar no seu Echo
Pronto, já está lá. Skills em modo **Development** ficam ativas em todos os dispositivos da sua conta. Não precisa publicar.
- O idioma do Echo precisa ser **Português (Brasil)** (app Alexa → Dispositivos → seu Echo → Idioma).
- Diga: **"Alexa, abre modo conversa"**.

---

## 6. Como a conversa fluida funciona (por dentro)

```
Você fala ─► Alexa (voz→texto) ─► ConversaIntent{texto} ─► Lambda
                                                            │
                     histórico da sessão (sessionAttributes)┤
                                                            ▼
                                             LLM (Groq/Gemini) ── quer pesquisar? ──► Tavily / Wikipédia
                                                            │      (Alexa diz "deixa eu pesquisar")
                                                            ▼
                         resposta + reprompt + shouldEndSession=false
                                                            │
Alexa fala a resposta ◄─────────────────────────────────────┘
e reabre o microfone  ◄── você responde sem "Alexa"
```

Os pontos principais do código:

- **Microfone aberto**: `response_builder.speak(...).ask(reprompt)` em [lambda_function.py](lambda/lambda_function.py). O `.ask()` mantém a sessão viva.
- **Memória**: o histórico vai em `session_attributes["historico"]` e volta a cada turno. Ele some quando a sessão fecha.
- **Pesquisa**: a LLM recebe a ferramenta `pesquisar_web` (tool calling). Se ela chamar, o código busca, devolve o resultado e pede a resposta final ([llm.py](lambda/llm.py)).
- **Resposta progressiva**: a API *Progressive Response* faz a Alexa falar "um segundinho…" enquanto pesquisa.
- **Controle de tempo**: as duas chamadas da LLM e a busca dividem um orçamento de 7 s (`TEMPO_MAXIMO_TOTAL`).
- **Texto para voz**: o código remove markdown, links e listas, e escapa caracteres de SSML (`&`, `<`).

---

## 7. Personalizar

| O quê | Onde |
|---|---|
| Personalidade, tamanho das respostas, regras | `_prompt_sistema()` em [lambda/llm.py](lambda/llm.py) |
| Te chamar pelo nome | `NOME_USUARIO` no `segredos.py` |
| Trocar de LLM | `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` no `segredos.py` |
| Quantas mensagens lembrar | `MAX_HISTORICO` |
| Nome para chamar a skill | `invocationName` no JSON do modelo de interação, depois Build |
| Frases de saudação e de "pesquisando" | listas em [lambda/lambda_function.py](lambda/lambda_function.py) |
| Voz diferente | troque `_ssml()` para envolver o texto em `<voice name="Ricardo">…</voice>` (vozes Polly pt-BR: Camila, Vitória, Ricardo, Thiago) |

### Ideias de evolução
- **Memória permanente** (lembrar de você entre conversas): skills Alexa-hosted vêm com uma tabela DynamoDB grátis. Use `ask-sdk-dynamodb-persistence-adapter` e salve um resumo da conversa ao encerrar.
- **Mais ferramentas** para a LLM: clima (Open-Meteo, grátis e sem chave), cotação (AwesomeAPI), lembretes (Reminders API da Alexa), controle de casa via webhook.
- **Rotina de bom dia**: Rotina no app Alexa → "abre modo conversa" e um prompt que comece com as notícias do dia.

---

## 8. Atalho: abrir a conversa com uma frase natural

App Alexa → **Mais** → **Rotinas** → **+**
- **Quando**: Voz → "Alexa, **vamos conversar**"
- **Ação**: *Skills* → *Suas skills* → **Modo Conversa** (se não aparecer, use *Personalizado* → digite `abre modo conversa`).

Também funciona em uma frase só: **"Alexa, pergunta ao modo conversa quanto tempo leva pra chegar em Marte"**.

---

## 9. Problemas comuns

| Sintoma | Causa provável / solução |
|---|---|
| "Houve um problema com a resposta da skill solicitada" | Erro no código ou demora acima de 8 s. Veja os **CloudWatch Logs**. Teste no `chat_local.py`. |
| "A chave da LLM não está configurada" | Falta o `segredos.py` na aba Code, ou você não clicou em **Deploy**. |
| `HTTP 404` / `model not found` nos logs | Nome do modelo mudou. Rode `chat_local.py --modelos`. |
| `HTTP 400` falando de tools | O modelo não aceita tool calling. Troque de modelo. |
| `HTTP 429` | Limite grátis atingido. Espere ou troque de modelo ou provedor. |
| Ela corta minha frase ou responde algo sem sentido | Limite do reconhecimento livre da Alexa. Fale frases completas. Adicione exemplos parecidos com o que você fala em `TEXTO_LIVRE` e faça o Build. |
| Diz "não sei" para notícias de hoje | Configure o `TAVILY_API_KEY` (a Wikipédia não tem notícias) ou diga "pesquise sobre…". |
| A sessão fecha rápido | Normal: ~8 s de silêncio + reprompt + ~8 s. Responda logo depois que ela terminar de falar. |
| A skill não aparece no Echo | Conta Amazon diferente da do console, idioma do Echo diferente de pt-BR, ou o teste não está em **Development**. |

---

## 10. Alternativa: ASK CLI + GitHub (para quem prefere terminal)

```bash
npm install -g ask-cli
ask configure                       # login na conta Amazon Developer
# Crie a skill Alexa-hosted no console (passo 5.1) e copie o Skill ID.
ask init --hosted-skill-id amzn1.ask.skill.XXXX
# Copie lambda/ e skill-package/ deste repo para a pasta clonada e então:
git add . && git commit -m "skill" && git push    # o push faz deploy automático
```
O `segredos.py` fica de fora do GitHub (por causa do `.gitignore`), mas precisa existir no repositório da Alexa-hosted. Crie-o pelo console (aba Code) ou faça commit dele **somente** no remoto da Alexa, nunca no GitHub.

**Lambda própria na AWS**: se preferir, crie uma função Lambda Python 3.12 com gatilho "Alexa Skills Kit", defina `LLM_API_KEY` etc. como **variáveis de ambiente** (aí o `segredos.py` não é necessário), coloque o timeout em 10 s e aponte o *Endpoint* da skill para o ARN da função.
