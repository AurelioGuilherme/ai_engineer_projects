import os
from datetime import datetime
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from dotenv import load_dotenv
from groq import Groq
from langfuse import observe

from src.agents.news_agent import news_agent_func

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa o cliente Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Diretório de saída dos relatórios
OUTPUT_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _plot_series(series_records, x_key, y_key, outpath, title):
    """Gera e salva um gráfico de linha a partir de uma série temporal."""
    df = pd.DataFrame(series_records)
    df[x_key] = pd.to_datetime(df[x_key])

    # Configurações do gráfico
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 4))
    sns.lineplot(data=df, x=x_key, y=y_key, marker="o")
    plt.title(title)
    plt.xlabel("")
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()

    return outpath


@observe(name="Groq_Metrics_Analysis")
def _analyze_metrics_with_groq(metrics: dict, task: str) -> str:
    """Gera uma interpretação textual das métricas usando Groq."""

    # Prompts para tarefa inicial com 12 meses de dados para gerar contexto
    system_prompt_summary = """
    Você é um especialista em epidemiologia e análise de dados em saúde
    pública.
    Explique o que significam as métricas fornecidas e o que sugerem sobre a
    situação epidemiológica atual da SRAG.
    Seja claro, objetivo e técnico, sem especulações.
    """

    # Prompt para análise detalhada de todas as métricas
    system_prompt_all_metrics = """
    Você é um especialista em epidemiologia e análise de dados em saúde
    pública.
    Analise detalhadamente todas as métricas fornecidas, identificando
    tendências, padrões e possíveis implicações para a saúde pública.

    É preciso que forneça os detalhes referente a cada métrica, relacionando-as
    entre si quando possível.
    """

    # Prompt do usuário com as métricas em formato JSON.
    user_prompt = f"Métricas obtidas: {metrics}"

    # Task de análise específica de 12 meses
    if task == "summary":
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt_summary},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )

    # Task de análise detalhada de todas as métricas
    elif task == "All_metrics_analysis":
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt_all_metrics},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
    return response.choices[0].message.content.strip()


@observe(name="ReportAggent")
def report_agent_func(context: Dict) -> Dict:
    """
    Gera relatório Markdown com:
    - métricas e análise via Groq
    - gráficos
    - resumo e análise de notícias via Groq - web search
    """
    metrics = context.get("metrics", {})
    daily = context.get("daily_cases", [])
    monthly = context.get("monthly_cases", [])

    # séries adicionais
    monthly_all = context.get("monthly_cases_all", [])
    # monthly_deaths = context.get("monthly_deaths", [])
    # monthly_vacc_covid = context.get("monthly_vaccination_covid", [])
    # monthly_vacc_gripe = context.get("monthly_vaccination_gripe", [])
    monthly_sex = context.get("monthly_cases_by_sex", [])
    # monthly_uti = context.get("monthly_uti_occupation", [])
    # monthly_classificacao = context.get("monthly_classificacao", [])
    # monthly_desfecho = context.get("monthly_desfecho", [])
    # monthly_uf = context.get("monthly_cases_by_uf", [])

    full_context_for_ai = {
        "metrics": metrics,
        # "daily_cases": daily,
        # "monthly_cases": monthly,
        "monthly_cases_all": monthly_all,
        # "monthly_deaths": monthly_deaths,
        # "monthly_vaccination_covid": monthly_vacc_covid,
        # "monthly_vaccination_gripe": monthly_vacc_gripe,
        "monthly_cases_by_sex": monthly_sex,
        # "monthly_uti_occupation": monthly_uti,
        # "monthly_classificacao": monthly_classificacao,
        # "monthly_desfecho": monthly_desfecho,
        # "monthly_cases_by_uf": monthly_uf
    }

    # Busca e interpretar notícias
    print("Buscando notícias recentes sobre SRAG...")
    news_context = {
        "news_query": "Síndrome Respiratória Aguda Grave OR SRAG OR surtos respiratórios Brasil 2025"
    }
    news_data = news_agent_func(news_context)

    news_summary = news_data.get("news_summary", "")
    sources = news_data.get("sources", [])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(OUTPUT_DIR, f"relatorio_srag_{timestamp}.md")

    # Gera análise das métricas com IA de 12 meses
    metrics_analysis = _analyze_metrics_with_groq(metrics, task="summary")  # noqa: F841
    all_metrics_analysis = _analyze_metrics_with_groq(
        full_context_for_ai, task="All_metrics_analysis"
    )

    # Gráficos
    daily_img = _plot_series(
        daily,
        "date",
        "cases",
        os.path.join(OUTPUT_DIR, f"daily_{timestamp}.png"),
        "Casos diários (últimos 30 dias)",
    )
    monthly_img = _plot_series(
        monthly,
        "month",
        "cases",
        os.path.join(OUTPUT_DIR, f"monthly_{timestamp}.png"),
        "Casos mensais (últimos 12 meses)",
    )

    # Construção do relatório Markdown
    md = []
    md.append("# Relatório Epidemiológico — SRAG\n")
    md.append(f"**Gerado em:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

    md.append("## Métricas e Análise\n")
    md.append(f"{all_metrics_analysis}\n\n")

    md.append("## Gráficos\n")
    if daily_img:
        md.append(f"![Casos diários]({os.path.basename(daily_img)})\n")
    if monthly_img:
        md.append(f"![Casos mensais]({os.path.basename(monthly_img)})\n")

    # Notícias e análise
    md.append("\n## Notícias recentes e contexto\n")
    md.append(f"{news_summary}\n\n")

    md.append("\n## Observações gerais\n")
    md.append("- Dados provenientes do Open DATASUS.\n")
    md.append("- Notícias obtidas via busca em tempo real com o modelo `groq/compound`.\n")
    md.append("- Este relatório foi gerado automaticamente por agentes de IA.\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return {
        "report_path": report_path,
        "daily_img": daily_img,
        "monthly_img": monthly_img,
        "news_summary": news_summary,
        "sources": sources,
    }
