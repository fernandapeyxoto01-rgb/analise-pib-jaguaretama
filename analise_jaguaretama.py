import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
from openai import OpenAI

# ============================================================
# CHAVE DA API
# ============================================================
# ⬇️ COLOQUE SUA CHAVE AQUI
OPENAI_API_KEY = "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"

def get_secret(key, default=None):
    if key == "OPENAI_API_KEY":
        return OPENAI_API_KEY
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Análise Econômica - Jaguaretama/CE",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a3c5e 0%, #2563a8 100%);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stTextArea textarea {
        background: white !important;
        color: #1a3c5e !important;
        border: 1px solid rgba(255,255,255,0.4) !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] .stTextArea textarea::placeholder {
        color: #aaa !important;
    }

    h1, h2, h3 { color: #1a3c5e !important; }

    .stTabs [data-baseweb="tab"] { font-weight: 600; color: #2563a8; }

    .stButton > button {
        background: linear-gradient(90deg, #1a3c5e, #2563a8);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    /* Cards de métrica */
    .metric-card {
        background: white;
        border-radius: 12px;
        border-left: 5px solid #2563a8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.09);
        padding: 18px 20px 14px 20px;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-label {
        font-size: 0.72rem;
        color: #888;
        font-weight: 500;
        line-height: 1.35;
        height: 2.5em;
        overflow: hidden;
    }
    .metric-value {
        font-size: 1.25rem;
        font-weight: 800;
        color: #1a3c5e;
    }
    .delta-pos { font-size: 0.78rem; color: #27ae60; font-weight: 600; }
    .delta-neg { font-size: 0.78rem; color: #e74c3c; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# CARREGAR DADOS
# ============================================================
@st.cache_data
def carregar_dados():
    df = pd.read_csv("pib_jaguaretama.csv", sep=";", encoding="latin1", on_bad_lines="skip")
    anos = [str(a) for a in range(2010, 2024)]

    # PIB Total
    linha_total = df.iloc[1]
    df_total = pd.DataFrame({
        "Ano": anos,
        "PIB_Total": pd.to_numeric(linha_total[anos], errors="coerce")
    })
    df_total["Ano"] = df_total["Ano"].astype(int)
    df_total["Crescimento_%"] = df_total["PIB_Total"].pct_change() * 100
    df_total["Crescimento_%"] = df_total["Crescimento_%"].round(2)

    # PIB Per Capita
    linha_pc = df.iloc[5]
    df_pc = pd.DataFrame({
        "Ano": anos,
        "PIB_Per_Capita": pd.to_numeric(linha_pc[anos], errors="coerce")
    })
    df_pc["Ano"] = df_pc["Ano"].astype(int)

    # Setores
    setores = {"Agropecuária": 10, "Indústria": 11, "Serviços": 12, "Administração Pública": 13}
    anos_setores = [str(a) for a in range(2010, 2022)]
    dados_setores = []
    for setor, idx in setores.items():
        linha = df.iloc[idx]
        for ano in anos_setores:
            valor = pd.to_numeric(linha[ano], errors="coerce")
            if pd.notna(valor):
                dados_setores.append({"Setor": setor, "Ano": int(ano), "Valor": valor})
    df_setores = pd.DataFrame(dados_setores)

    cagr = ((df_total["PIB_Total"].iloc[-1] / df_total["PIB_Total"].iloc[0])
            ** (1 / (len(df_total) - 1)) - 1) * 100

    return df_total, df_pc, df_setores, cagr


df_total, df_pc, df_setores, cagr = carregar_dados()

cores_setores = {
    "Agropecuária": "#2ecc71",
    "Indústria": "#3498db",
    "Serviços": "#e67e22",
    "Administração Pública": "#9b59b6"
}


# ============================================================
# SIDEBAR — FILTROS + CHAT
# ============================================================
with st.sidebar:
    st.title("🗂️ Filtros")

    ano_min = int(df_total["Ano"].min())
    ano_max = int(df_total["Ano"].max())

    ano_inicio, ano_fim = st.slider(
        "Intervalo de anos",
        min_value=ano_min,
        max_value=ano_max,
        value=(ano_min, ano_max),
        key="ano_slider"
    )

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:10px;margin:8px 0;">
        <div style="font-size:0.78rem;opacity:0.8;">Período selecionado</div>
        <div style="font-size:1.3rem;font-weight:700;">{ano_inicio} → {ano_fim}</div>
        <div style="font-size:0.78rem;opacity:0.8;">{ano_fim - ano_inicio + 1} anos</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Setores**")

    setores_lista = df_setores["Setor"].unique()
    setores_sel = []
    for s in setores_lista:
        if st.checkbox(s, value=True, key=f"setor_{s}"):
            setores_sel.append(s)

    if st.button("🔄 Limpar filtros", use_container_width=True):
        st.session_state["ano_slider"] = (ano_min, ano_max)
        for s in df_setores["Setor"].unique():
            st.session_state[f"setor_{s}"] = True
        st.rerun()

    st.markdown("---")

    # ── CHAT ──────────────────────────────────────────────────
    st.markdown("### 🤖 Assistente IA")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Olá! Pergunte sobre o PIB, setores ou economia de Jaguaretama."}
        ]

    if st.button("Limpar conversa", key="clear_chat", use_container_width=True):
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Conversa reiniciada. Como posso ajudar?"}
        ]
        st.rerun()

    # Histórico
    with st.container(height=260):
        for msg in st.session_state.chat_messages[-20:]:
            role_label = "👤 Você" if msg["role"] == "user" else "🤖 Assistente"
            cor = "rgba(255,255,255,0.15)" if msg["role"] == "assistant" else "rgba(255,255,255,0.08)"
            st.markdown(
                f'<div style="background:{cor};border-radius:8px;padding:8px 10px;'
                f'margin-bottom:6px;font-size:0.82rem;">'
                f'<b>{role_label}:</b> {msg["content"]}</div>',
                unsafe_allow_html=True
            )

    # Input
    user_question = st.text_area(
        "Pergunta",
        placeholder="Ex.: Qual o ano com maior PIB?",
        height=75,
        key="chat_question_input",
        label_visibility="collapsed"
    )
    send_clicked = st.button("📨 Enviar mensagem", key="send_chat", use_container_width=True)

    st.markdown("---")
    st.caption("Fonte: IBGE — PIB dos Municípios")

    _api_key = get_secret("OPENAI_API_KEY")
    if _api_key:
        st.success("✅ API Key carregada")
    else:
        st.error("❌ OPENAI_API_KEY não encontrada")
        st.info("Crie `.streamlit/secrets.toml` com:\n`ANTHROPIC_API_KEY = 'sk-ant-...'`")


# ============================================================
# DADOS FILTRADOS
# ============================================================
df_total_f = df_total[(df_total["Ano"] >= ano_inicio) & (df_total["Ano"] <= ano_fim)]
df_pc_f    = df_pc[(df_pc["Ano"] >= ano_inicio) & (df_pc["Ano"] <= ano_fim)]

ano_max_setores = min(ano_fim, 2021)
ano_min_setores = max(ano_inicio, 2010)
df_setores_f = df_setores[
    (df_setores["Ano"] >= ano_min_setores) &
    (df_setores["Ano"] <= ano_max_setores) &
    (df_setores["Setor"].isin(setores_sel))
]

pib_ultimo    = df_total_f["PIB_Total"].iloc[-1]
pib_pc_ultimo = df_pc_f["PIB_Per_Capita"].iloc[-1]
pib_pc_primeiro = df_pc_f["PIB_Per_Capita"].iloc[0]
crescimento   = df_total_f["Crescimento_%"].iloc[-1]
variacao_pc   = pib_pc_ultimo - pib_pc_primeiro
variacao_pct  = (variacao_pc / pib_pc_primeiro * 100)

cagr_filtrado = (
    ((df_total_f["PIB_Total"].iloc[-1] / df_total_f["PIB_Total"].iloc[0])
     ** (1 / (len(df_total_f) - 1)) - 1) * 100
    if len(df_total_f) > 1 else 0.0
)


# ============================================================
# PROCESSAMENTO DO CHAT
# ============================================================
def gerar_contexto():
    return f"""
Você é um economista especialista em desenvolvimento regional do Brasil.
Analise os dados do PIB de Jaguaretama/CE (IBGE). Período: {ano_inicio}–{ano_fim}.

=== PIB TOTAL (R$ mil) ===
{df_total_f.to_string(index=False)}

=== PIB PER CAPITA (R$) ===
{df_pc_f.to_string(index=False)}

=== PIB POR SETOR (R$ mil) ===
{df_setores_f.pivot(index="Ano", columns="Setor", values="Valor").to_string() if not df_setores_f.empty else "Sem dados."}

=== INDICADORES ===
- CAGR {ano_inicio}–{ano_fim}: {cagr_filtrado:.2f}%
- PIB Total {ano_fim}: R$ {pib_ultimo:,.0f} mil
- PIB per Capita {ano_fim}: R$ {pib_pc_ultimo:,.2f}
- Variação per Capita: R$ {variacao_pc:,.0f} ({variacao_pct:.1f}%)

Responda em português, de forma clara e objetiva.
"""

if send_clicked and user_question.strip():
    st.session_state.chat_messages.append({"role": "user", "content": user_question.strip()})
    try:
        _chave = get_secret("OPENAI_API_KEY")
        if not _chave:
            raise ValueError("Chave OPENAI_API_KEY não encontrada em st.secrets nem em variável de ambiente.")
        _client = OpenAI(api_key=_chave)
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": gerar_contexto()},
                *[{"role": m["role"], "content": m["content"]}
                  for m in st.session_state.chat_messages]
            ],
            temperature=0.3
        )
        resposta = response.choices[0].message.content
    except Exception as e:
        resposta = f"⚠️ Erro: {str(e)}"
    st.session_state.chat_messages.append({"role": "assistant", "content": resposta})
    st.rerun()


# ============================================================
# CABEÇALHO
# ============================================================
st.title("📊 Análise Econômica — Jaguaretama/CE")
st.markdown(f"Dados do **IBGE** — PIB dos Municípios &nbsp;|&nbsp; Período: **{ano_inicio} – {ano_fim}**")
st.divider()


# ============================================================
# MÉTRICAS
# ============================================================
def card(col, label, value, delta=None, positivo=True):
    delta_html = ""
    if delta is not None:
        cls  = "delta-pos" if positivo else "delta-neg"
        seta = "▲" if positivo else "▼"
        delta_html = f'<p class="{cls}">{seta} {delta}</p>'
    else:
        delta_html = '<p style="margin:0;height:1em;"></p>'
    col.markdown(f"""
<div class="metric-card">
    <p class="metric-label">{label}</p>
    <p class="metric-value">{value}</p>
    {delta_html}
</div>""", unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
card(c1, f"PIB Total {ano_fim}",        f"R$ {pib_ultimo:,.0f} mil".replace(",", "."))
card(c2, f"PIB per Capita {ano_fim}",   f"R$ {pib_pc_ultimo:,.2f}".replace(",", "."))
card(c3, f"Crescimento {ano_fim}",      f"{crescimento:.2f}%",
     delta=f"{crescimento:.2f}%",       positivo=crescimento >= 0)
card(c4, f"Variação per Capita ({ano_inicio}–{ano_fim})",
     f"R$ {variacao_pc:,.0f}".replace(",", "."),
     delta=f"{variacao_pct:.1f}%",      positivo=variacao_pc >= 0)
card(c5, f"CAGR {ano_inicio}–{ano_fim}", f"{cagr_filtrado:.2f}%")

st.divider()


# ============================================================
# HELPER GRÁFICO
# ============================================================
def estilo_ax(ax, titulo=""):
    ax.set_facecolor("#f8fafc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#dde3ea")
    ax.spines["bottom"].set_color("#dde3ea")
    ax.tick_params(colors="#555", labelsize=9)
    ax.yaxis.label.set_color("#555")
    ax.xaxis.label.set_color("#555")
    if titulo:
        ax.set_title(titulo, fontsize=12, fontweight="bold", color="#1a3c5e", pad=12)
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.8, linestyle="--")


# ============================================================
# GRÁFICO 1 — PIB PER CAPITA
# ============================================================
st.subheader(f"📈 PIB per Capita ({ano_inicio}–{ano_fim})")

fig1, ax1 = plt.subplots(figsize=(12, 4.5))
fig1.patch.set_facecolor("#f0f4f8")
estilo_ax(ax1)
ax1.plot(df_pc_f["Ano"], df_pc_f["PIB_Per_Capita"],
         marker="o", color="#2563a8", linewidth=2.5, markersize=7, zorder=3)
ax1.fill_between(df_pc_f["Ano"], df_pc_f["PIB_Per_Capita"], alpha=0.12, color="#2563a8")
margem = df_pc_f["PIB_Per_Capita"].max() * 0.025
for _, row in df_pc_f.iterrows():
    ax1.text(row["Ano"], row["PIB_Per_Capita"] + margem,
             f"R$ {row['PIB_Per_Capita']:,.0f}".replace(",", "."),
             ha="center", fontsize=7.5, color="#1a3c5e", fontweight="600")
ax1.set_xlabel("Ano")
ax1.set_ylabel("R$")
ax1.set_xticks(df_pc_f["Ano"])
ax1.tick_params(axis="x", rotation=45)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x:,.0f}".replace(",", ".")))
plt.tight_layout()
st.pyplot(fig1)

st.divider()


# ============================================================
# GRÁFICO 2 — PIB TOTAL + CRESCIMENTO
# ============================================================
st.subheader(f"🏦 PIB Total e Crescimento Anual ({ano_inicio}–{ano_fim})")

fig2, (ax2, ax3) = plt.subplots(2, 1, figsize=(12, 9), gridspec_kw={"hspace": 0.45})
fig2.patch.set_facecolor("#f0f4f8")

estilo_ax(ax2, "PIB Total (R$ mil)")
bars = ax2.bar(df_total_f["Ano"], df_total_f["PIB_Total"],
               color="#2563a8", alpha=0.85, width=0.6, zorder=2)
ax2.set_xticks(df_total_f["Ano"])
ax2.tick_params(axis="x", rotation=45)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
for bar in bars:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width() / 2,
             h + df_total_f["PIB_Total"].max() * 0.01,
             f"{h/1000:.0f}k", ha="center", va="bottom",
             fontsize=7.5, color="#1a3c5e", fontweight="600")

estilo_ax(ax3, "Crescimento Anual (%)")
cores_barras = ["#e74c3c" if x < 0 else "#27ae60"
                for x in df_total_f["Crescimento_%"].fillna(0)]
bars3 = ax3.bar(df_total_f["Ano"], df_total_f["Crescimento_%"],
                color=cores_barras, alpha=0.85, width=0.6, zorder=2)
ax3.axhline(y=0, color="#555", linewidth=1)

# Rótulos nas barras
for bar, val in zip(bars3, df_total_f["Crescimento_%"].fillna(0)):
    if val == 0:
        continue
    y_pos = val + 0.5 if val >= 0 else val - 1.8
    ax3.text(
        bar.get_x() + bar.get_width() / 2,
        y_pos,
        f"{val:.1f}%",
        ha="center", va="bottom" if val >= 0 else "top",
        fontsize=7.5, fontweight="600",
        color="#1a6b35" if val >= 0 else "#a93226"
    )
ax3.set_xticks(df_total_f["Ano"])
ax3.tick_params(axis="x", rotation=45)
if ano_inicio <= 2012 <= ano_fim:
    ax3.annotate("🌵 Seca 2012", xy=(2012, -6.79), xytext=(2012.5, -10),
                 arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.5),
                 color="#c0392b", fontsize=8.5, fontweight="600")
