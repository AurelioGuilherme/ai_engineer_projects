import os
from typing import Dict

from dotenv import load_dotenv
from groq import Groq
from langfuse import observe

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@observe(name="NewsAgent")
def news_agent_func(context: Dict) -> Dict:
    """
    Agente responsável por buscar e interpretar notícias recentes sobre SRAG.
    Usa o modelo 'groq/compound' com web search.
    """

    query = context.get(
        "news_query", "Síndrome Respiratória Aguda Grave OR SRAG OR surtos respiratórios"
    )

    system_prompt = """
        Você é um analista de saúde pública com foco em epidemiologia e
        comunicação técnica.

        Sua tarefa é analisar as informações mais recentes sobre SRAG
        (Síndrome Respiratória Aguda Grave)
        e produzir um relatório conciso e técnico contendo:
        - Principais fatos e tendências recentes (alta, queda ou estabilidade de casos)
        - Fatores mencionados (vacinação, hospitalizações, taxa de UTI)
        - Contextualização com base nas fontes (sem copiar diretamente)
        - Linguagem neutra, voltada a relatórios institucionais
    """

    user_prompt = f"""
        Busque e analise as notícias mais recentes sobre: {query}.
        Gere um parágrafo analítico com citações das fontes com link completo
        e preciso.

        exemplo de formatação do output:
        A analise das informações recentes sobre a Síndrome Respiratória Aguda
        Grave (SRAG) no Brasil indicam... Vários fatores contribuem para essa
        tendência, incluindo...

        Segundo as fontes do Jornal X [1] houve um crescimento de X% nos casos
        de SRAG... Os dados do governo federal [2] mostram que a taxa de
        ocupação de UTIs atingiu X%... Segundo a reportagem do Jornal X[1]...

        [1] Nome do jornal X – “Titulo da noticia”,
        URL: https://www.jornalx.com/noticia-srag

        [2] Governo Federal – “Titulo do boletim", Data da noticia por extenso
        URL: https://www.gov.br/boletim-srag
    """

    # Chama o modelo Groq com capacidade de busca na web
    response = client.chat.completions.create(
        model="groq/compound",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    # Extrai o conteúdo da resposta do modelo
    message = response.choices[0].message
    content = message.content.strip()

    # Extrai URLs das ferramentas executadas (web search)
    sources = []
    if getattr(message, "executed_tools", None):
        for tool in message.executed_tools:
            for res in tool.search_results:
                if isinstance(res, dict):
                    sources.append(res.get("url") or res.get("source") or "")
                elif isinstance(res, (list, tuple)) and len(res) > 0:
                    sources.append(res[0])

    return {
        "news_summary": content,
        "sources": sources,
    }
