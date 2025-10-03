import pandas as pd
import re

# === CONFIGURAÇÕES ===
# Caminhos dos arquivos
ARQUIVO_PUBLICACOES = "relatorio-8682625-70016.xlsx"
ARQUIVO_CLASSIFICACAO = "modelo_classificacao.xlsx"
ARQUIVO_SAIDA = "analise_publicacoes.xlsx"

# === FUNÇÕES AUXILIARES ===
def extrair_prazo(texto):
    """Extrai prazos mantendo o texto original (ex: 'prazo de 15 dias', 'prazo comum de 5 dias')."""
    padrao = r'(?i)(prazo[^.:\n]*)'
    prazos = re.findall(padrao, texto)
    return "; ".join(prazos) if prazos else ""

def classificar_publicacao(texto, df_classificacao):
    """Retorna Grupo/Teor e Providência resumida com base nas palavras/frases do modelo."""
    for _, row in df_classificacao.iterrows():
        chave = str(row["Palavra-chave"]).strip().lower()
        if chave in texto.lower():
            return row["Grupo/Teor"], row["Providência resumida"]
    return "", ""  # caso não encontre

# === CARREGAR DADOS ===
# Publicações
df = pd.read_excel(ARQUIVO_PUBLICACOES)

# Modelo de classificação
df_classificacao = pd.read_excel(ARQUIVO_CLASSIFICACAO)

# === ANÁLISE ===
resultado = []
for idx, row in df.iterrows():
    publicacao = str(row.get("Publicação", ""))

    grupo, providencia_resumida = classificar_publicacao(publicacao, df_classificacao)
    prazo = extrair_prazo(publicacao)

    resultado.append({
        "Nº publicação": idx + 1,
        "Processo": row.get("Processo", ""),
        "Nº de incidente": row.get("Incidente", "s/inc"),
        "Autor": row.get("Parte(s)", "").split(",")[0] if pd.notna(row.get("Parte(s)", "")) else "",
        "Parte Contrária": "MUNICÍPIO DE SÃO PAULO",
        "Classificação de processo": row.get("Classificação", ""),
        "Grupo/Teor": grupo,
        "Providência resumida": providencia_resumida,
        "Prazo": prazo,
        "Providência completa": publicacao
    })

# === EXPORTAR ===
df_final = pd.DataFrame(resultado)
df_final.to_excel(ARQUIVO_SAIDA, index=False)

print(f"Análise concluída! Arquivo salvo em: {ARQUIVO_SAIDA}")

