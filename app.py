import streamlit as st
from supabase import create_client, Client
import math
from docx import Document  # Ferramenta para ler o Word

# --- CONEXÃO COM O BANCO DE DADOS ---
url: str = "https://gbeoizrqxzopjsxthwym.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdiZW9penJxeHpvcGpzeHRod3ltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NzAwNzcsImV4cCI6MjA5MjA0NjA3N30.dGQ3gnzjT5jHd4LAZTTSp1k8XemowUglFToPbDL38OY"
supabase: Client = create_client(url, key)

# --- FUNÇÃO MODULAR: LEITURA DE CARACTERES ---
def contar_caracteres(arquivo):
    doc = Document(arquivo)
    texto_total = ""
    # O loop abaixo percorre cada parágrafo e nota do arquivo
    for p in doc.paragraphs:
        texto_total += p.text
    # Também contamos o que está nas tabelas, se houver
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                texto_total += celula.text
    return len(texto_total)

# --- INTERFACE DO APP ---
st.set_page_config(page_title="Editora Cloud", layout="wide")
st.title("📚 Orçamentador Inteligente")

# 1. ENTRADA DE DADOS
st.subheader("1. Upload e Configuração")
col1, col2 = st.columns(2)

with col1:
    nome_cliente = st.text_input("Nome do Cliente/Obra:")
    arquivo_word = st.file_uploader("Suba o arquivo Word (.docx)", type=["docx"])
    
    # Se subir o arquivo, o sistema conta. Se não, permite digitar.
    if arquivo_word:
        total_caracteres = contar_caracteres(arquivo_word)
        st.info(f"Caracteres detectados: {total_caracteres}")
    else:
        total_caracteres = st.number_input("Ou digite manualmente:", value=0)

with col2:
    formato = st.selectbox("Formato do Livro:", ["14x21", "16x23", "17x24"])
    valor_lauda = st.sidebar.number_input("Preço da Lauda (R$)", value=6.0)

# 2. CÁLCULOS
qtd_laudas = total_caracteres / 2000
fatores = {"14x21": 1.15, "16x23": 1.0, "17x24": 0.9}
est_paginas = math.ceil(qtd_laudas * fatores[formato])

# Custos exemplares
custo_revisao = qtd_laudas * valor_lauda
valor_total = custo_revisao + 750.0 # Exemplo: Revisão + Custos Fixos (Capa/ISBN)

# 3. EXIBIÇÃO E SALVAMENTO
st.markdown("---")
st.metric("Estimativa de Páginas", est_paginas)

if st.button("💾 Salvar no Supabase"):
    if nome_cliente and total_caracteres > 0:
        dados = {
            "cliente": nome_cliente,
            "caracteres": total_caracteres,
            "formato": formato,
            "paginas": est_paginas,
            "valor_total": valor_total
        }
        supabase.table("orcamentos").insert(dados).execute()
        st.success("Orçamento salvo com sucesso!")
    else:
        st.error("Preencha o nome e o conteúdo antes de salvar.")

# 4. HISTÓRICO
if st.checkbox("Ver histórico de orçamentos"):
    res = supabase.table("orcamentos").select("*").execute()
    st.dataframe(res.data)
