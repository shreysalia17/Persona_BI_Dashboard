import pandas as pd
import streamlit as st

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.components.header import page_header
from src.components.metric_card import metric_card


st.set_page_config(
    page_title="Smart Search",
    page_icon="🔍",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/styles.css")

page_header(
    "Smart Search",
    "Search across customers, products, stores, categories, and sales records."
)

st.markdown("---")

try:
    sales_df = load_sheet("Sales Table")
    store_df = load_sheet("Store Table")
    product_df = load_sheet("Product Table")
    customer_df = load_sheet("Customer Table")

    sales_df = sales_df.merge(
        store_df[["Store_ID", "Store_Name"]],
        on="Store_ID",
        how="left"
    )

    sales_df = sales_df.merge(
        product_df[["Product_ID", "Product_Name", "Category"]],
        on="Product_ID",
        how="left"
    )

    sales_df = sales_df.merge(
        customer_df,
        on="Customer_ID",
        how="left"
    )

    sales_df["Sale_Date"] = pd.to_datetime(sales_df["Sale_Date"])

    st.subheader("Search Workspace")

    search_query = st.text_input(
        "Search by customer ID, product, category, store, or sale ID",
        placeholder="Example: Minimal Necklace, Persona Fifth Avenue, CUST00888..."
    )

    searchable_df = sales_df.copy()

    searchable_columns = [
        "Sale_ID",
        "Customer_ID",
        "Store_Name",
        "Product_Name",
        "Category",
        "Product_ID",
        "Store_ID"
    ]

    if search_query:
        query = search_query.lower().strip()

        mask = False

        for col in searchable_columns:
            if col in searchable_df.columns:
                mask = mask | searchable_df[col].astype(str).str.lower().str.contains(
                    query,
                    na=False
                )

        result_df = searchable_df[mask].copy()
    else:
        result_df = searchable_df.copy()

    total_matches = len(result_df)
    revenue_found = result_df["Revenue"].sum() if total_matches else 0
    customers_found = result_df["Customer_ID"].nunique() if total_matches else 0
    products_found = result_df["Product_ID"].nunique() if total_matches else 0

    st.markdown("---")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        metric_card(
            "Matches Found",
            f"{total_matches:,}",
            "assets/icons/total_order.png",
            "",
            "#666666",
        )

    with kpi_col2:
        metric_card(
            "Revenue Found",
            format_currency_short(revenue_found),
            "assets/icons/total_revenue.png",
            "",
            "#666666",
        )

    with kpi_col3:
        metric_card(
            "Customers Found",
            f"{customers_found:,}",
            "assets/icons/customer.png",
            "",
            "#666666",
        )

    with kpi_col4:
        metric_card(
            "Products Found",
            f"{products_found:,}",
            "assets/icons/product_sold.png",
            "",
            "#666666",
        )

    st.markdown("---")

    if search_query and result_df.empty:
        st.warning("No matching records found. Try searching another customer, product, store, or category.")

    else:
        st.subheader("Search Insights")

        insight_col1, insight_col2, insight_col3 = st.columns(3)

        top_store = (
            result_df.groupby("Store_Name")["Revenue"]
            .sum()
            .sort_values(ascending=False)
            if not result_df.empty else pd.Series(dtype=float)
        )

        top_product = (
            result_df.groupby("Product_Name")["Revenue"]
            .sum()
            .sort_values(ascending=False)
            if not result_df.empty else pd.Series(dtype=float)
        )

        top_customer = (
            result_df.groupby("Customer_ID")["Revenue"]
            .sum()
            .sort_values(ascending=False)
            if not result_df.empty else pd.Series(dtype=float)
        )

        with insight_col1:
            st.markdown(
                f"""
                <div class="summary-card">
                    <strong>Top Store</strong><br><br>
                    {top_store.index[0] if not top_store.empty else "N/A"}<br>
                    <strong>{format_currency_short(top_store.iloc[0]) if not top_store.empty else "$0"}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )

        with insight_col2:
            st.markdown(
                f"""
                <div class="summary-card">
                    <strong>Top Product</strong><br><br>
                    {top_product.index[0] if not top_product.empty else "N/A"}<br>
                    <strong>{format_currency_short(top_product.iloc[0]) if not top_product.empty else "$0"}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )

        with insight_col3:
            st.markdown(
                f"""
                <div class="summary-card">
                    <strong>Top Customer</strong><br><br>
                    {top_customer.index[0] if not top_customer.empty else "N/A"}<br>
                    <strong>{format_currency_short(top_customer.iloc[0]) if not top_customer.empty else "$0"}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.subheader("Search Results")

        display_df = result_df[
            [
                "Sale_Date",
                "Sale_ID",
                "Store_Name",
                "Customer_ID",
                "Category",
                "Product_Name",
                "Quantity",
                "Revenue"
            ]
        ].copy()

        display_df["Sale_Date"] = display_df["Sale_Date"].dt.strftime("%Y-%m-%d")
        display_df["Revenue"] = display_df["Revenue"].apply(lambda x: f"${x:,.0f}")

        st.dataframe(
            display_df.sort_values("Sale_Date", ascending=False),
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error("❌ Smart Search page failed to load.")
    st.exception(e)