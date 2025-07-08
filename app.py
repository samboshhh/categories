import pandas as pd
import plotly.express as px
import streamlit as st

# --- Page setup ---
st.set_page_config(page_title="Spending Categories Explorer", layout="wide")
st.title("🔍 Enrichment Category Explorer")

# --- Upload CSV ---
uploaded_file = st.file_uploader("Upload your open banking CSV", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # --- Normalise column names ---
    df.columns = df.columns.str.strip().str.lower()

    # --- Filter outgoings only ---
    df = df[df['amount'] < 0].copy()
    df['amount_abs'] = df['amount'].abs()

    # --- Remove noisy categories ---
    excluded = ['intra account transfer', 'inter account transfer', 'not enough information', 'peer to peer transfer']
    df = df[~df['enrichment_categories'].str.lower().isin(excluded)]

    # --- Top 20 categories summary ---
    cat_summary = (
        df.groupby('enrichment_categories')
        .agg(
            txn_count=('id', 'count'),
            total_spend=('amount_abs', 'sum'),
            avg_txn=('amount_abs', 'mean')
        )
        .sort_values(by='total_spend', ascending=False)
        .head(20)
        .reset_index()
    )

    # --- Bubble chart ---
    st.subheader("🫧 Top Spending Categories (Bubble View)")
    fig_main = px.scatter(
        cat_summary,
        x='txn_count',
        y='total_spend',
        size='total_spend',
        color='enrichment_categories',
        hover_data=['avg_txn'],
        labels={
            'txn_count': 'Number of Transactions',
            'total_spend': 'Total Spend (£)',
            'enrichment_categories': 'Category',
            'avg_txn': 'Avg Txn (£)'
        },
        title='💸 Top Spending Categories (Outgoings Only)'
    )
    fig_main.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
    fig_main.update_layout(height=600)
    st.plotly_chart(fig_main, use_container_width=True)

    # --- Dropdown to drill down ---
    st.subheader("📂 Explore Top Merchants by Category")
    selected = st.selectbox("Select a category to drill into:", cat_summary['enrichment_categories'])

    filtered = df[df['enrichment_categories'] == selected]
    top_merchants = (
        filtered.groupby('enrichment_merchant_name')
        .agg(total_spend=('amount_abs', 'sum'), txn_count=('id', 'count'))
        .sort_values(by='total_spend', ascending=False)
        .head(10)
        .reset_index()
    )

    top_merchants['label'] = top_merchants.apply(
        lambda row: f"£{row['total_spend']:,.0f} ({row['txn_count']} txns)", axis=1
    )

    fig = px.bar(
        top_merchants,
        x='total_spend',
        y='enrichment_merchant_name',
        orientation='h',
        text='label',
        labels={'total_spend': 'Total Spend (£)', 'enrichment_merchant_name': 'Merchant'},
        title=f"🛒 Top Merchants in: {selected}"
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis=dict(categoryorder='total ascending'), height=500)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 Upload a CSV file to begin")