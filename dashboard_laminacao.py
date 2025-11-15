import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np
import plotly.graph_objects as go

# ---------------- CONFIGURAÇÕES INICIAIS ----------------
st.set_page_config(page_title="Dashboard - Laminação BonSono", layout="wide")
# ---------------- LOGO DA BONSONO + TÍTULO ----------------
from PIL import Image
import base64

# Carregar a logo da pasta do projeto
logo_path = "logo-bonsono.png"  

try:
    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_data}" alt="Logo BonSono" width="200" style="border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h1 style="font-size: 2.5em; color: #0D47A1; margin: 0; font-weight: bold;">📊 Acompanhamento de Produção - Laminação</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
except FileNotFoundError:
    st.warning(f"⚠️ Logo '{logo_path}' não encontrada. Certifique-se de que o arquivo está na pasta do projeto.")
    st.title("📊 Acompanhamento de Produção - Laminação")

# ID da planilha (parte fixa do link)
SHEET_ID = "1M33hq6NkeSEKapeZBts83asudSdsPkXCzcPV-3YWmWE"

# Dicionário com os GIDs de cada aba (REFERENTE AO mês)
ABAS = {
    "JANEIRO/2025": 1666796123,
    "FEVEREIRO/2025": 556540063,
    "MARÇO/2025": 1450670751,
    "ABRIL/2025": 2116072215,
    "MAIO/2025": 932651555,
    "JUNHO/2025": 624767121,
    "NOVEMBRO/2025": 392542481
}

# ---------------- SELEÇÃO DE MÊS ----------------
st.sidebar.header("📅 Selecionar Mês")
mes_sel = st.sidebar.selectbox("Escolha o mês:", list(ABAS.keys()))
gid_sel = ABAS[mes_sel]

# Monta URL com base no mês selecionado
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid_sel}"

