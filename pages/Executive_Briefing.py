import pandas as pd
import streamlit as st

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.components.header import page_header
from src.components.metric_card import metric_card


st.set_page_config(
    page_title="Executive Briefing",
    page_icon="🤖",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def answer_question(question, metrics):
    q = question.lower()

    if "best store" in q or "top store" in q or "highest revenue store" in q:
        return f"""
### 🏆 Finding
**{metrics['top_store']}** is the strongest-performing store, generating **{format_currency_short(metrics['top_store_revenue'])}** in revenue.

### 💡 Recommendation
Study this store’s product mix, customer traffic, merchandising approach, and sales strategy to replicate success across other locations.
"""

    if "underperform" in q or "lowest store" in q or "weakest store" in q:
        return f"""
### ⚠️ Finding
**{metrics['lowest_store']}** is currently the lowest-performing store, generating **{format_currency_short(metrics['lowest_store_revenue'])}** in revenue.

### 💡 Recommendation
Review local marketing, inventory mix, staffing, customer conversion, and store-level merchandising strategy.

### 🎯 Priority
This should be reviewed as a store optimization opportunity.
"""

    if "top product" in q or "best product" in q or "highest revenue product" in q:
        return f"""
### 💎 Finding
**{metrics['top_product']}** is the highest revenue-generating product, producing **{format_currency_short(metrics['top_product_revenue'])}**.

### 💡 Recommendation
Prioritize product availability, premium placement, visual merchandising, and targeted campaigns for this product.
"""

    if "category" in q or "best category" in q or "top category" in q:
        return f"""
### 💍 Finding
**{metrics['top_category']}** is the leading category, generating **{format_currency_short(metrics['top_category_revenue'])}**.

### 💡 Recommendation
Use this category as a focus area for inventory planning, campaign strategy, and in-store merchandising.
"""

    if "customer" in q or "top customer" in q or "highest spending" in q:
        return f"""
### 👤 Finding
The highest-value customer generated **{format_currency_short(metrics['top_customer_spend'])}** in lifetime spend.

### 💡 Recommendation
Build VIP retention strategies, private offers, personalized outreach, and clienteling campaigns for high-value customers.
"""

    if "forecast" in q or "next month" in q or "future sales" in q:
        return f"""
### 📈 Forecast
The next-month revenue forecast is approximately **{format_currency_short(metrics['next_month_forecast'])}**.

### 💡 Recommendation
Align inventory, staffing, and marketing spend with forecasted demand.
"""

    if "summary" in q or "performance" in q or "business" in q:
        return f"""
### 📊 Executive Summary
The business generated **{format_currency_short(metrics['total_revenue'])}** in revenue and **{format_currency_short(metrics['total_profit'])}** in profit.

Profit margin is **{metrics['profit_margin']:.1f}%** across **{metrics['total_orders']:,}** orders.

### Executive View
Performance is led by **{metrics['top_store']}**, with **{metrics['top_category']}** driving category revenue.
"""

    if "recommend" in q or "what should" in q or "action" in q:
        return f"""
### ✅ Recommended Leadership Actions

1. Prioritize inventory and campaigns around **{metrics['top_category']}**.
2. Review performance strategy for **{metrics['lowest_store']}**.
3. Increase visibility for **{metrics['top_product']}**.
4. Build VIP campaigns for high-value customers.
5. Monitor forecasted sales demand before planning inventory.
"""

    return """
### 🤖 I can help answer questions like:

- Which store is underperforming?
- What is the top product?
- Which category is performing best?
- Who is the highest-spending customer?
- What is the next month forecast?
- Summarize business performance.
- What should leadership focus on?
"""


load_css("assets/styles.css")

page_header(
    "Executive Briefing",
    "Ask business questions and receive executive-style recommendations powered by dashboard data."
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
    sales_df["Month"] = sales_df["Sale_Date"].dt.to_period("M").astype(str)

    total_revenue = sales_df["Revenue"].sum()
    total_cost = sales_df["Cost"].sum()
    total_profit = total_revenue - total_cost
    total_orders = len(sales_df)
    unique_customers = sales_df["Customer_ID"].nunique()
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0

    store_perf = sales_df.groupby("Store_Name")["Revenue"].sum().sort_values(ascending=False)
    category_perf = sales_df.groupby("Category")["Revenue"].sum().sort_values(ascending=False)
    product_perf = sales_df.groupby("Product_Name")["Revenue"].sum().sort_values(ascending=False)
    customer_perf = sales_df.groupby("Customer_ID")["Revenue"].sum().sort_values(ascending=False)

    monthly_revenue = (
        sales_df.groupby("Month")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    monthly_revenue["Moving_Avg"] = (
        monthly_revenue["Revenue"]
        .rolling(window=3, min_periods=1)
        .mean()
    )

    next_month_forecast = (
        monthly_revenue["Moving_Avg"].iloc[-1]
        if not monthly_revenue.empty else 0
    )

    metrics = {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "unique_customers": unique_customers,
        "profit_margin": profit_margin,
        "top_store": store_perf.index[0],
        "top_store_revenue": store_perf.iloc[0],
        "lowest_store": store_perf.index[-1],
        "lowest_store_revenue": store_perf.iloc[-1],
        "top_category": category_perf.index[0],
        "top_category_revenue": category_perf.iloc[0],
        "top_product": product_perf.index[0],
        "top_product_revenue": product_perf.iloc[0],
        "top_customer": customer_perf.index[0],
        "top_customer_spend": customer_perf.iloc[0],
        "next_month_forecast": next_month_forecast,
    }

    st.subheader("Executive Copilot Summary")

    st.markdown(
        f"""
        <div class="summary-card">
            <strong>Good day, Executive Team.</strong><br><br>
            Persona generated <strong>{format_currency_short(total_revenue)}</strong> in revenue,
            <strong>{format_currency_short(total_profit)}</strong> in profit, and maintained a
            <strong>{profit_margin:.1f}%</strong> profit margin.
            <strong>{metrics["top_store"]}</strong> is leading store performance, while
            <strong>{metrics["top_category"]}</strong> is the strongest category.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        metric_card(
            "Business Health",
            "Strong",
            "assets/icons/total_revenue.png",
            "Revenue positive",
            "#2E8B57"
        )

    with kpi_col2:
        metric_card(
            "Top Store",
            metrics["top_store"],
            "assets/icons/best_store.png",
            format_currency_short(metrics["top_store_revenue"]),
            "#666666"
        )

    with kpi_col3:
        metric_card(
            "Top Category",
            metrics["top_category"],
            "assets/icons/top_product.png",
            format_currency_short(metrics["top_category_revenue"]),
            "#666666"
        )

    with kpi_col4:
        metric_card(
            "Forecast",
            format_currency_short(next_month_forecast),
            "assets/icons/avg_order_value.png",
            "Next month",
            "#666666"
        )

    st.markdown("---")

    st.subheader("Ask Persona Executive Copilot")

    question = st.text_input(
        "Ask a business question",
        placeholder="Example: Which store is underperforming? What should leadership focus on?"
    )

    if st.button("Analyze"):
        if question.strip():
            response = answer_question(question, metrics)

            with st.container(border=True):
                st.markdown("## 🤖 Executive Recommendation")
                st.markdown(response)
        else:
            st.warning("Please enter a question first.")

    st.markdown("---")

    st.subheader("Example Questions")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        - Which store is underperforming?
        - Which store has the highest revenue?
        - What is the top product?
        - Which category is performing best?
        """)

    with col2:
        st.markdown("""
        - Who is the highest-spending customer?
        - What is the next month forecast?
        - Summarize business performance.
        - What should leadership focus on?
        """)

except Exception as e:
    st.error("❌ Executive Briefing page failed to load.")
    st.exception(e)