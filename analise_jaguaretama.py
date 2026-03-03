import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title='Análise Municipal - Jaguaretama/CE',
    page_icon='📊',
    layout='wide'
)

st.title('📊 Análise Econômica - Jaguaretama/CE')
st.markdown('Dados do **IBGE** — Produto Interno Bruto dos Municípios')
st.markdown('---')


# ============================================================
# CARREGANDO E PROCESSANDO DADOS
# ============================================================
@st.cache_data
def carregar():
    df = pd.read_csv('pib_jaguaretama.csv', sep=';')

    # PIB per capita
    linha_pib = df.iloc[5]
    anos = [str(a) for a in range(2010, 2024)]
    df_pib = pd.DataFrame({
        'ano': anos,
        'pib_per_capita': pd.to_numeric(linha_pib[anos].values, errors='coerce')
    })
    df_pib = df_pib.dropna(subset=['pib_per_capita'])
    df_pib['ano'] = df_pib['ano'].astype(int)

    # PIB total
    linha_total = df.iloc[1]
    df_total = pd.DataFrame({
        'ano': anos,
        'pib_total': pd.to_numeric(linha_total[anos].values, errors='coerce')
    })
    df_total = df_total.dropna(subset=['pib_total'])
    df_total['ano'] = df_total['ano'].astype(int)
    df_total['crescimento_%'] = df_total['pib_total'].pct_change() * 100
    df_total['crescimento_%'] = df_total['crescimento_%'].round(2)

    cagr = ((df_total['pib_total'].iloc[-1] / df_total['pib_total'].iloc[0]) 
        ** (1 / (len(df_total)-1)) - 1) * 100

    # Setores
    setores = {
        'Agropecuária': 10,
        'Indústria': 11,
        'Serviços': 12,
        'Adm. Pública': 13
    }
    anos_setores = [str(a) for a in range(2010, 2022)]
    dados_setores = []
    for setor, idx in setores.items():
        linha = df.iloc[idx]
        for ano in anos_setores:
            val = pd.to_numeric(linha[ano], errors='coerce')
            if pd.notna(val):
                dados_setores.append({'setor': setor, 'ano': int(ano), 'valor': val})
    df_setores = pd.DataFrame(dados_setores)

    return df_pib, df_total, df_setores,cagr


df_pib, df_total, df_setores,cagr = carregar()


# ============================================================
# MÉTRICAS NO TOPO
# ============================================================
col1, col2, col3, col4 ,col5= st.columns(5)

with col1:
    st.metric('PIB Total 2023', f"R$ {df_total['pib_total'].iloc[-1]:,.0f} mil".replace(',', '.'))

with col2:
    st.metric('PIB per Capita 2023', f"R$ {df_pib['pib_per_capita'].iloc[-1]:,.2f}".replace(',', '.'))

with col3:
    crescimento = df_total['crescimento_%'].iloc[-1]
    st.metric('Crescimento 2023', f"{crescimento}%", delta=f"{crescimento}%")

with col4:
    variacao = df_pib['pib_per_capita'].iloc[-1] - df_pib['pib_per_capita'].iloc[0]
    st.metric('Variação PIB per Capita (2010-2023)', f"R$ {variacao:,.0f}".replace(',', '.'))

with col5:
    st.metric('CAGR 2010-2023', f"{cagr:.2f}%")   

st.markdown('---')


# ============================================================
# GRÁFICO 1 - PIB PER CAPITA
# ============================================================
st.subheader('📈 PIB per Capita (2010-2023)')

fig1, ax1 = plt.subplots(figsize=(12, 5))
ax1.plot(df_pib['ano'], df_pib['pib_per_capita'], marker='o', color='#2ecc71', linewidth=2)
ax1.fill_between(df_pib['ano'], df_pib['pib_per_capita'], alpha=0.2, color='#2ecc71')
for _, row in df_pib.iterrows():
    ax1.text(row['ano'], row['pib_per_capita'] + 200,
             f"R$ {row['pib_per_capita']:,.0f}".replace(',', '.'),
             ha='center', fontsize=8)
