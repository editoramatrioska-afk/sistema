import streamlit as st
from supabase import create_client, Client
import math
from docx import Document
from fpdf import FPDF
import io
import os 
from lxml import etree # Para leitura precisa do XML

# --- 1. CONEXÃO COM O BANCO DE DADOS ---
URL: str = "https://gbeoizrqxzopjsxthwym.supabase.co"
KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdiZW9penJxeHpvcGpzeHRod3ltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NzAwNzcsImV4cCI6MjA5MjA0NjA3N30.dGQ3gnzjT5jHd4LAZTTSp1k8XemowUglFToPbDL38OY"
supabase: Client = create_client(URL, KEY)

NOME_LOGO = "logo.jpeg"

# --- 2. FUNÇÕES DE APOIO ---

def contar_caracteres_oficial_word(arquivo):
    """Conta caracteres exatamente como o Word (Corpo + Notas + Tabelas)."""
    doc = Document(arquivo)
    texto_total = ""
    
    # Namespace necessário para ler as tags do Word (w:t)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

    # 1. Corpo Principal
    for p in doc.paragraphs:
        texto_total += p.text
    
    # 2. Tabelas
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                texto_total += celula.text
                
    # 3. Notas de Rodapé (Footnotes) e Notas de Fim (Endnotes)
    # Varremos as 'parts' do documento em busca de notas
    for rel in doc.part.rels.values():
        if "footnotes" in rel.target_ref or "endnotes" in rel.target_ref:
            xml_content = rel.target_part.blob
            root = etree.fromstring(xml_content)
            # Buscamos apenas as tags de texto oficial <w:t>
            for t in root.xpath('//w:t', namespaces=ns):
                if t.text:
                    texto_total += t.text

    # O Word conta caracteres (com espaços). 
    # Para bater o valor exato, limpamos apenas nulos, mas mantemos espaços.
    return len(texto_total)

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists(NOME_LOGO):
        pdf.image(NOME_LOGO, 10, 8, 30) 
        pdf.ln(20)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Orcamento Editorial", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Cliente/Obra: {dados['cliente']}", ln=True)
    pdf.cell(200, 10, f"Total de Caracteres: {dados['caracteres']}", ln=True)
    pdf.cell(200, 10, f"Qtd. de Laudas: {dados['laudas']:.2f}", ln=True)
    pdf.cell(200, 10, f"Estimativa de Paginas ({dados['formato']}): {dados['paginas']}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"VALOR TOTAL: R$ {dados['total']:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# --- 3. INTERFACE ---
st.set_page_config(page_title="Editora - Orçamentador", layout="wide")

with st.sidebar:
    if os.path.exists(NOME_LOGO):
        st.image(NOME_LOGO, width=150)
    st.header("Configuração")
    valor_lauda = st.number_input("Preço Lauda (R$)", value=6.0)
    valor_pag_diag = st.number_input("Diagramação/Pág (R$)", value=5.0)
    custos_fixos = st.number_input("Custos Fixos (R$)", value=750.0)

st.title("📚 Orçamentador Editorial")

col1, col2 = st.columns(2)
with col1:
    nome_cliente = st.text_input("Nome do Cliente:")
    arquivo_word = st.file_uploader("Arquivo Word", type=["docx"])
    
    if arquivo_word:
        total_caracteres = contar_caracteres_oficial_word(arquivo_word)
        st.success(f"{total_caracteres} caracteres detectados.")
    else:
        total_caracteres = st.number_input("Digite manualmente:", value=0)

with col2:
    formato = st.selectbox("Formato:", ["14x21", "16x23", "17x24"])
    quer_ebook = st.checkbox("Incluir E-book?", value=True)

# Cálculos
qtd_laudas = total_caracteres / 2000
fator = {"14x21": 1.15, "16x23": 1.0, "17x24": 0.9}[formato]
est_paginas = math.ceil(qtd_laudas * fator)
c_revisao = qtd_laudas * valor_lauda
c_diag = est_paginas * valor_pag_diag
c_ebook = est_paginas * 2.0 if quer_ebook else 0.0
total_geral = c_revisao + c_diag + c_ebook + custos_fixos

dados_finais = {
    "cliente": nome_cliente, "caracteres": total_caracteres, "laudas": qtd_laudas,
    "formato": formato, "paginas": est_paginas, "total": total_geral
}

st.markdown("---")
if total_caracteres > 0:
    st.metric("Investimento Estimado", f"R$ {total_geral:,.2f}")
    if st.button("💾 Salvar no Banco"):
        payload = {"cliente": nome_cliente, "caracteres": total_caracteres, "formato": formato, "paginas": est_paginas, "valor_total": total_geral}
        supabase.table("orcamentos").insert(payload).execute()
        st.success("Salvo!")
    
    pdf_file = gerar_pdf(dados_finais)
    st.download_button("📥 Baixar PDF", data=pdf_file, file_name=f"Orcamento_{nome_cliente}.pdf")
