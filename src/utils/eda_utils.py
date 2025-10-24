def iter_blocos(n_total, tamanho_bloco):
    """ "Gerador que retorna intervalos de colunas para blocos do DataFrame."""
    for start in range(0, n_total, tamanho_bloco):
        end = min(start + tamanho_bloco, n_total)
        yield start, end


def proximo_bloco(df, blocos):
    """Função para exibir o próximo bloco de colunas do DataFrame."""
    try:
        start, end = next(blocos)
        print(f"📊 Colunas {start} a {end - 1}")
        columns_name = df.iloc[:, start:end].columns
        return df.iloc[:, start:end].info(), columns_name
    except StopIteration:
        print("Todos os blocos já foram exibidos.")