ax1.set_xlabel('Ano')
ax1.set_ylabel('R$')
ax1.set_xticks(df_pib['ano'])
ax1.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig1)

st.markdown('---')


# ============================================================
# GRÁFICO 2 - PIB TOTAL E CRESCIMENTO
# ============================================================
st.subheader('🏦 PIB Total e Crescimento Anual')

fig2, (ax2, ax3) = plt.subplots(2, 1, figsize=(12, 10))

ax2.bar(df_total['ano'], df_total['pib_total'], color='#3498db')
ax2.set_ylabel('PIB Total (R$ mil)')
ax2.set_xticks(df_total['ano'])
ax2.tick_params(axis='x', rotation=45)

cores = ['#e74c3c' if x < 0 else '#2ecc71' for x in df_total['crescimento_%'].fillna(0)]
ax3.bar(df_total['ano'], df_total['crescimento_%'], color=cores)
ax3.axhline(y=0, color='black', linewidth=0.8)
ax3.set_ylabel('Crescimento (%)')
ax3.set_xticks(df_total['ano'])
ax3.tick_params(axis='x', rotation=45)
ax3.annotate('Seca 2012', xy=(2012, -6.79), xytext=(2013, -9),
             arrowprops=dict(arrowstyle='->', color='red'), color='red', fontsize=9)
ax3.annotate('Aux. Emergencial', xy=(2020, 20.54), xytext=(2018, 22),
             arrowprops=dict(arrowstyle='->', color='green'), color='green', fontsize=9)

plt.tight_layout()
st.pyplot(fig2)

st.markdown('---')


# ============================================================
# GRÁFICO 3 - SETORES
# ============================================================
st.subheader('🏭 Composição do PIB por Setor')

cores_setores = {
    'Agropecuária': '#2ecc71',
    'Indústria': '#3498db',
    'Serviços': '#e67e22',
    'Adm. Pública': '#9b59b6'
}

col_a, col_b = st.columns(2)

with col_a:
    fig3, ax4 = plt.subplots(figsize=(8, 5))
    for setor, grupo in df_setores.groupby('setor'):
        ax4.plot(grupo['ano'], grupo['valor'], marker='o',
                 label=setor, color=cores_setores[setor], linewidth=2)
    ax4.set_title('Evolução por Setor')
    ax4.set_xlabel('Ano')
    ax4.set_ylabel('Valor (R$ mil)')
    ax4.legend()
    ax4.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    st.pyplot(fig3)

with col_b:
    ultimo_ano = df_setores[df_setores['ano'] == 2021]
    fig4, ax5 = plt.subplots(figsize=(8, 5))
    ax5.pie(ultimo_ano['valor'], labels=ultimo_ano['setor'], autopct='%1.1f%%',
            colors=[cores_setores[s] for s in ultimo_ano['setor']], startangle=90)
    ax5.set_title('Composição do PIB em 2021')
    plt.tight_layout()
    st.pyplot(fig4)

st.markdown('---')


# ============================================================
# TABELA DE DADOS
# ============================================================
st.subheader('📋 Dados Completos')

aba1, aba2, aba3 = st.tabs(['PIB per Capita', 'PIB Total', 'Setores'])

with aba1:
    st.dataframe(df_pib, use_container_width=True)

with aba2:
    st.dataframe(df_total, use_container_width=True)

with aba3:
    st.dataframe(df_setores, use_container_width=True)


# ============================================================
# EXPORTAR EXCEL
# ============================================================
st.markdown('---')
if st.button('📥 Exportar Relatório Excel'):
    with pd.ExcelWriter('relatorio_jaguaretama.xlsx', engine='openpyxl') as writer:
        df_pib.to_excel(writer, sheet_name='PIB_per_capita', index=False)
        df_setores.to_excel(writer, sheet_name='Setores', index=False)
        df_total.to_excel(writer, sheet_name='PIB_Total', index=False)
    st.success('Relatório exportado com sucesso: relatorio_jaguaretama.xlsx')
