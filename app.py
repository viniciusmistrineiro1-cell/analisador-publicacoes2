import streamlit as st
import pandas as pd
import re
import io
import unicodedata

# ================== Funções auxiliares ==================
def _normalize(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s)) if not unicodedata.combining(c)).lower()

def _find_intim_col(df):
    for col in df.columns:
        if 'intim' in _normalize(col):
            return col
    return None

def analisar_publicacao(texto, numero_pub):
    texto = "" if texto is None else str(texto)
    resultado = {
        "Nº de publicação": numero_pub,
        "Processo": None,
        "Nº de incidente": None,
        "Autor": None,
        "Parte Contrária": "MUNICÍPIO DE SÃO PAULO",
        "Classificação de processo": None,
        "Grupo/Teor": None,
        "Providência resumida": None,
        "Prazo": None,
        "Providência completa": None
    }

    # Processo CNJ
    match_proc = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", texto)
    if match_proc:
        resultado["Processo"] = match_proc.group()
        incidente_match = re.search(r"/(\d+)\b", texto)
        if incidente_match:
            resultado["Nº de incidente"] = incidente_match.group(1)
        else:
            resultado["Nº de incidente"] = "s/inc"

    # Autor
    partes_match = re.search(r"Parte\(s\):\s*(.*?)\n\s*MUNICÍPIO DE SÃO PAULO", texto, re.S | re.I)
    if partes_match:
        autor = partes_match.group(1).strip().split("\n")[0]
        resultado["Autor"] = autor

    lower = texto.lower()

    # Classificação
    if "precatório" in lower or "precatorio" in lower:
        resultado["Classificação de processo"] = "Precatório"
    elif "rpv" in lower:
        resultado["Classificação de processo"] = "RPV"
    elif "cumprimento de sentença" in lower or "cumprimento" in lower:
        resultado["Classificação de processo"] = "Cumprimento de sentença"

    # Grupo/Teor + Resumida
    if "homologo o acordo" in lower:
        resultado["Grupo/Teor"] = "Homologação de acordo"
        resultado["Providência resumida"] = "Homologar acordo"
    elif "requisite-se" in lower or "requisite se" in lower:
        resultado["Grupo/Teor"] = "Requisição de pagamento"
        resultado["Providência resumida"] = "Expedir requisição de pagamento"
    elif "intime-se" in lower or "intime se" in lower:
        resultado["Grupo/Teor"] = "Intimação"
        resultado["Providência resumida"] = "Cumprir intimação"
    elif "defiro" in lower:
        resultado["Grupo/Teor"] = "Decisão favorável"
        resultado["Providência resumida"] = "Cumprir decisão judicial"

    # Prazo
    prazo_match = re.search(r"(\d+)\s*(?:dias?|dia)\b", texto, re.I)
    if prazo_match:
        resultado["Prazo"] = int(prazo_match.group(1))

    # Providência completa
    prov_completa = re.split(r"\bInt(?:\.|imação|imacao)", texto, flags=re.I)
    if prov_completa:
        resultado["Providência completa"] = prov_completa[0].strip()
    else:
        resultado["Providência completa"] = texto.strip()

    return resultado

# ================== Interface Streamlit ==================
st.title("📑 Analisador de Publicações")
st.write("Envie o arquivo Excel com a aba **Publicacoes** e a coluna de intimações.")

file = st.file_uploader("Envie o arquivo (.xlsx)", type=["xlsx"])

if file:
    xls = pd.ExcelFile(file)
    st.write("Planilhas encontradas:", xls.sheet_names)

    sheet_name = "Publicacoes" if "Publicacoes" in xls.sheet_names else xls.sheet_names[0]
    df_publicacoes = pd.read_excel(file, sheet_name=sheet_name)

    intim_col = _find_intim_col(df_publicacoes)
    if intim_col is None:
        st.error("Não encontrei coluna com 'Intim' no nome.")
    else:
        publicacoes = df_publicacoes[intim_col].dropna().astype(str).tolist()
        analises = [analisar_publicacao(txt, i+1) for i, txt in enumerate(publicacoes)]
        df_resultado = pd.DataFrame(analises)

        st.success(f"{len(df_resultado)} publicações analisadas com sucesso!")
        st.dataframe(df_resultado.head(10))

        # Preparar download
        output = io.BytesIO()
        df_resultado.to_excel(output, index=False)
        st.download_button(
            label="📥 Baixar análise completa",
            data=output,
            file_name="analise_publicacoes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
