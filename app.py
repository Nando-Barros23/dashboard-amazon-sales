import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página (Melhoria 1: Título Profissional para SEO/Navegador)
st.set_page_config(page_title="Portfólio Data Science - Análise Amazon", page_icon="🛍️", layout="wide")

# 2. Carregamento e Tratamento
@st.cache_data
def carregar_dados():
    df = pd.read_csv("amazon.csv")
    
    # --- LIMPEZA DE PREÇOS ---
    cols_precos = ['discounted_price', 'actual_price']
    for col in cols_precos:
        df[col] = df[col].astype(str).str.replace('₹', '').str.replace(',', '').str.replace('$', '')
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # --- CONVERSÃO DE MOEDA (Rúpia -> Real) ---
    df['preco_reais'] = df['discounted_price'] * 0.07
    
    # --- LIMPEZA DE NOTAS ---
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
    df['rating_count'] = df['rating_count'].astype(str).str.replace(',', '')
    df['rating_count'] = pd.to_numeric(df['rating_count'], errors='coerce').fillna(0)
    
    # --- TRADUÇÃO DE CATEGORIAS ---
    df['category_main'] = df['category'].astype(str).str.split('|').str[0]
    
    dicionario_traducao = {
        'Electronics': 'Eletrônicos',
        'Computers&Accessories': 'Informática',
        'Home&Kitchen': 'Casa e Cozinha',
        'OfficeProducts': 'Escritório',
        'MusicalInstruments': 'Instrumentos Musicais',
        'Health&PersonalCare': 'Saúde e Beleza',
        'HomeImprovement': 'Ferramentas e Construção',
        'Toys&Games': 'Brinquedos',
        'Car&Motorbike': 'Automotivo'
    }
    df['categoria_pt'] = df['category_main'].map(dicionario_traducao).fillna(df['category_main'])

    # Nome curto para gráficos
    df['nome_curto'] = df['product_name'].apply(lambda x: x[:35] + '...' if isinstance(x, str) and len(x) > 35 else x)
    
    return df

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro: {e}")
    st.stop()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header(" Filtros")
    
    # Filtro de Categoria
    lista_cats = sorted(df['categoria_pt'].unique())
    cat_filtro = st.multiselect("Selecione a Categoria:", lista_cats)
    
    # Filtro de Preço (Melhoria 2: Slider Formatado)
    preco_min = float(df['preco_reais'].min())
    preco_max = float(df['preco_reais'].max())
    
    preco_range = st.slider(
        "Faixa de Preço (R$)",
        min_value=preco_min,
        max_value=preco_max,
        value=(preco_min, preco_max),
        step=10.0,            # Pula de 10 em 10 reais (mais fácil de arrastar)
        format="R$ %.2f"      # Mostra o R$ bonitinho
    )
    
    st.markdown("---")
    
    # Filtra os dados antes de criar o botão de download
    df_filtrado = df.copy()
    if cat_filtro:
        df_filtrado = df_filtrado[df_filtrado['categoria_pt'].isin(cat_filtro)]

    df_filtrado = df_filtrado[
        (df_filtrado['preco_reais'] >= preco_range[0]) & 
        (df_filtrado['preco_reais'] <= preco_range[1])
    ]
    
    # (Melhoria 3: Botão de Download)
    st.write("###  Exportar Dados")
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar Tabela Filtrada (.csv)",
        data=csv,
        file_name="dados_amazon_filtrados.csv",
        mime="text/csv",
        help="Baixe os dados que você filtrou acima para usar no Excel."
    )

# --- DASHBOARD PRINCIPAL ---
st.title(" Dashboard de Vendas Amazon")
st.markdown("Visão estratégica de produtos, preços e avaliações convertidos para **Reais (BRL)**.")

# Métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric(" Preço Médio", f"R$ {df_filtrado['preco_reais'].mean():.2f}")
col2.metric(" Produtos Listados", len(df_filtrado))
col3.metric(" Nota Média", f"{df_filtrado['rating'].mean():.1f} / 5.0")
col4.metric(" Total Avaliações", f"{df_filtrado['rating_count'].sum():,.0f}".replace(",", "."))

st.markdown("---")

# Gráficos
st.subheader("Quais categorias dominam o mercado?")
fig_tree = px.treemap(
    df_filtrado, 
    path=['categoria_pt'], 
    values='rating_count',
    color='rating',
    color_continuous_scale='RdBu',
    title="Volume de Vendas por Categoria"
)
fig_tree.update_layout(height=450)
st.plotly_chart(fig_tree, use_container_width=True)

col_g1, col_g2 = st.columns([1, 1])

with col_g1:
    st.subheader("Top 10 Mais Caros")
    top_caros = df_filtrado.nlargest(10, 'preco_reais').sort_values('preco_reais', ascending=True)
    fig_bar = px.bar(
        top_caros,
        x='preco_reais',
        y='nome_curto',
        orientation='h',
        text_auto='.2s',
        color='preco_reais',
        color_continuous_scale='Viridis'
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Preço (R$)",
        yaxis_title="",
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_g2:
    st.subheader("Distribuição de Preços")
    fig_box = px.box(
        df_filtrado, 
        x="categoria_pt", 
        y="preco_reais",
        color="categoria_pt",
    )
    fig_box.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="Preço (R$)",
        showlegend=False,
        xaxis={'tickangle': -45}
    )
    st.plotly_chart(fig_box, use_container_width=True)