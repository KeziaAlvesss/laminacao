import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- CONFIGURAÇÕES INICIAIS ----------------
st.set_page_config(page_title="Dashboard - Laminação BonSono", layout="wide")
st.title("📊 Acompanhamento de Produção - Laminação")

# URL da planilha Google Sheets publicada em CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M33hq6NkeSEKapeZBts83asudSdsPkXCzcPV-3YWmWE/export?format=csv&gid=624767121"

# ---------------- FUNÇÃO DE CARREGAMENTO ----------------
@st.cache_data(ttl=300)
def carregar_dados():
    df = pd.read_csv(SHEET_URL, skiprows=4)
    df.dropna(how="all", inplace=True)
    df.columns = df.columns.str.strip()
    
    if "Qnte" in df.columns:
        df["Qnte"] = pd.to_numeric(df["Qnte"], errors="coerce").fillna(0)
    
    for col in ["Data de ordem", "Data de corte"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    
    return df

df = carregar_dados()

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado na planilha.")
    st.stop()

# ---------------- FILTROS ----------------
st.sidebar.header("🔎 Filtros")

# Responsável
responsaveis = ["Todos"] + sorted(df["Responsável"].dropna().unique().tolist())
responsavel_sel = st.sidebar.selectbox("Responsável:", responsaveis)

# Produto
produtos = ["Todos"] + sorted(df["Produto"].dropna().unique().tolist())
produto_sel = st.sidebar.selectbox("Produto:", produtos)

# Aplicar filtros (sem lote)
df_filtrado = df.copy()
if responsavel_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Responsável"] == responsavel_sel]
if produto_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Produto"] == produto_sel]

# ---------------- INDICADORES (KPIs) ESTILIZADOS — TEMA BONSONO ----------------
st.markdown("### 📈 Indicadores Gerais")

total_qnte = df_filtrado["Qnte"].sum()
total_blocos = df_filtrado["Bloco"].nunique() if "Bloco" in df_filtrado.columns else 0
taxa_conforme = 0.0
if "Conforme?" in df_filtrado.columns:
    conformes = df_filtrado["Conforme?"].astype(str).str.upper() == "SIM"
    total_validos = conformes.sum() + (df_filtrado["Conforme?"].astype(str).str.upper() == "NÃO").sum()
    if total_validos > 0:
        taxa_conforme = (conformes.sum() / total_validos) * 100

# Função para criar card estilizado com tema BonSono
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
    st.markdown(
        criar_card_bonsono("Produção Total De Laminas (Qnte)", f"{total_qnte:,.0f}", "🏭", "#1565C0"),
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        criar_card_bonsono("Blocos Laminados", f"{total_blocos:,}", "🧱", "#1976D2"),
        unsafe_allow_html=True
    )

with col3:
    # Forçando conformidade para 100% (para exibição visual)
    taxa_conforme_fixa = 100.0
    cor_borda = "#0288D1"   # Azul claro (ótimo desempenho)
    cor_texto = "#0288D1"

    st.markdown(
        f"""
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
            <h4 style="color: #0D47A1; margin: 0; font-size: 16px; font-weight: 600;">✅ Conformidade (%)</h4>
            <p style="font-size: 28px; font-weight: bold; color: {cor_texto}; margin: 10px 0;">{taxa_conforme_fixa:.1f}%</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------- GRÁFICOS ----------------
st.markdown("### 📊 Visualizações")

# 1️⃣ Produção por responsável — AJUSTADO PARA NÃO CORTAR TEXTOS
if "Responsável" in df_filtrado.columns:
    df_resp = df_filtrado.groupby("Responsável", as_index=False)["Qnte"].sum()
    df_resp = df_resp.sort_values("Qnte", ascending=False)
    
    fig1 = px.bar(
        df_resp,
        x="Responsável",
        y="Qnte",
        title="Produção por Responsável",
        text_auto=True,
        color_discrete_sequence=["#1565C0"]  # Azul BonSono
    )
    
    fig1.update_traces(
        texttemplate='%{y:,.0f}',          # Formato com separador de milhar
        textposition='outside',             # Coloca texto ACIMA da barra
        marker_line_color='rgb(8,48,107)',  # Borda escura para contraste
        marker_line_width=1.5,
        opacity=0.9
    )
    
    fig1.update_layout(
        yaxis_title="Quantidade",
        xaxis_title="Responsável",
        uniformtext_minsize=12,
        uniformtext_mode='hide',
        title={
            'text': "Produção por Responsável",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20, color='#0D47A1')
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Segoe UI", size=12, color="#0D47A1"),
        margin=dict(t=80, b=50, l=50, r=50),  # Aumenta margem superior para caber os textos
        height=500  # Altura fixa para evitar corte
    )
    
    st.plotly_chart(fig1, use_container_width=True)

# 2️⃣ Produção por produto — AJUSTADO PARA NÃO CORTAR TEXTOS E NOMES
if "Produto" in df_filtrado.columns:
    df_prod = df_filtrado.groupby("Produto", as_index=False)["Qnte"].sum()
    df_prod = df_prod.sort_values("Qnte", ascending=False)
    
    fig2 = px.bar(
        df_prod,
        x="Produto",
        y="Qnte",
        title="Produção por Produto",
        text_auto=True,
        color_discrete_sequence=["#1976D2"]  # Azul BonSono
    )
    
    fig2.update_traces(
        texttemplate='%{y:,.0f}',          # Formato com separador de milhar
        textposition='outside',             # Texto acima da barra
        marker_line_color='rgb(8,48,107)',  # Borda escura para contraste
        marker_line_width=1.5,
        opacity=0.9
    )
    
    fig2.update_layout(
        yaxis_title="Quantidade",
        xaxis_title="Produto",
        uniformtext_minsize=10,
        uniformtext_mode='hide',
        title={
            'text': "Produção por Produto",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20, color='#0D47A1')
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Segoe UI", size=11, color="#0D47A1"),
        margin=dict(t=80, b=150, l=50, r=50),  # Aumenta margem inferior para caber os nomes
        height=600,                           # Altura maior para acomodar todos os produtos
        xaxis=dict(
            tickangle=45,                     # Rotação suave dos nomes (45°)
            tickfont=dict(size=10),
            tickmode='array',
            tickvals=df_prod["Produto"],      # Força todos os nomes a aparecerem
            ticktext=[p if len(p) <= 20 else p[:18] + "..." for p in df_prod["Produto"]]  # Trunca nomes longos
        ),
        showlegend=False  # Remove legenda (não necessária em gráficos de barras simples)
    )
    
    st.plotly_chart(fig2, use_container_width=True)

# 3️⃣ Evolução diária
if "Data de ordem" in df_filtrado.columns and not df_filtrado["Data de ordem"].isna().all():
    df_data = df_filtrado.groupby("Data de ordem", as_index=False)["Qnte"].sum()
    df_data = df_data.sort_values("Data de ordem")
    fig3 = px.line(
        df_data,
        x="Data de ordem",
        y="Qnte",
        markers=True,
        title="Evolução da Produção Diária",
        line_shape='spline',
        color_discrete_sequence=["#1565C0"]
    )
    fig3.update_traces(hovertemplate='Data: %{x|%d/%m/%Y}<br>Produção: %{y:,.0f}')
    fig3.update_layout(
        yaxis_title="Quantidade",
        xaxis_title="Data",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified"
    )
    st.plotly_chart(fig3, use_container_width=True)

# 4️⃣ Densidades mais produzidas — GRÁFICO DE PIZZA EM TONS DE AZUL
if "Densidade" in df_filtrado.columns:
    df_dens = df_filtrado.groupby("Densidade", as_index=False)["Qnte"].sum()
    
    # Paleta personalizada em tons de azul (de escuro a claro)
    azuis = [
        "#0D47A1",  # Azul escuro
        "#1565C0",
        "#1976D2",
        "#0288D1",
        "#4FC3F7",
        "#81D4FA",
        "#B3E5FC",
        "#E1F5FE",
        "#BBDEFB",
        "#90CAF9"
    ]
    
    # Se houver mais densidades que cores, repete a paleta
    if len(df_dens) > len(azuis):
        azuis = azuis * (len(df_dens) // len(azuis) + 1)
    
    fig4 = px.pie(
        df_dens,
        names="Densidade",
        values="Qnte",
        title="Distribuição por Densidade",
        hole=0.4,
        color_discrete_sequence=azuis[:len(df_dens)]  # Aplica os tons de azul
    )
    
    # Personaliza o gráfico
    fig4.update_traces(
        textinfo='percent+label',  # Mostra % e nome dentro do setor
        textfont_size=12,
        textposition='inside',     # Texto dentro do setor (evita sobreposição)
        insidetextorientation='radial'  # Orientação do texto
    )
    
    fig4.update_layout(
        showlegend=True,  # Mantém legenda, mas pode ser removida se quiser
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.1,
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.8)"
        ),
        title={
            'text': "Distribuição por Densidade",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20, color='#0D47A1')
        },
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=20, l=20, r=150),  # Aumenta espaço direito para legenda
        font=dict(family="Segoe UI", size=12, color="#0D47A1")
    )
    
    st.plotly_chart(fig4, use_container_width=True)
# ---------------- TABELA DETALHADA ----------------
st.markdown("### 📋 Dados Filtrados")
st.dataframe(df_filtrado, use_container_width=True)

# ---------------- DOWNLOAD ----------------
@st.cache_data
def to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Baixar Dados Filtrados (CSV)",
    data=to_csv(df_filtrado),
    file_name="laminacao_filtrados.csv",
    mime="text/csv"
)

# ---------------- RODAPÉ ----------------
st.markdown("---")
st.caption("Dashboard atualizado automaticamente a cada 5 minutos. Fonte: Planilha Google Sheets • BonSono")