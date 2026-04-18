import streamlit as st
from supabase import create_client, Client
import math
from docx import Document
from fpdf import FPDF
import io
import os 
from lxml import etree
from datetime import datetime
from num2words import num2words

# --- 1. CONEXÃO COM O BANCO DE DADOS ---
URL: str = "https://gbeoizrqxzopjsxthwym.supabase.co"
KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdiZW9penJxeHpvcGpzeHRod3ltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NzAwNzcsImV4cCI6MjA5MjA0NjA3N30.dGQ3gnzjT5jHd4LAZTTSp1k8XemowUglFToPbDL38OY"
supabase: Client = create_client(URL, KEY)

NOME_LOGO = "logo.png"
NOME_RODAPE = "rodape.png"

# --- 2. FUNÇÕES DE APOIO ---

def valor_por_extenso(valor):
    try:
        inteiro = int(valor)
        extenso = num2words(inteiro, lang='pt_BR')
        return f"({extenso} reais)"
    except:
        return ""

def contar_caracteres_oficial_word(arquivo):
    doc = Document(arquivo)
    texto_total = []
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    for p in doc.paragraphs: texto_total.append(p.text)
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells: texto_total.append(celula.text)
    for rel in doc.part.rels.values():
        if "footnotes" in rel.target_ref or "endnotes" in rel.target_ref:
            root = etree.fromstring(rel.target_part.blob)
            for t in root.xpath('//w:t', namespaces=ns):
                if t.text: texto_total.append(t.text)
    return len("".join(texto_total))

class PDF_Proposta(FPDF):
    def header(self):
        if os.path.exists(NOME_LOGO):
            self.image(NOME_LOGO, (210 - 40) / 2, 8, 40)
        self.ln(25)

    def footer(self):
        if os.path.exists(NOME_RODAPE):
            self.image(NOME_RODAPE, 0, 275, 210)

def obter_data_formatada():
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", 
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    hoje = datetime.now()
    return f"São Paulo, {hoje.day} de {meses[hoje.month - 1]} de {hoje.year}"

def gerar_pdf_matrioska(dados):
    pdf = PDF_Proposta()
    pdf.set_auto_page_break(auto=True, margin=35)
    
    # --- PÁGINA 1: APRESENTAÇÃO ---
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, obter_data_formatada(), ln=True)
    pdf.ln(5)
    
    pdf.set_font("helvetica", size=12)
    texto_apresentacao = (
        "A Matrioska é uma editora de livros científicos, técnicos e profissionais, provedora de conteúdo para a "
        "formação sólida de estudantes universitários e para a atualização de profissionais das mais diversas áreas do conhecimento.\n\n"
        "Nosso catálogo contempla autoras e autores de primeira linha, que aliam o que há de mais inovador em termos de abordagem "
        "e rigor acadêmico, avaliados e validados por um renomado Conselho Editorial Nacional e Internacional que resguarda a "
        "qualidade de nossas publicações.\n\n"
        "Se você acredita no futuro dos livros (independente do formato ou suporte), vem com a gente!\n"
        "Para nós é uma grande satisfação tê-la como nosso autora.\n\n"
        "Forte abraço,\n\n"
        "Patrícia Melo e Luciana Félix"
    )
    pdf.multi_cell(0, 7, texto_apresentacao)

    # --- PÁGINA 2: PROJETO ---
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "Projeto Editorial", ln=True)
    pdf.ln(5)
    
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 8, f"Livro: {dados['livro']}", ln=True)
    pdf.cell(0, 8, f"Autor: {dados['cliente']}", ln=True)
    pdf.ln(2)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, "Especificações:", ln=True)
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 7, f"- Laudas: {dados['laudas']:.0f}", ln=True)
    pdf.cell(0, 7, f"- Páginas estimadas: {dados['paginas']}", ln=True)
    pdf.cell(0, 7, f"- Formato: {dados['formato']}", ln=True)
    pdf.cell(0, 7, f"- Miolo: {dados['miolo']}", ln=True)
    pdf.cell(0, 7, f"- Capa: {dados['capa']}", ln=True)
    pdf.cell(0, 7, f"- Acabamento: {dados['acabamento']}", ln=True)
    pdf.ln(5)

    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, "Produção editorial Premium", ln=True)
    pdf.set_font("helvetica", size=11)
    
    itens = [
        "- Copidesque e preparação de textos (revisão ortográfica e padronização conforme ABNT), diagramação, revisão pós-diagramação, conferências e fechamento de arquivo.",
        "- ISBN, Capa; ficha catalográfica, código de barras.",
        "- Conteúdo publicado sob o selo editorial Matrioska Editora.",
        "- Edições impressa e digital poderão ser disponibilizadas na loja virtual da editora e nas principais plataformas de e-commerce e livrarias virtuais (Amazon e marketplaces)."
    ]
    for item in itens:
        pdf.multi_cell(0, 6, item)
        pdf.ln(2)

    # --- PÁGINA 3: INVESTIMENTO ---
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "Proposta de investimento:", ln=True)
    pdf.ln(5)
    
    pdf.set_font("helvetica", size=12)
    valor_f = f"R$ {dados['total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    extenso = valor_por_extenso(dados['total'])
    
    texto_investimento = (
        f"- {valor_f} {extenso} para custeio da produção editorial "
        "(etapas de copidesque, projeto gráfico e diagramação, revisão pós-diagramação, "
        "capa, conferências e fechamento de arquivos: para impressão e e-books);\n\n"
        "- Não inclui exemplares impressos;\n\n"
        "- Condição de pagamento: 40% na assinatura do contrato; 30% após 30 dias "
        "e o restante no envio do arquivo para a gráfica.\n\n"
        "Orçamento válido por 30 dias."
    )
    pdf.multi_cell(0, 7, texto_investimento)
    
    pdf.ln(20)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, obter_data_formatada(), ln=True)

    return bytes(pdf.output())

