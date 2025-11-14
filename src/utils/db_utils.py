import os
import sqlite3

import pandas as pd

# ===== CAMINHOS E CONSTANTES =====
DATA_DIR = os.path.join("data", "srag_csvs")
DB_PATH = "srag.db"
TABELA = "srag_casos"
BATCH_SIZE = 200000

# ===== DICIONÁRIOS DE MAPEAMENTO =====
MAP_SEXO = {"M": "Masculino", "F": "Feminino", "I": "Ignorado"}

MAP_EVOLUCAO = {1: "Cura", 2: "Óbito", 3: "Óbito por outras causas", 9: "Ignorado"}

MAP_CLAS_FIN = {
    1: "SRAG por Influenza",
    2: "SRAG por outro vírus respiratório",
    3: "SRAG por outro agente etiológico",
    4: "SRAG não especificado",
    5: "SRAG por COVID-19",
}

MAP_UTI = {1: "Sim", 2: "Não", 9: "Ignorado"}

MAP_VACINA_COV = {1: "Sim", 2: "Não", 9: "Ignorado"}
MAP_VACINA_GRIPE = {1: "Sim", 2: "Não", 9: "Ignorado"}


def cria_tabela(con):
    """Cria a tabela principal se não existir, com PRIMARY KEY."""
    cur = con.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABELA} (
            NUMERO_DA_NOTIFICACAO INTEGER PRIMARY KEY,
            DATA_NOTIFICACAO DATE,
            SEXO_PACIENTE TEXT,
            DESFECHO TEXT,
            CLASSIFICACAO_FINAL TEXT,
            INTERNADO_UTI TEXT,
            VACINADO_COVID TEXT,
            VACINADO_GRIPE TEXT,
            UF TEXT
        )
    """)
    cur.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_data_notificacao
        ON {TABELA} (DATA_NOTIFICACAO);
    """)
    con.commit()


