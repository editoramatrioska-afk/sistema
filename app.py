import streamlit as st
from supabase import create_client, Client
import math
from docx import Document
from fpdf import FPDF
import io

# --- 1. CONEXÃO COM O BANCO DE DADOS (SUPABASE) ---
URL: str = "https://gbeoizrqxzopjsxthwym.supabase.co"
KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdiZW9penJxeHpvcGpzeHRod3ltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NzAwNzcsImV4cCI6MjA5MjA0NjA3N30.dGQ3gnzjT5jHd4LAZTTSp1k8XemowUglFToPbDL38OY"
supabase: Client = create_client(URL, KEY)

# --- 2. FUNÇÕES DE APOIO (LÓGICA DO NEGÓCIO) ---

def contar_caracteres(arquivo):
    """Lê o arquivo Word e conta caracteres com espaços e notas."""
    doc = Document(arquivo)
    texto_total = ""
    for p in doc.paragraphs:
        texto_total += p.text
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                texto_total += celula.text
    return len(texto_total)

def gerar_pdf(dados):
    """Cria um PDF organizado para o cliente."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Orcamento Editorial", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Cliente/Obra: {dados['cliente']}", ln=True)
    pdf.cell(200, 10, f"Formato Escolhido: {dados['formato']}", ln=True)
    pdf.cell(200, 10, f"Total de Caracteres: {dados['caracteres']}", ln=True)
    pdf.cell(200, 10, f"Qtd. de Laudas (2000 carac.): {dados['laudas']:.2f}", ln=True)
    pdf.cell(200, 10, f"Estimativa de Paginas: {dados['paginas']}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Resumo de Custos:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"- Revisao: R$ {dados['custo_revisao']:.2f}", ln=True)
    pdf.cell(200, 10, f"- Diagramacao: R$ {dados['custo_diagramacao']:.2f}", ln=True)
    pdf.cell(200, 10, f"- Conversao E-book: R$ {dados['custo_ebook']:.2f}", ln=True)
    pdf.cell(200, 10, f"- Custos Fixos (Capa/ISBN): R$ {dados['custos_fixos']:.2f}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"VALOR TOTAL: R$ {dados['total']:.2f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. INTERFACE DO USUÁRIO (STREAMLIT) ---

st.set_page_config(page_title="Editora - Sistema de Orçamento", layout="wide")
st.title("📚 Orçamentador Editorial Profissional")

# Sidebar para Custos Fixos (Você pode alterar conforme precisar)
st.sidebar.header("Configuração de Preços")
valor_lauda = st.sidebar.number_input("Preço da Lauda (R$)", value=6.0)
valor_pag_diagramacao = st.sidebar.number_input("Diagramação por Página (R$)", value=5.0)
custos_fixos_padrao = st.sidebar.number_input("Capa + ISBN + Ficha (R$)", value=750.0)

# Entrada de Dados
st.subheader("1. Informações do Projeto")
col1, col2 = st.columns(2)

with col1:
    nome_cliente = st.text_input("Nome do Cliente ou Título da Obra:")
    arquivo_word = st.file_uploader("Suba o manuscrito (.docx)", type=["docx"])
    
    if arquivo_word:
        total_caracteres = contar_caracteres(arquivo_word)
        st.success(f"Sucesso! {total_caracteres} caracteres detectados.")
    else:
        total_caracteres = st.number_input("Ou digite os caracteres manualmente:", value=0)

with col2:
    formato = st.selectbox("Formato do Livro Fisico:", ["14x21", "16x23", "17x24"])
    quer_ebook = st.checkbox("Incluir conversão para E-book?", value=True)

# --- 4. CÁLCULOS ---
# Calculando Laudas
qtd_laudas = total_caracteres / 2000

# Estimativa de Páginas baseada no formato (Fatores de conversão)
fatores = {"14x21": 1.15, "16x23": 1.0, "17x24": 0.9}
est_paginas = math.ceil(qtd_laudas * fatores[formato])

# Cálculo de Custos
c_revisao = qtd_laudas * valor_lauda
c_diagramacao = est_paginas * valor_pag_diagramacao
c_ebook = est_paginas * 2.0 if quer_ebook else 0.0 # Exemplo: R$ 2 por página para converter e-book
total_geral = c_revisao + c_diagramacao + c_ebook + custos_fixos_padrao

# Dados consolidados para salvar e gerar PDF
dados_finais = {
    "cliente": nome_cliente,
    "caracteres": total_caracteres,
    "laudas": qtd_laudas,
    "formato": formato,
    "paginas": est_paginas,
    "custo_revisao": c_revisao,
    "custo_diagramacao": c_diagramacao,
    "custo_ebook": c_ebook,
    "custos_fixos": custos_fixos_padrao,
    "total": total_geral
}

# --- 5. EXIBIÇÃO DE RESULTADOS E AÇÕES ---
st.markdown("---")
if total_caracteres > 0:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Laudas", f"{qtd_laudas:.2f}")
    c2.metric("Est. de Páginas", est_paginas)
    c3.metric("Investimento Total", f"R$ {total_geral:,.2f}")

    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("💾 Salvar no Banco de Dados"):
            if nome_cliente:
                # Prepara os dados para o Supabase (colunas devem existir na tabela)
                payload = {
                    "cliente": nome_cliente,
                    "caracteres": total_caracteres,
                    "formato": formato,
                    "paginas": est_paginas,
                    "valor_total": total_geral
                }
                supabase.table("orcamentos").insert(payload).execute()
                st.success("Orçamento gravado com sucesso!")
            else:
                st.warning("Dê um nome ao projeto antes de salvar.")

    with col_btn2:
        pdf_file = gerar_pdf(dados_finais)
        st.download_button(
            label="📥 Baixar Orçamento em PDF",
            data=pdf_file,
            file_name=f"Orcamento_{nome_cliente}.pdf",
            mime="application/pdf"
        )

# Histórico
st.markdown("---")
if st.checkbox("Visualizar histórico de orçamentos salvos"):
    historico = supabase.table("orcamentos").select("*").execute()
    st.dataframe(historico.data)
