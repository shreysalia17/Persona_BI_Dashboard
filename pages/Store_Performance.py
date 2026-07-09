import pandas as pd
import streamlit as st

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.charts import revenue_by_store_chart, revenue_trend_chart
from src.components.header import page_header
from src.components.metric_card import metric_card

st.set_page_config(
    page_title="Store Analytics",
    page_icon="🏬",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/styles.css")

page_header(
    "Store Analytics",
    "Compare store performance, benchmark locations, and identify operational opportunities."
)

st.markdown("---")

try:
    sales_df = load_sheet("Sales Table")
    store_df = load_sheet("Store Table")
    product_df = load_sheet("Product Table")

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

    sales_df["Sale_Date"] = pd.to_datetime(sales_df["Sale_Date"])

    st.subheader("Store Filters")

    store_options = ["All Stores"] + sorted(
        sales_df["Store_Name"].dropna().unique().tolist()
    )

    selected_store = st.selectbox("Store", store_options)

    if selected_store != "All Stores":
        filtered_df = sales_df[sales_df["Store_Name"] == selected_store].copy()
    else:
        filtered_df = sales_df.copy()

    total_revenue = filtered_df["Revenue"].sum()
    total_cost = filtered_df["Cost"].sum()
    total_profit = total_revenue - total_cost
    total_orders = len(filtered_df)
    total_customers = filtered_df["Customer_ID"].nunique()
    profit_margin = (total_profit / total_revenue) * 100 if total_revenue else 0

    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        metric_card(
            "Revenue",
            format_currency_short(total_revenue),
            "assets/icons/total_revenue.png",
            "",
            "#666666",
        )

    with col2:
        metric_card(
            "Profit",
            format_currency_short(total_profit),
            "assets/icons/total_profit.png",
            "",
            "#666666",
        )

    with col3:
        metric_card(
            "Orders",
            f"{total_orders:,}",
            "assets/icons/total_order.png",
            "",
            "#666666",
        )

    with col4:
        metric_card(
            "Customers",
            f"{total_customers:,}",
            "assets/icons/customer.png",
            "",
            "#666666",
        )

    with col5:
        metric_card(
            "Profit Margin",
            f"{profit_margin:.1f}%",
            "assets/icons/profit_margin.png",
            "",
            "#666666",
        )

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.plotly_chart(
            revenue_by_store_chart(sales_df),
            use_container_width=True
        )

    with chart_col2:
        st.plotly_chart(
            revenue_trend_chart(filtered_df),
            use_container_width=True
        )

    st.markdown("---")
    st.subheader("Store Leaderboard")

    store_summary = (
        sales_df.groupby("Store_Name")
        .agg(
            Revenue=("Revenue", "sum"),
            Cost=("Cost", "sum"),
            Orders=("Sale_ID", "count"),
            Customers=("Customer_ID", "nunique")
        )
        .reset_index()
    )

    store_summary["Profit"] = store_summary["Revenue"] - store_summary["Cost"]
    store_summary["Profit_Margin"] = (
        store_summary["Profit"] / store_summary["Revenue"] * 100
    )

    total_company_revenue = store_summary["Revenue"].sum()
    store_summary["Contribution"] = (
        store_summary["Revenue"] / total_company_revenue * 100
    )

    store_summary = store_summary.sort_values(
        by="Revenue",
        ascending=False
    ).reset_index(drop=True)

    for index, row in store_summary.iterrows():
        rank = index + 1

        if rank == 1:
            rank_display = "🥇"
            subtitle = "Revenue Leader"
            status = "Excellent"
            status_color = "🟢"
        elif rank == 2:
            rank_display = "🥈"
            subtitle = "Strong Performer"
            status = "Strong"
            status_color = "🟢"
        elif rank == 3:
            rank_display = "🥉"
            subtitle = "Growth Driver"
            status = "Strong"
            status_color = "🟢"
        elif rank == 4:
            rank_display = "assets/icons/4th_place.png"
            subtitle = "Stable Contributor"
            status = "Stable"
            status_color = "🟡"
        elif rank == 5:
            rank_display = "assets/icons/5th_place.png"
            subtitle = "Improvement Opportunity"
            status = "Needs Attention"
            status_color = "🔴"
        elif rank == 6:
            rank_display = "assets/icons/6th_place.png"
            subtitle = "Improvement Opportunity"
            status = "Needs Attention"
            status_color = "🔴"
        else:
            rank_display = f"#{rank}"
            subtitle = "Store Performance"
            status = "Stable"
            status_color = "🟡"

        with st.container(border=True):
            row_col1, row_col2, row_col3, row_col4, row_col5, row_col6, row_col7 = st.columns(
                [0.6, 2.4, 1.5, 1.2, 1, 1, 1.3]
            )

            with row_col1:
                if isinstance(rank_display, str) and rank_display.endswith(".png"):
                    st.image(rank_display, width=42)
                else:
                    st.markdown(f"### {rank_display}")

            with row_col2:
                st.markdown(f"**{row['Store_Name']}**")
                st.caption(subtitle)

            with row_col3:
                st.caption("Revenue")
                st.markdown(f"**{format_currency_short(row['Revenue'])}**")
                st.caption(f"{row['Contribution']:.1f}% of company revenue")

            with row_col4:
                st.caption("Profit")
                st.markdown(f"**{format_currency_short(row['Profit'])}**")

            with row_col5:
                st.caption("Orders")
                st.markdown(f"**{int(row['Orders']):,}**")

            with row_col6:
                st.caption("Margin")
                st.markdown(f"**{row['Profit_Margin']:.1f}%**")

            with row_col7:
                st.caption("Status")
                st.markdown(f"**{status_color} {status}**")

except Exception as e:
    st.error("❌ Store Performance page failed to load.")
    st.exception(e)