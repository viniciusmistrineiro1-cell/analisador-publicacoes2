import pandas as pd
import re
import streamlit as st

# === FUNÇÕES AUXILIARES ===
def extrair_prazo(texto):
    """Extrai prazos mantendo o texto original (ex: 'prazo de 15 dias')."""
    padrao = r'(?i)(prazo[^.:\n]*)'
    prazos = re.findall(padrao, texto)
    return "; ".join(prazos) if prazos else ""

def classificar_publicacao(texto, df_classificacao):
    """Retorna Grupo/Teor e Providência resumida com base nas frases do modelo."""
    for _, row in df_classificacao.iterrows():
        chave = str(row["Frase-chave"]).strip().lower()
        if chave in texto.lower():
            return row["Grupo/Teor"], row["Providência resumida"]
    return "", ""  # caso não encontre

# === CARREGAR MODELO DE CLASSIFICAÇÃO (fixo no repositório) ===
df_class = pd.read_excel("modelo_classificacao.xlsx")

# === INTERFACE STREAMLIT ===
st.title("📑 Analisador de Publicações")

st.write("Carregue o relatório de publicações para gerar a análise automática.")

# Upload do arquivo de publicações
arquivo_publicacoes = st.file_uploader("📂 Selecione o relatório de publicações (.xlsx)", type=["xlsx"])

if arquivo_publicacoes:
    # Carregar planilha de publicações
    df_pub = pd.read_excel(arquivo_publicacoes)

    resultado = []
    for idx, row in df_pub.iterrows():
        publicacao = str(row.get("Publicação", ""))

        grupo, providencia_resumida = classificar_publicacao(publicacao, df_class)
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

    df_final = pd.DataFrame(resultado)

    # Mostrar prévia
    st.subheader("🔎 Pré-visualização da análise")
    st.dataframe(df_final.head(20))

    # Exportar para download
    st.subheader("📥 Baixar resultado")
    st.download_button(
        label="⬇️ Download Excel",
        data=df_final.to_excel(index=False, engine="openpyxl"),
        file_name="analise_publicacoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