if ano_inicio <= 2020 <= ano_fim:
    ax3.annotate("💰 Aux. Emergencial", xy=(2020, 20.54), xytext=(2018.5, 23),
                 arrowprops=dict(arrowstyle="->", color="#27ae60", lw=1.5),
                 color="#27ae60", fontsize=8.5, fontweight="600")
plt.tight_layout()
st.pyplot(fig2)

st.divider()


# ============================================================
# GRÁFICO 3 — SETORES
# ============================================================
st.subheader(f"🏭 Composição do PIB por Setor ({ano_min_setores}–{ano_max_setores})")

if df_setores_f.empty:
    st.warning("⚠️ Nenhum setor selecionado. Ajuste os filtros na barra lateral.")
else:
    col_a, col_b = st.columns(2)

    with col_a:
        fig3, ax4 = plt.subplots(figsize=(9, 4.5))
        fig3.patch.set_facecolor("#f0f4f8")
        estilo_ax(ax4, "Evolução por Setor (R$ mil)")
        for setor, grupo in df_setores_f.groupby("Setor"):
            ax4.plot(grupo["Ano"], grupo["Valor"], marker="o",
                     label=setor, color=cores_setores.get(setor, "#999"),
                     linewidth=2.2, markersize=6)
        ax4.set_xlabel("Ano")
        ax4.set_ylabel("Valor (R$ mil)")
        ax4.legend(loc="upper left", fontsize=8.5, framealpha=0.9)
        ax4.tick_params(axis="x", rotation=45)
        plt.tight_layout()
        st.pyplot(fig3)

    with col_b:
        dados_pizza = df_setores_f[df_setores_f["Ano"] == ano_max_setores]
        if not dados_pizza.empty:
            fig4, ax5 = plt.subplots(figsize=(9, 4.5))
            fig4.patch.set_facecolor("#f0f4f8")
            wedges, texts, autotexts = ax5.pie(
                dados_pizza["Valor"],
                labels=dados_pizza["Setor"],
                autopct="%1.1f%%",
                colors=[cores_setores.get(s, "#999") for s in dados_pizza["Setor"]],
                startangle=90,
                pctdistance=0.82,
                wedgeprops=dict(width=0.6, edgecolor="white", linewidth=2)
            )
            for t in autotexts:
                t.set_fontsize(9)
                t.set_fontweight("bold")
                t.set_color("white")
            ax5.set_title(f"Composição em {ano_max_setores}",
                          fontsize=12, fontweight="bold", color="#1a3c5e", pad=12)
            plt.tight_layout()
            st.pyplot(fig4)

