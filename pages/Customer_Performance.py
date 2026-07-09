import pandas as pd
import streamlit as st

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.components.header import page_header
from src.components.metric_card import metric_card


st.set_page_config(
    page_title="Customer Analytics",
    page_icon="👥",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/styles.css")

page_header(
    "Customer Analytics",
    "Analyze customer value, purchasing behavior, and engagement patterns across the business."
)

st.markdown("---")

try:
    sales_df = load_sheet("Sales Table")
    customer_df = load_sheet("Customer Table")
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

    sales_df = sales_df.merge(
        customer_df,
        on="Customer_ID",
        how="left"
    )

    sales_df["Sale_Date"] = pd.to_datetime(sales_df["Sale_Date"])

    st.subheader("Customer Filters")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    store_options = ["All Stores"] + sorted(
        sales_df["Store_Name"].dropna().unique().tolist()
    )

    category_options = ["All Categories"] + sorted(
        sales_df["Category"].dropna().unique().tolist()
    )

    year_options = ["All Years"] + sorted(
        sales_df["Sale_Date"].dt.year.dropna().unique().tolist()
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
        filtered_df = filtered_df[
            filtered_df["Sale_Date"].dt.year == selected_year
        ]

    customer_summary = (
        filtered_df.groupby("Customer_ID")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("Sale_ID", "count"),
            Avg_Order_Value=("Revenue", "mean")
        )
        .reset_index()
    )

    total_customers = customer_summary["Customer_ID"].nunique()

    repeat_customers = customer_summary[
        customer_summary["Orders"] > 1
    ]["Customer_ID"].nunique()

    repeat_rate = (
        repeat_customers / total_customers * 100
    ) if total_customers else 0

    avg_customer_value = (
        customer_summary["Revenue"].mean()
    ) if total_customers else 0

    avg_orders_per_customer = (
        customer_summary["Orders"].mean()
    ) if total_customers else 0

    top_customer_revenue = (
        customer_summary["Revenue"].max()
    ) if total_customers else 0

    st.markdown("---")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        metric_card(
            "Unique Customers",
            f"{total_customers:,}",
            "assets/icons/unique_customer.png",
            "",
            "#666666",
        )

    with kpi_col2:
        metric_card(
            "Repeat Customers",
            f"{repeat_customers:,}",
            "assets/icons/customer.png",
            f"▲ {repeat_rate:.1f}% Repeat Rate",
            "#2E8B57",
        )

    with kpi_col3:
        metric_card(
            "Avg Customer Value",
            format_currency_short(avg_customer_value),
            "assets/icons/avg_order_value.png",
            "",
            "#666666",
        )

    with kpi_col4:
        metric_card(
            "Avg Customer Order",
            f"{avg_orders_per_customer:.1f}",
            "assets/icons/avg_customer_order.png",
            "",
            "#666666",
        )

    with kpi_col5:
        metric_card(
            "Top Customer Spend",
            format_currency_short(top_customer_revenue),
            "assets/icons/total_revenue.png",
            "",
            "#666666",
        )

    st.markdown("---")

    st.subheader("Customer Summary")

    st.markdown(
        f"""
        <div class="summary-card">
            The business currently has <strong>{total_customers:,}</strong>
            unique customers in the selected view. Repeat customers represent
            <strong>{repeat_rate:.1f}%</strong> of the customer base, with an
            average customer value of
            <strong>{format_currency_short(avg_customer_value)}</strong>.
            The highest-value customer generated
            <strong>{format_currency_short(top_customer_revenue)}</strong>
            in lifetime spend.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Top 10 Customers by Spend")

        top_customers = (
            customer_summary.sort_values("Revenue", ascending=False)
            .head(10)
            .copy()
        )

        st.bar_chart(
            top_customers.set_index("Customer_ID")["Revenue"]
        )

    with chart_col2:
        st.subheader("Customers by Store")

        customers_by_store = (
            filtered_df.groupby("Store_Name")["Customer_ID"]
            .nunique()
            .sort_values(ascending=False)
        )

        st.bar_chart(customers_by_store)

    st.markdown("---")
    st.subheader("Customer Leaderboard")

    customer_summary = customer_summary.sort_values(
        by="Revenue",
        ascending=False
    ).reset_index(drop=True)

    top_10_customers = customer_summary.head(10).copy()

    for index, row in top_10_customers.iterrows():
        rank = index + 1

        if rank == 1:
            rank_display = "🥇"
            rank_type = "emoji"
            status = "VIP Customer"
            status_color = "🟢"
        elif rank == 2:
            rank_display = "🥈"
            rank_type = "emoji"
            status = "High Value"
            status_color = "🟢"
        elif rank == 3:
            rank_display = "🥉"
            rank_type = "emoji"
            status = "High Value"
            status_color = "🟢"
        elif 4 <= rank <= 10:
            rank_display = f"assets/icons/{rank}th_place.png"
            rank_type = "image"

            if row["Orders"] > 3:
                status = "Loyal Customer"
                status_color = "🟡"
            else:
                status = "One-Time Buyer"
                status_color = "🔴"
        else:
            rank_display = f"#{rank}"
            rank_type = "text"
            status = "One-Time Buyer"
            status_color = "🔴"

        with st.container(border=True):
            row_col1, row_col2, row_col3, row_col4, row_col5 = st.columns(
                [0.7, 2.4, 1.5, 1.3, 1.5]
            )

            with row_col1:
                if rank_type == "image":
                    st.image(rank_display, width=42)
                else:
                    st.markdown(f"### {rank_display}")

            with row_col2:
                st.markdown(f"**{row['Customer_ID']}**")
                st.caption("Customer Profile")

            with row_col3:
                st.caption("Lifetime Spend")
                st.markdown(f"**{format_currency_short(row['Revenue'])}**")

            with row_col4:
                st.caption("Orders")
                st.markdown(f"**{int(row['Orders']):,}**")

            with row_col5:
                st.caption("Status")
                st.markdown(f"**{status_color} {status}**")

    st.markdown("---")
    st.subheader("Customer Purchase Detail")

    top_customer_options = top_10_customers["Customer_ID"].tolist()

    selected_customer = st.selectbox(
        "Select a top customer to view purchase history",
        top_customer_options
    )

    customer_purchases = filtered_df[
        filtered_df["Customer_ID"] == selected_customer
    ].copy()

    customer_purchases = customer_purchases[
        [
            "Sale_Date",
            "Store_Name",
            "Category",
            "Product_Name",
            "Quantity",
            "Revenue"
        ]
    ].sort_values("Sale_Date", ascending=False)

    customer_purchases["Sale_Date"] = customer_purchases["Sale_Date"].dt.strftime(
        "%Y-%m-%d"
    )

    customer_purchases["Revenue"] = customer_purchases["Revenue"].apply(
        lambda x: f"${x:,.0f}"
    )

    st.dataframe(
        customer_purchases,
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("❌ Customer Analytics page failed to load.")
    st.exception(e)