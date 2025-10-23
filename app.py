# Consulta Descritivo de Função (Streamlit)
# Arquivo: app.py

import streamlit as st
import pandas as pd
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

# Normaliza nomes de colunas
cols = {c.lower(): c for c in df.columns}
fun_col = None
cbo_col = None
act_col = None

for lc, orig in cols.items():
    if 'fun' in lc:
        fun_col = orig
    if 'cbo' == lc:
        cbo_col = orig
    if 'ativ' in lc:
        act_col = orig

if fun_col is None or cbo_col is None or act_col is None:
    st.error('Colunas esperadas não encontradas. Certifique-se de ter colunas: Função, CBO, Atividades.')
    st.write('Colunas detectadas:', list(df.columns))
    st.stop()

# Preprocessa coluna de função para busca
df['__fun_lower'] = df[fun_col].astype(str).str.strip().str.lower()

st.write('Base carregada — linhas:', len(df))
st.write('📋 Funções disponíveis:', ', '.join(df[fun_col].astype(str).tolist()))

query = st.text_input('Nome da função para buscar', value='', placeholder='Ex: Analista de RH, Enfermeiro...')

if FUZZY_AVAILABLE:
    min_score = st.slider('Sensibilidade da busca (fuzzy) — menor = mais permissiva', 50, 100, 80)

def fuzzy_search(query, choices, min_score, limit=10):
    """Função unificada para busca fuzzy"""
    if FUZZY_LIB == "rapidfuzz":
        matches = process.extract(query, choices, scorer=fuzz.WRatio, limit=limit)
        return [(match[0], match[1], match[2]) for match in matches]
    elif FUZZY_LIB == "fuzzywuzzy":
        matches = process.extract(query, choices, limit=limit)
        return [(match[0], match[1], idx) for idx, match in enumerate(matches)]
    return []

if query:
    # Busca exata
    mask_exact = df['__fun_lower'] == query.strip().lower()
    results = df[mask_exact]

    if not results.empty:
        st.success(f'🎯 Encontrado {len(results)} correspondência(s) exata(s)')
        for idx, row in results.iterrows():
            st.subheader(row[fun_col])
            st.write('**CBO:**', row[cbo_col])
            st.markdown('**Atividades:**')
            acts = str(row[act_col]).replace('\r', '\n')
            sep = ';' if ';' in acts else '\n'
            for a in [x.strip() for x in acts.split(sep) if x.strip()]:
                st.write('• ' + a)
    else:
        if FUZZY_AVAILABLE:
            # Busca fuzzy
            choices = df['__fun_lower'].tolist()
            matches = fuzzy_search(query, choices, min_score, limit=10)
            good = [m for m in matches if m[1] >= min_score]
            
            if not good:
                st.warning(f'❌ Nenhuma correspondência com score ≥ {min_score}%')
                st.write('🔍 Melhores sugestões:')
                for m in matches[:3]:
                    original_name = df[df['__fun_lower'] == m[0]].iloc[0][fun_col]
                    st.write(f"- {original_name} — {m[1]:.0f}%")
            else:
                st.success(f'✅ {len(good)} sugestão(ões) encontrada(s)')
                for m in good:
                    row = df[df['__fun_lower'] == m[0]].iloc[0]
                    st.subheader(f"{row[fun_col]} — {m[1]:.0f}%")
                    st.write('**CBO:**', row[cbo_col])
                    st.markdown('**Atividades:**')
                    acts = str(row[act_col]).replace('\r', '\n')
                    sep = ';' if ';' in acts else '\n'
                    for a in [x.strip() for x in acts.split(sep) if x.strip()]:
                        st.write('• ' + a)
        else:
            # Busca sem fuzzy - melhorada
            st.warning("⚡ Buscando sem biblioteca fuzzy...")
            
            # Busca por substring
            mask_substring = df['__fun_lower'].str.contains(query.strip().lower(), na=False)
            results_sub = df[mask_substring]
            
            if not results_sub.empty:
                st.success(f'🔍 Encontrado {len(results_sub)} correspondência(s) por texto parcial')
                for idx, row in results_sub.iterrows():
                    st.subheader(row[fun_col])
                    st.write('**CBO:**', row[cbo_col])
                    st.markdown('**Atividades:**')
                    acts = str(row[act_col]).replace('\r', '\n')
                    sep = ';' if ';' in acts else '\n'
                    for a in [x.strip() for x in acts.split(sep) if x.strip()]:
                        st.write('• ' + a)
            else:
                # Busca por palavras-chave
                query_words = [w for w in query.strip().lower().split() if len(w) > 3]
                if query_words:
                    st.info(f"🔎 Tentando busca por palavras-chave: {', '.join(query_words)}")
                    mask_words = pd.Series([False] * len(df))
                    for word in query_words:
                        mask_words = mask_words | df['__fun_lower'].str.contains(word, na=False)
                    
                    results_words = df[mask_words]
                    if not results_words.empty:
                        st.success(f'✅ Encontrado {len(results_words)} correspondência(s) por palavras-chave')
                        for idx, row in results_words.iterrows():
                            st.subheader(row[fun_col])
                            st.write('**CBO:**', row[cbo_col])
                            st.markdown('**Atividades:**')
                            acts = str(row[act_col]).replace('\r', '\n')
                            sep = ';' if ';' in acts else '\n'
                            for a in [x.strip() for x in acts.split(sep) if x.strip()]:
                                st.write('• ' + a)
                    else:
                        st.error('❌ Nenhuma correspondência encontrada.')
                        st.info("💡 **Dicas:** Tente termos mais curtos ou sinônimos")
                else:
                    st.error('❌ Nenhuma correspondência encontrada.')
                    st.info("💡 **Dica:** Use palavras-chave mais específicas")

# Download
csv = df.drop(columns=['__fun_lower']).to_csv(index=False)
st.download_button('💾 Baixar base atual (CSV)', data=csv, file_name='base_descritivo_funcoes.csv', mime='text/csv')

# Instruções de instalação
if not FUZZY_AVAILABLE:
    st.error("""
    **🚨 Para buscas mais eficientes, instale uma biblioteca fuzzy:**
    
    **Opção 1 (Recomendada):**
    ```bash
    pip install rapidfuzz
    ```
    
    **Opção 2:**
    ```bash
    pip install fuzzywuzzy python-levenshtein
    ```
    """)

st.info('💡 **Dica:** Para melhorar a busca, use termos específicos como "Analista RH" em vez de "analista de recursos humanos"')
