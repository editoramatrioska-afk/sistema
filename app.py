import streamlit as st
from supabase import create_client, Client
import math
from docx import Document
from fpdf import FPDF
import io
import os 
from lxml import etree

# --- 1. CONEXÃO COM O BANCO DE DADOS ---
URL: str = "https://gbeoizrqxzopjsxthwym.supabase.co"
KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdiZW9penJxeHpvcGpzeHRod3ltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NzAwNzcsImV4cCI6MjA5MjA0NjA3N30.dGQ3gnzjT5jHd4LAZTTSp1k8XemowUglFToPbDL38OY"
supabase: Client = create_client(URL, KEY)

NOME_LOGO = "logo.png"

# --- 2. FUNÇÕES DE APOIO ---

def contar_caracteres_oficial_word(arquivo):
    doc = Document(arquivo)
    texto_total = []
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

    for p in doc.paragraphs:
        texto_total.append(p.text)
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                texto_total.append(celula.text)
    for rel in doc.part.rels.values():
        if "footnotes" in rel.target_ref or "endnotes" in rel.target_ref:
            root = etree.fromstring(rel.target_part.blob)
            for t in root.xpath('//w:t', namespaces=ns):
                if t.text:
                    texto_total.append(t.text)
    return len("".join(texto_total))

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists(NOME_LOGO):
        pdf.image(NOME_LOGO, 10, 8, 30) 
        pdf.ln(20)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Orcamento Editorial", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 8, f"Cliente: {dados['cliente']}", ln=True)
    pdf.cell(200, 8, f"Caracteres Totais: {dados['caracteres']}", ln=True)
    pdf.cell(200, 8, f"Total de Laudas: {dados['laudas']:.2f}", ln=True)
    pdf.cell(200, 8, f"Formato: {dados['formato']} ({dados['paginas']} paginas)", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, "Detalhamento de Custos:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 7, f"- Copidesque: R$ {dados['v_copidesque']:.2f}", ln=True)
    pdf.cell(200, 7, f"- Diagramacao: R$ {dados['v_diag']:.2f}", ln=True)
    pdf.cell(200, 7, f"- Revisao: R$ {dados['v_revisao']:.2f}", ln=True)
    pdf.cell(200, 7, f"- E-pub: R$ {dados['v_epub']:.2f}", ln=True)
    pdf.cell(200, 7, f"- Capa, ISBN e Fichas: R$ {dados['v_fixos']:.2f}", ln=True)
    pdf.cell(200, 7, f"- Taxa da Editora: R$ {dados['v_taxa_ed']:.2f}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"VALOR TOTAL: R$ {dados['total']:.2f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# --- 3. INTERFACE ---
st.set_page_config(page_title="Editora - Orçamentador", layout="wide")

# Inicializar lista de formatos personalizados se não existir
if 'formatos_custom' not in st.session_state:
    st.session_state['formatos_custom'] = {}

with st.sidebar:
    if os.path.exists(NOME_LOGO):
        st.image(NOME_LOGO, width=150)
    
    st.header("Configuração de Preços")
    p_copidesque = st.number_input("Copidesque (por lauda): R$", value=6.0)
    p_diagramacao = st.number_input("Diagramação (por página): R$", value=5.0)
    p_revisao = st.number_input("Revisão (por página): R$", value=4.0)
    p_capa = st.number_input("Capa: R$", value=500.0)
    p_isbn = st.number_input("ISBN e Fichas: R$", value=300.0)
    p_epub = st.number_input("E-pub (por página): R$", value=2.50)
    p_taxa_editora = st.number_input("Taxa da editora: R$", value=3000.0)

st.title("📚 Orçamentador Editorial")

col1, col2 = st.columns(2)

with col1:
    nome_cliente = st.text_input("Nome do Cliente:")
    arquivo_word = st.file_uploader("Arquivo Word (.docx)", type=["docx"])
    
    if arquivo_word:
        total_caracteres = contar_caracteres_oficial_word(arquivo_word)
        st.success(f"{total_caracteres} caracteres detectados.")
    else:
        total_caracteres = st.number_input("Total de caracteres manualmente:", value=0)

    st.subheader("Elementos Extras")
    c_img = st.number_input("Imagens (Qtd. de páginas extras):", min_value=0, value=0)
    c_tab = st.number_input("Tabelas (Qtd. de páginas extras):", min_value=0, value=0)
    c_qua = st.number_input("Quadros (Qtd. de páginas extras):", min_value=0, value=0)
    c_gra = st.number_input("Gráficos (Qtd. de páginas extras):", min_value=0, value=0)
    c_out = st.number_input("Outros (Qtd. de páginas extras):", min_value=0, value=0)
    paginas_extras = c_img + c_tab + c_qua + c_gra + c_out

with col2:
    opcoes_formato = ["14x21", "16x23", "17x24", "Personalizado"] + list(st.session_state['formatos_custom'].keys())
    formato_sel = st.selectbox("Formato do Livro:", opcoes_formato)
    
    meta_caracteres = 0
    if formato_sel == "14x21": meta_caracteres = 1700
    elif formato_sel == "16x23": meta_caracteres = 2200
    elif formato_sel == "17x24": meta_caracteres = 2900
    elif formato_sel == "Personalizado":
        novo_nome = st.text_input("Nome do novo formato (ex: 10x15):")
        meta_caracteres = st.number_input("Caracteres por página deste formato:", value=1500)
        if st.button("Salvar Novo Formato"):
            st.session_state['formatos_custom'][novo_nome] = meta_caracteres
            st.experimental_rerun()
    else:
        meta_caracteres = st.session_state['formatos_custom'][formato_sel]

    incluir_epub = st.checkbox("Incluir E-pub no orçamento?", value=True)

# --- 4. LÓGICA DE CÁLCULO ---
# 1. Laudas e Copidesque
qtd_laudas = total_caracteres / 2000
custo_copidesque = qtd_laudas * p_copidesque

# 2. Páginas e Diagramação/Revisão
paginas_texto = math.ceil(total_caracteres / meta_caracteres) if meta_caracteres > 0 else 0
total_paginas_projeto = paginas_texto + paginas_extras

custo_diagramacao = total_paginas_projeto * p_diagramacao
custo_revisao = total_paginas_projeto * p_revisao
custo_epub = (total_paginas_projeto * p_epub) if incluir_epub else 0.0

# 3. Fixos e Taxa
custos_fixos_total = p_capa + p_isbn
valor_total = custo_copidesque + custo_diagramacao + custo_revisao + custo_epub + custos_fixos_total + p_taxa_editora

# --- 5. RESULTADOS ---
dados_finais = {
    "cliente": nome_cliente, "caracteres": total_caracteres, "laudas": qtd_laudas,
    "formato": formato_sel, "paginas": total_paginas_projeto, "total": valor_total,
    "v_copidesque": custo_copidesque, "v_diag": custo_diagramacao, "v_revisao": custo_revisao,
    "v_epub": custo_epub, "v_fixos": custos_fixos_total, "v_taxa_ed": p_taxa_editora
}

st.markdown("---")
if total_caracteres > 0:
    c1, c2, c3 = st.columns(3)
    c1.metric("Páginas Totais", total_paginas_projeto)
    c2.metric("Qtd. Laudas", f"{qtd_laudas:.2f}")
    c3.metric("Total Orçamento", f"R$ {valor_total:,.2f}")

    if st.button("💾 Salvar no Banco de Dados"):
        payload = {"cliente": nome_cliente, "caracteres": total_caracteres, "formato": formato_sel, "paginas": total_paginas_projeto, "valor_total": valor_total}
        supabase.table("orcamentos").insert(payload).execute()
        st.success("Orçamento salvo com sucesso!")

    pdf_file = gerar_pdf(dados_finais)
    st.download_button("📥 Baixar Orçamento PDF", data=pdf_file, file_name=f"Orcamento_{nome_cliente}.pdf")
