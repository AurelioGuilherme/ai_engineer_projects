import os
from typing import Any, Dict

import pandas as pd

from src.tools.sql_tool import query_sqlite

# Caminho padrão do DB
DB_PATH = os.path.join(os.getcwd(), "srag.db")


def _daily_series_last_30(db_path):
    """Retorna série diária dos últimos 30 dias."""
    sql = """
    SELECT DATA_NOTIFICACAO as date, COUNT(*) as cases
    FROM srag_casos
    WHERE DATA_NOTIFICACAO IS NOT NULL
    GROUP BY DATA_NOTIFICACAO
    ORDER BY DATA_NOTIFICACAO DESC
    LIMIT 30
    """
    df = query_sqlite(db_path, sql)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


def _monthly_cases_series_last_12(db_path):
    """Retorna série de casos mensais dos últimos 12 meses."""
    sql = """
    SELECT strftime('%Y-%m', DATA_NOTIFICACAO) as month, COUNT(*) as cases
    FROM srag_casos
    WHERE DATA_NOTIFICACAO IS NOT NULL
    GROUP BY month
    ORDER BY month DESC
    LIMIT 12
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _monthly_cases_series(db_path):
    """Retorna série de casos mensais"""
    sql = """
    SELECT strftime('%Y-%m', DATA_NOTIFICACAO) as month, COUNT(*) as cases
    FROM srag_casos
    WHERE DATA_NOTIFICACAO IS NOT NULL
    GROUP BY month
    ORDER BY month DESC
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _monthly_deaths_series(db_path):
    """Retorna série de óbitos mensais"""
    sql = """
    SELECT strftime('%Y-%m', DATA_NOTIFICACAO) as month,
           SUM(CASE WHEN DESFECHO = 'Óbito' THEN 1 ELSE 0 END) as deaths
    FROM srag_casos
    WHERE DATA_NOTIFICACAO IS NOT NULL
    GROUP BY month
    ORDER BY month DESC
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _monthly_vaccination_covid_series(db_path):
    """Retorna série de vacinação COVID mensais"""
    sql = """
    SELECT strftime('%Y-%m', DATA_NOTIFICACAO) as month,
           SUM(CASE WHEN VACINADO_COVID = 'Sim' THEN 1 ELSE 0 END) as vaccinated
    FROM srag_casos
    WHERE DATA_NOTIFICACAO IS NOT NULL
    GROUP BY month
    ORDER BY month DESC
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _monthly_vaccination_gripe_series(db_path):
    """Retorna série de vacinação GRIPE mensais"""
    sql = """
    SELECT strftime('%Y-%m', DATA_NOTIFICACAO) as month,
           SUM(CASE WHEN VACINADO_GRIPE = 'Sim' THEN 1 ELSE 0 END) as vaccinated
    FROM srag_casos
    WHERE DATA_NOTIFICACAO IS NOT NULL
    GROUP BY month
    ORDER BY month DESC
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _monthly_case_pacient_sex(db_path):
    """Retorna série mensal de casos por sexo do paciente"""
    sql = """
      SELECT strftime('%Y-%m', DATA_NOTIFICACAO) as month,
         SUM(CASE WHEN "SEXO_PACIENTE" = 'Masculino' THEN 1 ELSE 0 END) as count_homens,
         SUM(CASE WHEN "SEXO_PACIENTE" = 'Feminino' THEN 1 ELSE 0 END) as count_mulheres
      FROM srag_casos
      WHERE DATA_NOTIFICACAO IS NOT NULL
      GROUP BY month
      ORDER BY month DESC
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _monthly_uti_occupation_series(db_path):
    """Retorna série mensal de ocupação de UTI"""
    sql = """
      SELECT strftime('%Y-%m', DATA_NOTIFICACAO) as month,
             SUM(CASE WHEN INTERNADO_UTI = 'Sim' THEN 1 ELSE 0 END) as uti_occupied
      FROM srag_casos
      WHERE DATA_NOTIFICACAO IS NOT NULL
      GROUP BY month
      ORDER BY month DESC
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _monthly_categorical_distribution_series(db_path):
    """Retorna série mensal de distribuição de categoria de srag."""
    sql = """
      SELECT
          CLASSIFICACAO_FINAL,
          strftime('%Y-%m', DATA_NOTIFICACAO) AS month,
          COUNT(*) AS total_casos
      FROM srag_casos
      GROUP BY CLASSIFICACAO_FINAL, month
      ORDER BY month, total_casos DESC;
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _monthly_case_results_distribution_series(db_path):
    """Retorna série mensal de distribuição de desfecho dos casos."""
    sql = """
      SELECT
          DESFECHO,
          strftime('%Y-%m', DATA_NOTIFICACAO) AS month,
          COUNT(*) AS total_casos
      FROM srag_casos
      GROUP BY DESFECHO, month
      ORDER BY month, total_casos DESC;
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _monthly_cases_by_uf_series(db_path):
    """Retorna série mensal de casos por UF."""
    sql = """
      SELECT
          UF,
          strftime('%Y-%m', DATA_NOTIFICACAO) AS month,
          COUNT(*) AS total_casos
      FROM srag_casos
      GROUP BY UF, month
      ORDER BY month, total_casos DESC;
    """
    df = query_sqlite(db_path, sql)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")
    return df


def _compute_metrics(db_path) -> Dict[str, Any]:
    """Computa métricas principais a partir do DB."""
    sql_last_14 = """
    SELECT
      DATA_NOTIFICACAO as date, COUNT(*) as cases
    FROM srag_casos
    WHERE DATA_NOTIFICACAO IS NOT NULL
    GROUP BY DATA_NOTIFICACAO
    ORDER BY DATA_NOTIFICACAO DESC
    LIMIT 14
    """

    # taxa de aumento: (sum últimos 7 dias)/(sum 7 dias anteriores) - 1
    df14 = query_sqlite(db_path, sql_last_14)
    df14["date"] = pd.to_datetime(df14["date"])
    df14 = df14.sort_values("date")
    last7 = df14["cases"].tail(7).sum() if len(df14) >= 7 else df14["cases"].sum()
    prev7 = df14["cases"].head(7).sum() if len(df14) >= 14 else 0

    taxa_aumento = ((last7 - prev7) / prev7 * 100) if prev7 > 0 else None

    # taxa de mortalidade
    sql_mortalidade = """
    SELECT
      SUM(CASE WHEN DESFECHO = 'Óbito' THEN 1 ELSE 0 END) as deaths,
      COUNT(*) as total
    FROM srag_casos
    """
    dfm = query_sqlite(db_path, sql_mortalidade)
    deaths = int(dfm.at[0, "deaths"])
    total = int(dfm.at[0, "total"])
    taxa_mortalidade = (deaths / total * 100) if total > 0 else None

    # taxa ocupacao UTI
    sql_uti = """
    SELECT
      SUM(CASE WHEN INTERNADO_UTI = 'Sim' THEN 1 ELSE 0 END) as uti,
      COUNT(*) as total
    FROM srag_casos
    """
    dfu = query_sqlite(db_path, sql_uti)
    uti = int(dfu.at[0, "uti"])
    total2 = int(dfu.at[0, "total"])
    taxa_uti = (uti / total2 * 100) if total2 > 0 else None

    # taxa de vacinação (COVID): proporção VACINADO_COVID == 'Sim'
    sql_vac = """
    SELECT
      SUM(CASE WHEN VACINADO_COVID = 'Sim' THEN 1 ELSE 0 END) as vac,
      COUNT(*) as total
    FROM srag_casos
    """
    dfv = query_sqlite(db_path, sql_vac)
    vac = int(dfv.at[0, "vac"])
    total3 = int(dfv.at[0, "total"])
    taxa_vacinacao = (vac / total3 * 100) if total3 > 0 else None

    return {
        "taxa_aumento_percent": taxa_aumento,
        "taxa_mortalidade_percent": taxa_mortalidade,
        "taxa_uti_percent": taxa_uti,
        "taxa_vacinacao_percent": taxa_vacinacao,
        "counts": {"deaths": deaths, "total": total},
    }


def data_agent_func(context: Dict) -> Dict:
    """
    Agent que consulta o DB e retorna métricas e séries para o relatório.
    Retorna dict que será mesclado no contexto.
    """
    db_path = context.get("db_path", DB_PATH)

    # séries básicas
    daily = _daily_series_last_30(db_path)
    monthly = _monthly_cases_series_last_12(db_path)

    # séries adicionais
    monthly_all = _monthly_cases_series(db_path)
    # monthly_deaths = _monthly_deaths_series(db_path)
    # monthly_vacc_covid = _monthly_vaccination_covid_series(db_path)
    # monthly_vacc_gripe = _monthly_vaccination_gripe_series(db_path)
    monthly_sex = _monthly_case_pacient_sex(db_path)
    # monthly_uti = _monthly_uti_occupation_series(db_path)
    # monthly_classificacao = _monthly_categorical_distribution_series(db_path)
    # monthly_desfecho = _monthly_case_results_distribution_series(db_path)
    # monthly_uf = _monthly_cases_by_uf_series(db_path)

    # métricas gerais
    metrics = _compute_metrics(db_path)

    # Atualiza contexto da Crew com os dados extraídos
    context_update = {
        "daily_cases": daily.to_dict(orient="records"),
        "monthly_cases": monthly.to_dict(orient="records"),
        # novas métricas integradas
        "monthly_cases_all": monthly_all.to_dict(orient="records"),
        # "monthly_deaths": monthly_deaths.to_dict(orient='records'),
        # "monthly_vaccination_covid": monthly_vacc_covid.to_dict(orient='records'),
        # "monthly_vaccination_gripe": monthly_vacc_gripe.to_dict(orient='records'),
        "monthly_cases_by_sex": monthly_sex.to_dict(orient="records"),
        # "monthly_uti_occupation": monthly_uti.to_dict(orient='records'),
        # "monthly_classificacao": monthly_classificacao.to_dict(orient='records'),
        # "monthly_desfecho": monthly_desfecho.to_dict(orient='records'),
        # "monthly_cases_by_uf": monthly_uf.to_dict(orient='records'),
        # métricas principais
        "metrics": metrics,
    }

    return context_update