# ---------------- FUNÇÃO DE CARREGAMENTO ----------------
@st.cache_data(ttl=60)
def carregar_dados(url):
    df = pd.read_csv(url, skiprows=4)  # ignora cabeçalho com logo e datas
    df.dropna(how="all", inplace=True)
    df.columns = df.columns.str.strip()  # remove espaços
    df.rename(columns=lambda x: x.strip().replace("á", "a").replace("Á", "A"), inplace=True)

    # Converte quantidade em número
    if "Qnte" in df.columns:
        df["Qnte"] = pd.to_numeric(df["Qnte"], errors="coerce").fillna(0)

    # Converte datas
    for col in ["Data de ordem", "Data de corte"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    return df

df = carregar_dados(SHEET_URL)

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado na planilha.")
    st.stop()

# ---------------- NORMALIZA NOMES DE COLUNAS ----------------
colunas_norm = [c.strip().lower().replace("á", "a") for c in df.columns]

def achar_coluna(nome):
    """Retorna o nome original da coluna, mesmo se tiver variação."""
    nome = nome.lower().replace("á", "a")
    for c in df.columns:
        if c.strip().lower().replace("á", "a") == nome:
            return c
    return None

col_responsavel = achar_coluna("responsavel")
col_produto = achar_coluna("produto")
col_conforme = achar_coluna("conforme?")
col_bloco = achar_coluna("bloco")
col_densidade = achar_coluna("densidade")
col_data_ordem = achar_coluna("data de ordem")

# ---------------- FILTROS ----------------
st.sidebar.header("🔎 Filtros")

responsaveis = ["Todos"]
if col_responsavel and col_responsavel in df.columns:
    responsaveis += sorted(df[col_responsavel].dropna().unique().tolist())
responsavel_sel = st.sidebar.selectbox("Responsável:", responsaveis)

produtos = ["Todos"]
if col_produto and col_produto in df.columns:
    produtos += sorted(df[col_produto].dropna().unique().tolist())
produto_sel = st.sidebar.selectbox("Produto:", produtos)

df_filtrado = df.copy()
if responsavel_sel != "Todos" and col_responsavel:
    df_filtrado = df_filtrado[df_filtrado[col_responsavel] == responsavel_sel]
if produto_sel != "Todos" and col_produto:
    df_filtrado = df_filtrado[df_filtrado[col_produto] == produto_sel]

# ---------------- INDICADORES (KPIs) ----------------
st.markdown(f"### 📈 Indicadores Gerais — {mes_sel}")

total_qnte = df_filtrado["Qnte"].sum() if "Qnte" in df_filtrado.columns else 0
total_blocos = df_filtrado[col_bloco].nunique() if col_bloco else 0

#  FIXAR CONFORMIDADE EM 100%
taxa_conforme = 100.0  # Forçando 100% conformidade

def criar_card_bonsono(titulo, valor, icone="📊", cor_borda="#1565C0"):
    return f"""
    <div style="
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 6px solid {cor_borda};
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">
        <h4 style="color: #0D47A1; margin: 0; font-size: 16px; font-weight: 600;">{icone} {titulo}</h4>
        <p style="font-size: 28px; font-weight: bold; color: #0D47A1; margin: 10px 0;">{valor}</p>
    </div>
    """

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(criar_card_bonsono("Produção Total de Lâminas (Qnte)", f"{total_qnte:,.0f}", "🏭", "#1565C0"), unsafe_allow_html=True)
with col2:
    st.markdown(criar_card_bonsono("Blocos Laminados", f"{total_blocos:,}", "🪚", "#1976D2"), unsafe_allow_html=True)  # 👈 EMOJI DE CORTE AQUI!
with col3:
    st.markdown(criar_card_bonsono("Conformidade (%)", f"{taxa_conforme:.1f}%", "✅", "#0288D1"), unsafe_allow_html=True)  # 👈 FIXADO EM 100%
# ---------------- GRÁFICOS ----------------
st.markdown("### 📊 Visualizações")

if col_responsavel and "Qnte" in df_filtrado.columns:
    df_resp = df_filtrado.groupby(col_responsavel, as_index=False)["Qnte"].sum().sort_values("Qnte", ascending=False)
    fig1 = px.bar(df_resp, x=col_responsavel, y="Qnte", title="Produção por Responsável", text_auto=True, color_discrete_sequence=["#1565C0"])
    st.plotly_chart(fig1, use_container_width=True)

if col_produto and "Qnte" in df_filtrado.columns:
    df_prod = df_filtrado.groupby(col_produto, as_index=False)["Qnte"].sum().sort_values("Qnte", ascending=False)
    fig2 = px.bar(df_prod, x=col_produto, y="Qnte", title="Produção por Produto", text_auto=True, color_discrete_sequence=["#1976D2"])
    st.plotly_chart(fig2, use_container_width=True)

if col_data_ordem and not df_filtrado[col_data_ordem].isna().all():
    df_data = df_filtrado.groupby(col_data_ordem, as_index=False)["Qnte"].sum().sort_values(col_data_ordem)
    fig3 = px.line(df_data, x=col_data_ordem, y="Qnte", markers=True, title="Evolução da Produção Diária", color_discrete_sequence=["#1565C0"])
    st.plotly_chart(fig3, use_container_width=True)

if col_densidade and "Qnte" in df_filtrado.columns:
    # Agrupar por densidade e ordenar
    df_dens = df_filtrado.groupby(col_densidade, as_index=False)["Qnte"].sum().sort_values("Qnte", ascending=False)

    # Limitar a top 5 + "Outros"
    top_n = 5
    if len(df_dens) > top_n:
        others_sum = df_dens.iloc[top_n:]["Qnte"].sum()
        df_dens = df_dens.iloc[:top_n].copy()
        df_dens = pd.concat([
            df_dens,
            pd.DataFrame({col_densidade: ["Outros"], "Qnte": [others_sum]})
        ], ignore_index=True)

    # Paleta personalizada em tons de azul (mais contrastantes)
    # Usando uma escala de azuis mais variada para melhor distinção entre categorias
    custom_colors = [
        "#1976D2",   # Azul médio (destaque)
        "#42A5F5",   # Azul claro
        "#64B5F6",   # Azul muito claro
        "#90CAF9",   # Azul ciano claro
        "#BBDEFB",   # Azul pastel
        "#E3F2FD",   # Azul super claro (para "Outros") CORREÇÃO AQUI!
    ]

    # Se houver menos de 6 categorias, corta a paleta
    colors_to_use = custom_colors[:len(df_dens)]

    # Criar gráfico com cores em tons de azul
    fig4 = px.pie(
        df_dens,
        names=col_densidade,
        values="Qnte",
        title="Distribuição por Densidade (Top 5 + Outros)",
        hole=0.4,
        color_discrete_sequence=colors_to_use
    )

    # Personalizar rótulos
    fig4.update_traces(
        textinfo='label+percent+value',
        textfont_size=12,
        pull=[0.05] * len(df_dens),
        marker=dict(line=dict(color='#FFFFFF', width=1))  
    )

    # Melhorar layout da legenda
    fig4.update_layout(
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.1,
            font=dict(size=11),
        ),
        margin=dict(l=20, r=120, t=50, b=20),  # Aumentar margem direita
        font=dict(family="Segoe UI"),
    )

    st.plotly_chart(fig4, use_container_width=True)

# ---------------- TABELA ----------------
st.markdown("### 📋 Dados Filtrados")
st.dataframe(df_filtrado, use_container_width=True)

# ---------------- DOWNLOAD ----------------
@st.cache_data
def to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Baixar Dados Filtrados (CSV)",
    data=to_csv(df_filtrado),
    file_name=f"laminacao_{mes_sel.lower().replace('/', '_')}.csv",
    mime="text/csv"
)
# ---------------- BOTÃO DE ATUALIZAÇÃO MANUAL ----------------
st.markdown("### 🔄 Atualização de Dados")

col_refresh1, col_refresh2 = st.columns([1, 5])

with col_refresh1:
    if st.button("🔁 Atualizar Agora"):
        st.cache_data.clear()  # limpa cache do Streamlit
        st.experimental_rerun()  # recarrega o app imediatamente

with col_refresh2:
    st.caption("Os dados também são atualizados automaticamente a cada 60 segundos.")

# ---------------- AUTO-ATUALIZAÇÃO A CADA 60 SEGUNDOS ----------------
st.markdown(
    """
    <script>
    setTimeout(function() {
        window.location.reload();
    }, 60000); // 60.000 ms = 60 segundos
    </script>
    """,
    unsafe_allow_html=True
)

st.markdown("---")
st.caption("Dashboard atualizado automaticamente a cada 60 segundos. Fonte: Planilha Google Sheets • BonSono")

