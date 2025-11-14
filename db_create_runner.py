import sys

from src.utils import db_utils, get_data


def main(url=None):
    DATASET_URL = url or "https://opendatasus.saude.gov.br/dataset/srag-2021-a-2024"
    print("Iniciando pipeline SRAG - DATASUS")

    # Etapa 1: Baixar os dados
    print("[1/2] Baixando dados do OpenDataSUS...")
    get_data.main(DATASET_URL)
    print("\n✅ Etapa 1 concluída!\n")

    # Etapa 2: Atualizar/criar banco
    print("\n[2/2] Criando ou atualizando banco de dados...")
    db_utils.main()
    print("\n✅ Etapa 2 concluída!\n")

    print("Pipeline finalizado com sucesso!")


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(url=url_arg)
