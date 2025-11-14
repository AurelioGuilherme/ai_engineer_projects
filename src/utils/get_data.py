import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# URL base
BASE_URL = "https://opendatasus.saude.gov.br"
DEFAULT_DATASET_URL = f"{BASE_URL}/dataset/srag-2021-a-2024"

# Diretório de saída
OUTPUT_DIR = os.path.join("data", "srag_csvs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_html(url: str) -> BeautifulSoup:
    """Faz a requisição e retorna o conteúdo HTML parseado."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        raise RuntimeError(f"❌ Erro ao acessar {url}: {e}") from e


def get_csv_links(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Extrai todos os links CSV do dataset."""
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".csv"):
            csv_url = href if href.startswith("http") else BASE_URL + href
            name = csv_url.split("/")[-1]
            links.append((name, csv_url))
    return links


def download_csv(name: str, url: str):
    """Baixa o CSV se for novo ou atualizado."""
    filepath = os.path.join(OUTPUT_DIR, name)
    try:
        # Verifica se já existe
        if os.path.exists(filepath):
            local_size = os.path.getsize(filepath)
            remote_head = requests.head(url)
            remote_size = int(remote_head.headers.get("Content-Length", 0))

            if local_size == remote_size:
                print(f"Já existe e está atualizado: {name}")
                return

        print(f"Baixando {name}")
        r = requests.get(url, timeout=60)
        r.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(r.content)

        print(f"✅ Arquivo salvo: {filepath}")

    except Exception as e:
        print(f"❌ Erro ao baixar {name}: {e}")


def main(url: str = DEFAULT_DATASET_URL):
    """Executa o processo completo de coleta de CSVs SRAG."""
    print(f"Iniciando coleta em {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"URL usada: {url}")

    soup = fetch_html(url=url)
    csv_links = get_csv_links(soup)

    if not csv_links:
        print("⚠️ Nenhum link CSV encontrado.")
        return

    for name, csv_url in csv_links:
        download_csv(name, csv_url)

    print("✅ Processo concluído!")


if __name__ == "__main__":
    main()