def preparar_batch(df):
    """Seleciona, renomeia, tipa e traduz colunas."""

    # Colunas que esperamos do CSV original
    colunas_interesse = [
        "NU_NOTIFIC",
        "DT_NOTIFIC",
        "CS_SEXO",
        "EVOLUCAO",
        "CLASSI_FIN",
        "UTI",
        "VACINA_COV",
        "VACINA",
        "SG_UF",
    ]

    df_filtrado = df[colunas_interesse].copy()
    # Renomeia colunas
    df_filtrado.rename(
        columns={
            "NU_NOTIFIC": "NUMERO_DA_NOTIFICACAO",
            "DT_NOTIFIC": "DATA_NOTIFICACAO",
            "CS_SEXO": "SEXO_PACIENTE",
            "EVOLUCAO": "DESFECHO",
            "CLASSI_FIN": "CLASSIFICACAO_FINAL",
            "UTI": "INTERNADO_UTI",
            "VACINA_COV": "VACINADO_COVID",
            "VACINA": "VACINADO_GRIPE",
            "SG_UF": "UF",
        },
        inplace=True,
    )

    # --- Tipagem e Conversão ---

    # 1. Tipagem numérica do ID (Chave Primária)
    df_filtrado["NUMERO_DA_NOTIFICACAO"] = pd.to_numeric(
        df_filtrado["NUMERO_DA_NOTIFICACAO"], errors="coerce"
    ).astype("Int64")

    # 2. Conversão de datas
    df_filtrado["DATA_NOTIFICACAO"] = pd.to_datetime(
        df_filtrado["DATA_NOTIFICACAO"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    # 3. Preenchimento de NaNs em colunas categóricas com valores padrão
    df_filtrado.fillna(
        {
            "VACINADO_COVID": 9,
            "VACINADO_GRIPE": 9,
            "EVOLUCAO": 9,
            "INTERNADO_UTI": 9,
            "SEXO_PACIENTE": "I",
            "DESFECHO": 9,
            "CLASSIFICACAO_FINAL": 4,
        },
        inplace=True,
    )

    # 4. Mapeamento de valores categóricos
    df_filtrado["SEXO_PACIENTE"] = df_filtrado["SEXO_PACIENTE"].map(MAP_SEXO)

    df_filtrado["DESFECHO"] = pd.to_numeric(df_filtrado["DESFECHO"], errors="coerce").map(
        MAP_EVOLUCAO
    )

    df_filtrado["CLASSIFICACAO_FINAL"] = pd.to_numeric(
        df_filtrado["CLASSIFICACAO_FINAL"], errors="coerce"
    ).map(MAP_CLAS_FIN)

    df_filtrado["INTERNADO_UTI"] = pd.to_numeric(df_filtrado["INTERNADO_UTI"], errors="coerce").map(
        MAP_UTI
    )

    df_filtrado["VACINADO_COVID"] = pd.to_numeric(
        df_filtrado["VACINADO_COVID"], errors="coerce"
    ).map(MAP_VACINA_COV)

    df_filtrado["VACINADO_GRIPE"] = pd.to_numeric(
        df_filtrado["VACINADO_GRIPE"], errors="coerce"
    ).map(MAP_VACINA_GRIPE)

    # --- Limpeza ---
    # Remove linhas onde o NUMERO_DA_NOTIFICACAO (chave primária) é nulo
    df_filtrado = df_filtrado.dropna(subset=["NUMERO_DA_NOTIFICACAO"])
    # Remove duplicatas DENTRO do batch
    df_filtrado = df_filtrado.drop_duplicates(subset=["NUMERO_DA_NOTIFICACAO"])

    return df_filtrado


def processar_csv(con, caminho_csv):
    """
    Processa CSV em batchs e insere apenas registros novos
    usando INSERT OR IGNORE para máxima compatibilidade.
    """
    print(f"\nProcessando: {os.path.basename(caminho_csv)}")

    colunas_db = [
        "NUMERO_DA_NOTIFICACAO",
        "DATA_NOTIFICACAO",
        "SEXO_PACIENTE",
        "DESFECHO",
        "CLASSIFICACAO_FINAL",
        "INTERNADO_UTI",
        "VACINADO_COVID",
        "VACINADO_GRIPE",
        "UF",
    ]
    colunas_str = ", ".join([f'"{c}"' for c in colunas_db])
    tabela_temporaria = "temp_srag_batch"

    cur = con.cursor()
    total_lidos_arquivo = 0
    total_inseridos_arquivo = 0
    i = 0

    try:
        batch_iter = pd.read_csv(
            caminho_csv,
            sep=";",
            encoding="latin-1",
            low_memory=False,
            chunksize=BATCH_SIZE,
            on_bad_lines="warn",
        )
        # 1. Processa cada batch separadamente
        for i, batch in enumerate(batch_iter, start=1):
            df = preparar_batch(batch)
            total_lidos_arquivo += len(df)

            if not df.empty:
                # 2. Insere o lote em uma tabela temporária
                df.to_sql(tabela_temporaria, con, if_exists="replace", index=False)
                sql_insert = f"""
                    INSERT OR IGNORE INTO {TABELA} ({colunas_str})
                    SELECT {colunas_str}
                    FROM {tabela_temporaria};
                """
                cur.execute(sql_insert)

                # 3. Conta quantos registros foram inseridos
                inseridos_neste_lote = cur.rowcount
                total_inseridos_arquivo += inseridos_neste_lote

                con.commit()

                print(f"Lote {i}: {len(df)} lidos | {inseridos_neste_lote} inseridos")

        print(
            f"\nTotal inserido no arquivo: {total_inseridos_arquivo} (de {total_lidos_arquivo} lidos)"
        )

    except Exception as e:
        con.rollback()  # Desfaz a transação em caso de erro no lote
        print(f"\nErro ao processar Lote {i} de {caminho_csv}: {e}")
    finally:
        # Limpa a tabela temporária
        try:
            cur.execute(f"DROP TABLE IF EXISTS {tabela_temporaria}")
        except Exception as e_drop:
            print(f"\nAviso: Não foi possível limpar tabela temporária. {e_drop}")


def main():
    """Função principal para orquestrar a carga de dados."""
    print("\nIniciando atualização incremental SRAG - DATASUS")

    con = sqlite3.connect(DB_PATH)
    cria_tabela(con)

    try:
        arquivos = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
        if not arquivos:
            print(f"⚠️ Nenhum arquivo .csv encontrado em '{DATA_DIR}'")
            return

        print(f"Encontrados {len(arquivos)} arquivos CSV para processar.")

        for csv in arquivos:
            caminho = os.path.join(DATA_DIR, csv)
            processar_csv(con, caminho)

        print("\nAtualização incremental concluída com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
    finally:
        con.close()
        print("Conexão com o banco de dados fechada.")


if __name__ == "__main__":
    main()