st.divider()


# ============================================================
# TABELAS
# ============================================================
st.subheader("📋 Dados do Período Selecionado")

st.markdown("""
<style>
    /* Cabeçalho */
    [data-testid="stDataFrame"] thead tr th {
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: #1a3c5e !important;
        background-color: #dbeafe !important;
        padding: 14px 20px !important;
        border-bottom: 2px solid #2563a8 !important;
    }
    /* Células */
    [data-testid="stDataFrame"] tbody tr td {
        font-size: 0.97rem !important;
        padding: 12px 20px !important;
        color: #1a1a2e !important;
        border-bottom: 1px solid #e8edf5 !important;
    }
    /* Linhas alternadas */
    [data-testid="stDataFrame"] tbody tr:nth-child(even) td {
        background-color: #f0f6ff !important;
    }
    /* Hover */
    [data-testid="stDataFrame"] tbody tr:hover td {
        background-color: #bfdbfe !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

aba1, aba2, aba3 = st.tabs(["📊 PIB Total", "👤 PIB Per Capita", "🏭 Setores"])

with aba1:
    df_exib1 = df_total_f.copy()
    df_exib1.columns = ["Ano", "PIB Total (R$ mil)", "Crescimento (%)"]
    df_exib1["PIB Total (R$ mil)"] = df_exib1["PIB Total (R$ mil)"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))
    df_exib1["Crescimento (%)"] = df_exib1["Crescimento (%)"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "—")
    df_exib1["Ano"] = df_exib1["Ano"].astype(str)
    st.dataframe(df_exib1, use_container_width=True, hide_index=True, height=350)

with aba2:
    df_exib2 = df_pc_f.copy()
    df_exib2.columns = ["Ano", "PIB Per Capita (R$)"]
    df_exib2["PIB Per Capita (R$)"] = df_exib2["PIB Per Capita (R$)"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "."))
    df_exib2["Ano"] = df_exib2["Ano"].astype(str)
    st.dataframe(df_exib2, use_container_width=True, hide_index=True, height=350)

with aba3:
    df_exib3 = df_setores_f.copy()
    df_exib3.columns = ["Setor", "Ano", "Valor (R$ mil)"]
    df_exib3["Valor (R$ mil)"] = df_exib3["Valor (R$ mil)"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))
    df_exib3["Ano"] = df_exib3["Ano"].astype(str)
    df_exib3 = df_exib3.sort_values(["Setor", "Ano"]).reset_index(drop=True)
    st.dataframe(df_exib3, use_container_width=True, hide_index=True, height=350)

st.divider()


# ============================================================
# EXPORTAR EXCEL
# ============================================================
st.subheader("📥 Exportar Dados")

if st.button("Exportar Excel (período filtrado)"):
    nome = f"relatorio_jaguaretama_{ano_inicio}_{ano_fim}.xlsx"
    with pd.ExcelWriter(nome, engine="openpyxl") as writer:
        df_total_f.to_excel(writer, sheet_name="PIB_Total",     index=False)
        df_pc_f.to_excel(writer,    sheet_name="PIB_Per_Capita", index=False)
        df_setores_f.to_excel(writer, sheet_name="Setores",     index=False)
    st.success(f"✅ Arquivo exportado: {nome}")success('Relatório exportado com sucesso: relatorio_jaguaretama.xlsx')
