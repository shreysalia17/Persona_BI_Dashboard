import pandas as pd
import streamlit as st

from src.components.metric_card import metric_card, insight_card
from src.google_sheets import load_sheet
from src.calculations import (
    calculate_kpis,
    filter_sales_data,
    format_currency_short,
    calculate_kpi_change,
    get_current_previous_month_kpis,
)
from src.charts import (
    revenue_trend_chart,
    revenue_by_store_chart,
    revenue_by_category_chart,
    top_products_chart,
)
from src.insights import get_executive_insights
from src.summary import generate_executive_summary
from src.components.header import page_header


st.set_page_config(
    page_title="Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/styles.css")

page_header(
    "Business Performance Overview",
    "Enterprise Business Intelligence Platform"
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

    st.subheader("Global Filters")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    store_options = ["All Stores"] + sorted(
        sales_df["Store_Name"].dropna().unique().tolist()
    )

    category_options = ["All Categories"] + sorted(
        sales_df["Category"].dropna().unique().tolist()
    )

    year_options = ["All Years"] + sorted(
        sales_df["Sale_Date"].dt.year.dropna().unique().tolist()
    )

    quarter_options = ["All Quarters", "Q1", "Q2", "Q3", "Q4"]

    with filter_col1:
        selected_store = st.selectbox("Store", store_options)

    with filter_col2:
        selected_category = st.selectbox("Category", category_options)

    with filter_col3:
        selected_year = st.selectbox("Year", year_options)

    with filter_col4:
        selected_quarter = st.selectbox("Quarter", quarter_options)

    filtered_sales_df = filter_sales_data(
        sales_df,
        selected_store,
        selected_category,
        selected_year,
        selected_quarter,
    )

    kpis = calculate_kpis(filtered_sales_df)
    current_kpis, previous_kpis = get_current_previous_month_kpis(filtered_sales_df)

    revenue_change, revenue_color = calculate_kpi_change(
        current_kpis["total_revenue"],
        previous_kpis["total_revenue"]
    )

    profit_change, profit_color = calculate_kpi_change(
        current_kpis["total_profit"],
        previous_kpis["total_profit"]
    )

    orders_change, orders_color = calculate_kpi_change(
        current_kpis["total_orders"],
        previous_kpis["total_orders"]
    )

    customers_change, customers_color = calculate_kpi_change(
        current_kpis["unique_customers"],
        previous_kpis["unique_customers"]
    )

    aov_change, aov_color = calculate_kpi_change(
        current_kpis["average_order_value"],
        previous_kpis["average_order_value"]
    )

    margin_change, margin_color = calculate_kpi_change(
        current_kpis["profit_margin"],
        previous_kpis["profit_margin"]
    )

    st.markdown("---")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        metric_card(
            "Total Revenue",
            format_currency_short(kpis["total_revenue"]),
            "assets/icons/total_revenue.png",
            revenue_change,
            revenue_color,
        )

    with col2:
        metric_card(
            "Total Profit",
            format_currency_short(kpis["total_profit"]),
            "assets/icons/total_profit.png",
            profit_change,
            profit_color,
        )

    with col3:
        metric_card(
            "Total Orders",
            f"{kpis['total_orders']:,}",
            "assets/icons/total_order.png",
            orders_change,
            orders_color,
        )

    with col4:
        metric_card(
            "Customers",
            f"{kpis['unique_customers']:,}",
            "assets/icons/customer.png",
            customers_change,
            customers_color,
        )

    with col5:
        metric_card(
            "Avg Order Value",
            format_currency_short(kpis["average_order_value"]),
            "assets/icons/avg_order_value.png",
            aov_change,
            aov_color,
        )

    with col6:
        metric_card(
            "Profit Margin",
            f"{kpis['profit_margin']:.1f}%",
            "assets/icons/profit_margin.png",
            margin_change,
            margin_color,
        )

    insights = get_executive_insights(filtered_sales_df)
    summary_text = generate_executive_summary(
        revenue_change,
        profit_change,
        margin_change,
        insights
    )

    st.markdown("---")
    st.subheader("Executive Summary")

    st.markdown(
        f"""
        <div class="summary-card">
         {summary_text}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.subheader("Executive Insights")

    insight_col1, insight_col2, insight_col3, insight_col4 = st.columns(4)

    with insight_col1:
        insight_card(
            "Best Store",
            insights["best_store"],
            format_currency_short(insights["best_store_revenue"]),
            "assets/icons/best_store.png",
        )

    with insight_col2:
        insight_card(
            "Top Category",
            insights["top_category"],
            format_currency_short(insights["top_category_revenue"]),
            "assets/icons/top_category.png",
        )

    with insight_col3:
        insight_card(
            "Top Product",
            insights["top_product"],
            format_currency_short(insights["top_product_revenue"]),
            "assets/icons/top_product.png",
        )

    with insight_col4:
        insight_card(
            "Lowest Performing Store",
            insights["lowest_store"],
            format_currency_short(insights["lowest_store_revenue"]),
            "assets/icons/lowest_store.png",
        )

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.plotly_chart(
            revenue_trend_chart(filtered_sales_df),
            use_container_width=True
        )

    with chart_col2:
        st.plotly_chart(
            revenue_by_store_chart(sales_df),
            use_container_width=True
        )

    st.markdown("---")

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.plotly_chart(
            revenue_by_category_chart(filtered_sales_df),
            use_container_width=True
        )

    with chart_col4:
        st.plotly_chart(
            top_products_chart(filtered_sales_df),
            use_container_width=True
        )

except Exception as e:
    st.error("❌ Data loading failed.")
    st.exception(e)