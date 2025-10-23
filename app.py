# Consulta Descritivo de Função (Streamlit)
# Arquivo: app.py
# Objetivo: ambiente simples para consultar descritivos de função por nome da função
# Saída: atividades (lista/texto) e CBO (código)
# Requisitos:
#   pip install streamlit pandas rapidfuzz openpyxl
# Uso:
#   1. Salve este arquivo como app.py
#   2. Prepare um arquivo CSV com colunas: "Função", "CBO", "Atividades"
#      - Exemplo de linha:
#        "Analista de RH", "2524-05", "Recrutamento; Seleção; Treinamento"
#   3. Execute: streamlit run app.py
#   4. No navegador, busque pelo nome da função (aceita buscas parciais e fuzzy)

# Observações:
# - O campo 'Atividades' pode ser um texto longo com itens separados por ';' ou '\n'.
# - O app faz match exato primeiro e, se não encontrar, apresenta as melhores correspondências (fuzzy).
# - Permite upload de CSV/Excel e também usar a base de exemplo embutida.

import streamlit as st
import pandas as pd
from io import StringIO

# Tentar importar rapidfuzz, com fallback para fuzzywuzzy ou busca simples
try:
    from rapidfuzz import process, fuzz
    FUZZY_AVAILABLE = True
    FUZZY_LIB = "rapidfuzz"
except ImportError:
    try:
        from fuzzywuzzy import process, fuzz
        from fuzzywuzzy.utils import full_process
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
    st.sidebar.info(f"Usando {FUZZY_LIB} para busca fuzzy")
else:
    st.sidebar.warning("Biblioteca fuzzy não encontrada. Usando busca simples.")

# Função utilitária para carregar dados
@st.cache_data
def load_df_from_file(uploaded_file):
    if uploaded_file is None:
        return None
    fname = uploaded_file.name.lower()
    try:
        if fname.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif fname.endswith(('.xls', '.xlsx')):
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
            'Auxiliar Administrativo'
        ],
        'CBO': ['2524-05', '2235-10', '3222-05', '1421-10', '4110-05'],
        'Atividades': [
            'Recrutamento; Seleção; Treinamento e desenvolvimento; Administração de pessoal',
            'Assistência de enfermagem, administração de medicamentos, plantões, cuidados ao paciente',
            'Cuidados básicos de enfermagem; curativos; aferição de sinais vitais; suporte à equipe',
            'Gestão de equipe de vendas; acompanhamento de metas; planejamento comercial',
            'Atendimento ao cliente; organização de documentos; apoio administrativo'
        ]
    }
    return pd.DataFrame(data)

st.sidebar.header('Configurações')
uploaded = st.sidebar.file_uploader('Enviar base (CSV / XLSX)', type=['csv', 'xls', 'xlsx'])
use_sample = st.sidebar.checkbox('Usar base de exemplo', value=True)

# Carrega dataframe
df = None
if uploaded is not None:
    df = load_df_from_file(uploaded)
    if df is None:
        st.stop()

if df is None and use_sample:
    df = sample_df()

if df is None:
    st.warning('Nenhuma base carregada. Faça upload de um CSV/Excel ou habilite a base de exemplo na barra lateral.')
    st.stop()

# Normaliza nomes de colunas (tolerância a variações)
cols = {c.lower(): c for c in df.columns}
required = ['função', 'funcao', 'cbo', 'atividades', 'atividades/atividade']
# Mapeia colunas mais prováveis
fun_col = None
cbo_col = None
act_col = None
for lc, orig in cols.items():
    if 'fun' in lc:
        fun_col = orig
    if 'cbo' == lc or 'cbo' in lc:
        cbo_col = orig
    if 'ativ' in lc or 'atividade' in lc:
        act_col = orig

# Se não encontrou colunas essenciais, mostra instrução
if fun_col is None or cbo_col is None or act_col is None:
    st.error('Colunas esperadas não encontradas. Certifique-se de ter colunas com nomes parecidos com: Função, CBO, Atividades.')
    st.write('Colunas detectadas:', list(df.columns))
    st.stop()

# Preprocessa coluna de função para busca
df['__fun_lower'] = df[fun_col].astype(str).str.strip()

st.write('Base carregada — linhas:', len(df))

query = st.text_input('Nome da função para buscar', value='')
min_score = st.slider('Sensibilidade da busca (fuzzy) — menor = mais permissiva', 50, 100, 80)

if query:
    # Busca exata (case-insensitive)
    mask_exact = df['__fun_lower'].str.lower() == query.strip().lower()
    results = df[mask_exact]

    if not results.empty:
        st.success(f'Encontrado {len(results)} correspondência(s) exata(s)')
        for idx, row in results.iterrows():
            st.subheader(row[fun_col])
            st.write('CBO:', row[cbo_col])
            st.markdown('**Atividades:**')
            # Formata atividades em lista
            acts = str(row[act_col]).replace('\r', '\n')
            sep = ';' if ';' in acts else '\n'
            for a in [x.strip() for x in acts.split(sep) if x.strip()]:
                st.write('- ' + a)
    else:
        # Busca fuzzy
        choices = df['__fun_lower'].tolist()
        matches = process.extract(query, choices, scorer=fuzz.WRatio, limit=10)
        # matches: list of (choice, score, index)
        # Filtra por min_score
        good = [m for m in matches if m[1] >= min_score]
        if not good:
            st.warning('Nenhuma correspondência com o nível de sensibilidade escolhido. Tente reduzir a exigência ou verifique sua digitação.')
            st.write('Melhores sugestões:')
            for m in matches[:5]:
                st.write(f"{m[0]} — {m[1]}%")
        else:
            st.success(f'{len(good)} sugestão(ões) encontrada(s) (score >= {min_score})')
            for m in good:
                choice_text = m[0]
                score = m[1]
                # recupera a linha correspondente
                row = df[df['__fun_lower'] == choice_text].iloc[0]
                st.subheader(f"{row[fun_col]} — {score}%")
                st.write('CBO:', row[cbo_col])
                st.markdown('**Atividades:**')
                acts = str(row[act_col]).replace('\r', '\n')
                sep = ';' if ';' in acts else '\n'
                for a in [x.strip() for x in acts.split(sep) if x.strip()]:
                    st.write('- ' + a)

# Permite baixar a base atual (por segurança/backup)
csv = df.drop(columns=['__fun_lower']).to_csv(index=False)
st.download_button('Baixar base atual (CSV)', data=csv, file_name='base_descritivo_funcoes.csv', mime='text/csv')

st.info('Dica: para melhorar a busca, padronize os nomes das funções (ex.: sem abreviações) e mantenha as atividades separadas por ponto e vírgula ou quebra de linha.')

# Fim do app
