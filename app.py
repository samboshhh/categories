import pandas as pd
import plotly.express as px
import streamlit as st

# --- Page setup ---
st.set_page_config(page_title="Committed Spend Explorer", layout="wide")
st.title("💸 Committed Expenditure Explorer")

# --- Upload CSV ---
uploaded_file = st.file_uploader("Upload your open banking CSV", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # --- Normalise column names ---
    df.columns = df.columns.str.strip().str.lower()

    # --- Filter outgoings only ---
    df = df[df['amount'] < 0].copy()
    df['amount_abs'] = df['amount'].abs()

    # --- Optional merchant mapping (example logic) ---
    merchant_mapping = {
        'ee': 'Media & Connectivity',
        'vodafone': 'Media & Connectivity',
        'virgin media': 'Media & Connectivity',
        'thames water': 'Utilities',
        'edf': 'Utilities',
        'manchester city council': 'Council Tax',
        'hsbc mortgage': 'Housing',
        'childcare co-op': 'Childcare',
    }

    df['enrichment_merchant_name'] = df['enrichment_merchant_name'].str.lower()
    df['internal_committed_category'] = df['enrichment_merchant_name'].map(merchant_mapping)

    # --- Filter to mapped committed spend ---
    df_committed = df[df['internal_committed_category'].notnull()].copy()

    # --- Summary Table ---
    summary = (
        df_committed.groupby('internal_committed_category')
        .agg(
            total_spend=('amount_abs', 'sum'),
            txn_count=('id', 'count'),
            unique_merchants=('enrichment_merchant_name', 'nunique')
        )
        .sort_values(by='total_spend', ascending=False)
        .reset_index()
    )

    st.subheader("📊 Summary by Committed Category")
    st.dataframe(summary.style.format({"total_spend": "£{:,.2f}"}))

    # --- Category Selector ---
    selected_category = st.selectbox("Select a category to drill down:", summary['internal_committed_category'])

    filtered = df_committed[df_committed['internal_committed_category'] == selected_category]
    top_merchants = (
        filtered.groupby('enrichment_merchant_name')
        .agg(
            total_spend=('amount_abs', 'sum'),
            txn_count=('id', 'count')
        )
        .sort_values(by='total_spend', ascending=False)
        .head(10)
        .reset_index()
    )

    top_merchants['label'] = top_merchants.apply(
        lambda row: f"£{row['total_spend']:,.0f} ({row['txn_count']} txns)", axis=1
    )

    st.subheader(f"🧾 Top Merchants: {selected_category}")
    fig = px.bar(
        top_merchants,
        x='total_spend',
        y='enrichment_merchant_name',
        orientation='h',
        text='label',
        labels={'total_spend': 'Total Spend (£)', 'enrichment_merchant_name': 'Merchant'}
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis=dict(categoryorder='total ascending'), height=500)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 Upload a CSV file to get started")