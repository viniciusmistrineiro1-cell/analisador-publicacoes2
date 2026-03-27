import pandas as pd
import re
import unicodedata
import streamlit as st

# === FUNÇÕES AUXILIARES ===
def normalizar_texto(texto):
    """Remove acentos e converte para minúsculas."""
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode()
    return texto.lower()

def extrair_prazo(texto):
    """Extrai prazos mantendo o texto original (ex: 'prazo de 15 dias')."""
    padrao = r'(?i)(prazo[^.:\n]*)'
    prazos = re.findall(padrao, texto)
    return "; ".join(prazos) if prazos else ""

def carregar_modelo_classificacao(df_class):
    """
    Constrói um dicionário de busca a partir do DataFrame de classificação.
    A chave é a palavra-chave normalizada, e o valor é uma tupla (grupo, providência).
    """
    # Identifica as colunas (pode ser que os nomes tenham pequenas diferenças)
    col_chave = None
    col_grupo = None
    col_providencia = None

    for col in df_class.columns:
        if "palavra" in col.lower() or "expressão" in col.lower():
            col_chave = col
        if "grupo" in col.lower() or "teor" in col.lower():
            col_grupo = col
        if "providência" in col.lower() or "providencia" in col.lower():
            col_providencia = col

    if not col_chave or not col_grupo or not col_providencia:
        st.error("❌ O arquivo de classificação não possui as colunas esperadas.")
        st.stop()

    # Constrói o dicionário de busca
    busca = {}
    for _, row in df_class.iterrows():
        chave = str(row[col_chave]).strip()
        if not chave or chave == "(outros casos)":
            continue
        chave_norm = normalizar_texto(chave)
        grupo = row[col_grupo]
        providencia = row[col_providencia]
        busca[chave_norm] = (grupo, providencia)
    return busca

def classificar_publicacao(texto, busca):
    """
    Retorna Grupo/Teor e Providência resumida com base no dicionário de busca.
    Usa regex com limites de palavra para evitar falsos positivos.
    """
    texto_norm = normalizar_texto(texto)
    for chave_norm, (grupo, providencia) in busca.items():
        # Busca a palavra-chave como palavra inteira
        padrao = r'\b' + re.escape(chave_norm) + r'\b'
        if re.search(padrao, texto_norm):
            return grupo, providencia
    return "", ""  # caso não encontre

# === CARREGAR MODELO DE CLASSIFICAÇÃO ===
df_class = pd.read_excel("modelo_classificacao.xlsx")
busca_classificacao = carregar_modelo_classificacao(df_class)

# === INTERFACE STREAMLIT ===
st.title("📑 Analisador de Publicações")
st.write("Carregue o relatório de publicações (formato .xlsx) para gerar a análise automática.")

arquivo_publicacoes = st.file_uploader("📂 Selecione o relatório de publicações (.xlsx)", type=["xlsx"])

if arquivo_publicacoes:
    # Carregar planilha de publicações
    df_pub = pd.read_excel(arquivo_publicacoes)

    # Exibir as colunas encontradas para diagnóstico
    st.write("**Colunas encontradas no relatório:**", list(df_pub.columns))

    # Mapeamento de colunas obrigatórias (pode personalizar)
    # Tenta identificar a coluna que contém o texto principal
    col_texto = None
    possiveis_nomes = ["publicação", "intimação", "texto", "despacho", "conteúdo"]
    for col in df_pub.columns:
        if col.lower() in possiveis_nomes:
            col_texto = col
            break
    if col_texto is None:
        # Se não encontrou, assume a primeira coluna que não seja 'processo' ou 'parte(s)'
        for col in df_pub.columns:
            if "processo" not in col.lower() and "parte" not in col.lower():
                col_texto = col
                break

    if col_texto is None:
        st.error("❌ Não foi possível identificar a coluna com o texto da publicação.")
        st.stop()

    # Nomes das colunas de metadados (opcionais)
    col_processo = "Processo" if "Processo" in df_pub.columns else None
    col_parte = "Parte(s)" if "Parte(s)" in df_pub.columns else None
    col_incidente = "Incidente" if "Incidente" in df_pub.columns else None
    col_classificacao = "Classificação" if "Classificação" in df_pub.columns else None

    resultado = []
    for idx, row in df_pub.iterrows():
        try:
            publicacao = str(row[col_texto]) if pd.notna(row[col_texto]) else ""

            grupo, providencia_resumida = classificar_publicacao(publicacao, busca_classificacao)
            prazo = extrair_prazo(publicacao)

            processo = row[col_processo] if col_processo else ""
            incidente = row[col_incidente] if col_incidente else "s/inc"
            autor = row[col_parte].split(",")[0] if col_parte and pd.notna(row[col_parte]) else ""
            classificacao = row[col_classificacao] if col_classificacao else ""

            resultado.append({
                "Nº publicação": idx + 1,
                "Processo": processo,
                "Nº de incidente": incidente,
                "Autor": autor,
                "Parte Contrária": "MUNICÍPIO DE SÃO PAULO",
                "Classificação de processo": classificacao,
                "Grupo/Teor": grupo,
                "Providência resumida": providencia_resumida,
                "Prazo": prazo,
                "Providência completa": publicacao
            })
        except Exception as e:
            # Log do erro para depuração, mas continua processando
            st.warning(f"Erro ao processar linha {idx}: {e}")
            continue

    if not resultado:
        st.error("Nenhuma linha foi processada. Verifique o formato do relatório.")
        st.stop()

    df_final = pd.DataFrame(resultado)

    # Mostrar prévia
    st.subheader("🔎 Pré-visualização da análise")
    st.dataframe(df_final.head(20))

    # Exportar para download
    st.subheader("📥 Baixar resultado")
    output = df_final.to_excel(index=False, engine="openpyxl")
    st.download_button(
        label="⬇️ Download Excel",
        data=output,
        file_name="analise_publicacoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
