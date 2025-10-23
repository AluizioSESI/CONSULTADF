# Consulta Descritivo de Função (Streamlit)
# Arquivo: app.py

import streamlit as st
import pandas as pd
import os
from io import StringIO

# Tentar importar rapidfuzz, com fallback para fuzzywuzzy
try:
    from rapidfuzz import process, fuzz
    FUZZY_AVAILABLE = True
    FUZZY_LIB = "rapidfuzz"
except ImportError:
    try:
        from fuzzywuzzy import process, fuzz
        from fuzzywuzzy import process as fuzzy_process
        FUZZY_AVAILABLE = True
        FUZZY_LIB = "fuzzywuzzy"
    except ImportError:
        FUZZY_AVAILABLE = False
        FUZZY_LIB = "none"

st.set_page_config(page_title='Consulta Descritivo de Função', layout='centered')
st.title('Consulta de Descritivo de Função')
st.markdown('Busque pelo **nome da função** e veja as atividades e o CBO.')

# Adicionar informação sobre a biblioteca de busca
if FUZZY_AVAILABLE:
    st.sidebar.success(f"✓ Usando {FUZZY_LIB} para busca fuzzy")
else:
    st.sidebar.error("✗ Biblioteca fuzzy não disponível")

# Função utilitária para carregar dados
@st.cache_data
def load_df_from_file(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        if uploaded_file.name.lower().endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.lower().endswith(('.xls', '.xlsx')):
            return pd.read_excel(uploaded_file)
        else:
            st.error('Formato não suportado. Envie CSV ou Excel.')
            return None
    except Exception as e:
        st.error(f'Erro ao ler arquivo: {e}')
        return None

# Base de exemplo (se usuário não enviar arquivo)
@st.cache_data
def sample_df():
    data = {
        'Função': [
            'Analista de Recursos Humanos',
            'Enfermeiro',
            'Técnico em Enfermagem',
            'Coordenador de Vendas',
            'Auxiliar Administrativo',
            'Analista de Remuneração'
        ],
        'CBO': ['2524-05', '2235-10', '3222-05', '1421-10', '4110-05', '2524-10'],
        'Atividades': [
            'Recrutamento; Seleção; Treinamento e desenvolvimento; Administração de pessoal',
            'Assistência de enfermagem, administração de medicamentos, plantões, cuidados ao paciente',
            'Cuidados básicos de enfermagem; curativos; aferição de sinais vitais; suporte à equipe',
            'Gestão de equipe de vendas; acompanhamento de metas; planejamento comercial',
            'Atendimento ao cliente; organização de documentos; apoio administrativo',
            'Cálculo de salários; benefícios; pesquisa salarial; estrutura de cargos e salários'
        ]
    }
    return pd.DataFrame(data)

# Nome do seu arquivo Excel - ALTERE PARA O NOME DO SEU ARQUIVO
SEU_ARQUIVO_EXCEL = "base_descritivo_funcoes.xlsx"  # ⬅️ ALTERE ESTE NOME!

@st.cache_data
def load_seu_arquivo():
    try:
        if os.path.exists(SEU_ARQUIVO_EXCEL):
            df = pd.read_excel(SEU_ARQUIVO_EXCEL)
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Erro ao carregar {SEU_ARQUIVO_EXCEL}: {e}")
        return None

st.sidebar.header('Configurações')

# Opções de carregamento
uploaded = st.sidebar.file_uploader('Enviar base (CSV / XLSX)', type=['csv', 'xls', 'xlsx'])
use_seu_arquivo = st.sidebar.checkbox(f'Carregar {SEU_ARQUIVO_EXCEL} automaticamente', value=True)
use_sample = st.sidebar.checkbox('Usar base de exemplo se necessário', value=True)

# Carrega dataframe
df = None
source = ""

# 1. Tenta carregar arquivo enviado
if uploaded is not None:
    df = load_df_from_file(uploaded)
    if df is not None:
        source = "upload"

# 2. Tenta carregar seu arquivo específico
if df is None and use_seu_arquivo:
    df = load_seu_arquivo()
    if df is not None:
        source = "auto"
        st.sidebar.success(f"✅ Base carregada: {SEU_ARQUIVO_EXCEL}")

# 3. Usa base de exemplo
if df is None and use_sample:
    df = sample_df()
    source = "sample"
    st.sidebar.info("📋 Usando base de exemplo")

if df is None:
    st.error('''
    ❌ Nenhuma base carregada. 
    
    **Soluções:**
    1. **Renomeie seu arquivo Excel para '{SEU_ARQUIVO_EXCEL}'** e coloque na mesma pasta do app
    2. **Ou faça upload manual** usando o botão acima
    3. **Ou use a base de exemplo** marcando a opção abaixo
    ''')
    
    # Mostra arquivos disponíveis
    try:
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        excel_files = [f for f in files if f.endswith(('.xlsx', '.xls', '.csv'))]
        if excel_files:
            st.info("📂 Arquivos encontrados no diretório:")
            for file in excel_files:
                st.write(f"- {file}")
            st.info(f"💡 **Dica:** Renomeie um desses arquivos para '{SEU_ARQUIVO_EXCEL}'")
    except Exception as e:
        st.write("Não foi possível listar os arquivos do diretório")
    
    st.stop()

# Mostra fonte dos dados
if source == "upload":
    st.sidebar.info("📤 Fonte: Arquivo enviado")
elif source == "auto":
    st.sidebar.info("📁 Fonte: Arquivo do repositório")
elif source == "sample":
    st.sidebar.info("📋 Fonte: Base de exemplo")

# ... (o resto do código permanece igual) ...

# Resto do código (normalização de colunas, busca, etc.) - mantenha igual ao anterior