# --- 3. INTERFACE STREAMLIT ---
st.set_page_config(page_title="Editora Matrioska - Orçamentador", layout="wide")

if 'formatos_custom' not in st.session_state:
    st.session_state['formatos_custom'] = {}

with st.sidebar:
    if os.path.exists(NOME_LOGO): st.image(NOME_LOGO, width=150)
    st.header("Configuração de Preços")
    p_copidesque = st.number_input("Copidesque (por lauda): R$", value=6.0)
    p_diagramacao = st.number_input("Diagramação (por página): R$", value=5.0)
    p_revisao = st.number_input("Revisão (por página): R$", value=4.0)
    p_capa = st.number_input("Capa: R$", value=500.0)
    p_isbn = st.number_input("ISBN e Fichas: R$", value=300.0)
    p_epub = st.number_input("E-pub (por página): R$", value=2.50)
    p_taxa_editora = st.number_input("Taxa da editora: R$", value=3000.0)

st.title("📚 Sistema de Orçamento Editorial - Matrioska")

col1, col2 = st.columns(2)

with col1:
    nome_cliente = st.text_input("Nome do Autor(a):")
    nome_livro = st.text_input("Nome do Livro:") 
    arquivo_word = st.file_uploader("Subir Manuscrito (.docx)", type=["docx"])
    
    total_caracteres = 0
    if arquivo_word:
        total_caracteres = contar_caracteres_oficial_word(arquivo_word)
        st.success(f"{total_caracteres} caracteres detectados.")
    else:
        total_caracteres = st.number_input("Total de caracteres manualmente:", value=0)

    st.subheader("Elementos Extras")
    pag_extras = st.number_input("Soma de páginas extras:", min_value=0, value=0)

with col2:
    opcoes_formato = ["14x21", "16x23", "17x24", "Personalizado"] + list(st.session_state['formatos_custom'].keys())
    formato_sel = st.selectbox("Formato do Livro:", opcoes_formato)
    
    meta = {"14x21": 1700, "16x23": 2200, "17x24": 2900}.get(formato_sel, 0)
    if formato_sel == "Personalizado":
        n_f = st.text_input("Nome Formato:"); m_f = st.number_input("Caracteres/Pág:", value=1500)
        if st.button("Salvar Formato"): 
            st.session_state['formatos_custom'][n_f] = m_f
            st.rerun()
    elif formato_sel not in ["14x21", "16x23", "17x24"]:
        meta = st.session_state['formatos_custom'][formato_sel]

    # NOVAS OPÇÕES SOLICITADAS
    miolo_sel = st.selectbox("Miolo:", ["PB", "Colorido", "PB com caderno colorido"])
    capa_sel = st.selectbox("Capa:", ["4x0", "4x1", "4x4"])
    acabamento_sel = st.selectbox("Acabamento:", ["Brochura", "Capa Dura"])

    incluir_epub = st.checkbox("Incluir E-pub?", value=True)

# --- 4. CÁLCULOS ---
qtd_laudas = total_caracteres / 2000
custo_copidesque = qtd_laudas * p_copidesque
paginas_texto = math.ceil(total_caracteres / meta) if meta > 0 else 0
total_paginas = paginas_texto + pag_extras

custo_diag = total_paginas * p_diagramacao
custo_revisao = total_paginas * p_revisao
custo_epub = (total_paginas * p_epub) if incluir_epub else 0.0
custos_fixos = p_capa + p_isbn
valor_total = custo_copidesque + custo_diag + custo_revisao + custo_epub + custos_fixos + p_taxa_editora

dados_finais = {
    "cliente": nome_cliente, "livro": nome_livro, "caracteres": total_caracteres, 
    "laudas": qtd_laudas, "formato": formato_sel, "miolo": miolo_sel, "capa": capa_sel, 
    "acabamento": acabamento_sel, "paginas": total_paginas, "total": valor_total
}

st.markdown("---")
if total_caracteres > 0:
    st.metric("Investimento Total", f"R$ {valor_total:,.2f}")
    
    if st.button("💾 Salvar Orçamento"):
        payload = {"cliente": nome_cliente, "caracteres": total_caracteres, "formato": formato_sel, "paginas": total_paginas, "valor_total": valor_total}
        supabase.table("orcamentos").insert(payload).execute()
        st.success("Salvo no banco de dados!")

    try:
        pdf_bytes = gerar_pdf_matrioska(dados_finais)
        st.download_button(
            label="📥 Gerar Proposta Editorial (PDF)", 
            data=pdf_bytes, 
            file_name=f"Proposta_{nome_livro}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
