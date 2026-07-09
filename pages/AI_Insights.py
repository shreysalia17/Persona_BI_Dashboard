import pandas as pd
import streamlit as st

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.components.header import page_header


st.set_page_config(
    page_title="AI Business Insights",
    page_icon="🤖",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/styles.css")

page_header(
    "AI Business Insights",
    "Generate executive recommendations from revenue, customer, store, and product performance patterns."
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
    sales_df["Month"] = sales_df["Sale_Date"].dt.to_period("M").astype(str)
    sales_df["Year"] = sales_df["Sale_Date"].dt.year

    st.subheader("Insight Filters")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    store_options = ["All Stores"] + sorted(
        sales_df["Store_Name"].dropna().unique().tolist()
    )

    category_options = ["All Categories"] + sorted(
        sales_df["Category"].dropna().unique().tolist()
    )

    year_options = ["All Years"] + sorted(
        sales_df["Year"].dropna().unique().tolist()
    )

    with filter_col1:
        selected_store = st.selectbox("Store", store_options)

    with filter_col2:
        selected_category = st.selectbox("Category", category_options)

    with filter_col3:
        selected_year = st.selectbox("Year", year_options)

    filtered_df = sales_df.copy()

    if selected_store != "All Stores":
        filtered_df = filtered_df[filtered_df["Store_Name"] == selected_store]

    if selected_category != "All Categories":
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]

    if selected_year != "All Years":
        filtered_df = filtered_df[filtered_df["Year"] == selected_year]

    total_revenue = filtered_df["Revenue"].sum()
    total_cost = filtered_df["Cost"].sum()
    total_profit = total_revenue - total_cost
    total_orders = len(filtered_df)
    total_customers = filtered_df["Customer_ID"].nunique()
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0
    avg_order_value = total_revenue / total_orders if total_orders else 0

    monthly_revenue = (
        filtered_df.groupby("Month")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    if len(monthly_revenue) >= 2:
        latest_revenue = monthly_revenue.iloc[-1]["Revenue"]
        previous_revenue = monthly_revenue.iloc[-2]["Revenue"]

        revenue_change = (
            (latest_revenue - previous_revenue) / previous_revenue * 100
            if previous_revenue else 0
        )
    else:
        latest_revenue = total_revenue
        previous_revenue = 0
        revenue_change = 0

    store_performance = (
        filtered_df.groupby("Store_Name")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    category_performance = (
        filtered_df.groupby("Category")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    product_performance = (
        filtered_df.groupby("Product_Name")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    customer_summary = (
        filtered_df.groupby("Customer_ID")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("Sale_ID", "count")
        )
        .reset_index()
    )

    repeat_customers = customer_summary[
        customer_summary["Orders"] > 1
    ]["Customer_ID"].nunique()

    repeat_rate = (
        repeat_customers / total_customers * 100
        if total_customers else 0
    )

    top_store = store_performance.index[0] if not store_performance.empty else "N/A"
    top_store_revenue = store_performance.iloc[0] if not store_performance.empty else 0

    weakest_store = store_performance.index[-1] if not store_performance.empty else "N/A"
    weakest_store_revenue = store_performance.iloc[-1] if not store_performance.empty else 0

    top_category = category_performance.index[0] if not category_performance.empty else "N/A"
    top_category_revenue = category_performance.iloc[0] if not category_performance.empty else 0

    top_product = product_performance.index[0] if not product_performance.empty else "N/A"
    top_product_revenue = product_performance.iloc[0] if not product_performance.empty else 0

    revenue_direction = "increased" if revenue_change >= 0 else "declined"
    revenue_symbol = "▲" if revenue_change >= 0 else "▼"
    revenue_color = "#2E8B57" if revenue_change >= 0 else "#D9534F"

    st.markdown("---")

    st.subheader("AI Executive Brief")

    st.markdown(
        f"""
        <div class="summary-card">
            Revenue <strong style="color:{revenue_color};">
            {revenue_symbol} {abs(revenue_change):.1f}%</strong> compared to the previous month.
            The selected view generated <strong>{format_currency_short(total_revenue)}</strong>
            in revenue, <strong>{format_currency_short(total_profit)}</strong> in profit,
            and maintained a profit margin of <strong>{profit_margin:.1f}%</strong>.
            <strong>{top_store}</strong> is currently the strongest-performing store,
            while <strong>{top_category}</strong> leads category performance.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown(
            f"""
            <div class="summary-card">
                <h4>🏆 Biggest Win</h4>
                <p>
                    <strong>{top_store}</strong> generated
                    <strong>{format_currency_short(top_store_revenue)}</strong>
                    in revenue, making it the strongest location in the selected view.
                </p>
                <p><strong>Action:</strong> Review its product mix, staffing, and merchandising strategy for replication.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with insight_col2:
        st.markdown(
            f"""
            <div class="summary-card">
                <h4>💎 Product Opportunity</h4>
                <p>
                    <strong>{top_product}</strong> generated
                    <strong>{format_currency_short(top_product_revenue)}</strong>
                    in revenue.
                </p>
                <p><strong>Action:</strong> Prioritize availability, promotion, and premium placement for this product.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with insight_col3:
        st.markdown(
            f"""
            <div class="summary-card">
                <h4>⚠ Area to Review</h4>
                <p>
                    <strong>{weakest_store}</strong> generated
                    <strong>{format_currency_short(weakest_store_revenue)}</strong>,
                    the lowest store revenue in the selected view.
                </p>
                <p><strong>Action:</strong> Review traffic, conversion, inventory, and local marketing performance.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    rec_col1, rec_col2 = st.columns(2)

    with rec_col1:
        st.subheader("Recommended Business Actions")

        actions = []

        if revenue_change < 0:
            actions.append(
                "Investigate the revenue decline by reviewing store traffic, category performance, and promotional activity."
            )
        else:
            actions.append(
                "Continue monitoring growth drivers and identify whether the increase is coming from stores, products, or repeat customers."
            )

        if profit_margin < 40:
            actions.append(
                "Review pricing and cost structure because profit margin is below a healthy luxury retail threshold."
            )
        else:
            actions.append(
                "Maintain current pricing discipline since profit margin remains strong."
            )

        if repeat_rate < 50:
            actions.append(
                "Improve customer retention through loyalty campaigns, personalized offers, and clienteling."
            )
        else:
            actions.append(
                "Leverage repeat customers with VIP experiences, exclusive previews, and premium upsell campaigns."
            )

        actions.append(
            f"Use {top_category} as a priority category for merchandising, campaign planning, and inventory allocation."
        )

        for action in actions:
            st.markdown(f"- {action}")

    with rec_col2:
        st.subheader("Key Business Signals")

        signal_data = pd.DataFrame(
            {
                "Signal": [
                    "Revenue Trend",
                    "Profit Margin",
                    "Repeat Customer Rate",
                    "Top Store",
                    "Top Category",
                    "Top Product",
                ],
                "Result": [
                    f"{revenue_symbol} {abs(revenue_change):.1f}%",
                    f"{profit_margin:.1f}%",
                    f"{repeat_rate:.1f}%",
                    top_store,
                    top_category,
                    top_product,
                ],
            }
        )

        st.dataframe(
            signal_data,
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    st.subheader("AI Insight Questions Answered")

    st.markdown(
        """
        This page helps answer:
        
        - Is revenue improving or declining?
        - Which store is leading performance?
        - Which store requires leadership attention?
        - Which category is driving the business?
        - Which product should be prioritized?
        - Are customers showing repeat-purchase behavior?
        - What should leadership focus on next?
        """
    )

except Exception as e:
    st.error("❌ AI Business Insights page failed to load.")
    st.exception(e)