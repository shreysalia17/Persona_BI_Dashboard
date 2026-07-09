import pandas as pd
import plotly.express as px
import streamlit as st

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.components.header import page_header
from src.components.metric_card import metric_card


st.set_page_config(
    page_title="Inventory Intelligence",
    page_icon="📦",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/styles.css")

page_header(
    "Inventory Intelligence",
    "Monitor product movement, stock risk, and replenishment opportunities across the business."
)

st.markdown("---")

try:
    sales_df = load_sheet("Sales Table")
    product_df = load_sheet("Product Table")
    store_df = load_sheet("Store Table")

    sales_df = sales_df.merge(
        product_df[["Product_ID", "Product_Name", "Category"]],
        on="Product_ID",
        how="left"
    )

    sales_df = sales_df.merge(
        store_df[["Store_ID", "Store_Name"]],
        on="Store_ID",
        how="left"
    )

    sales_df["Sale_Date"] = pd.to_datetime(sales_df["Sale_Date"])
    sales_df["Year"] = sales_df["Sale_Date"].dt.year
    sales_df["Month"] = sales_df["Sale_Date"].dt.to_period("M").astype(str)

    st.subheader("Inventory Filters")

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

    product_summary = (
        filtered_df.groupby(["Product_ID", "Product_Name", "Category"])
        .agg(
            Units_Sold=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
            Cost=("Cost", "sum"),
            Orders=("Sale_ID", "count"),
            Active_Months=("Month", "nunique")
        )
        .reset_index()
    )

    product_summary["Profit"] = product_summary["Revenue"] - product_summary["Cost"]

    product_summary["Avg_Monthly_Units"] = (
        product_summary["Units_Sold"] / product_summary["Active_Months"]
    )

    avg_units = product_summary["Units_Sold"].mean() if not product_summary.empty else 0

    product_summary["Movement_Status"] = product_summary["Units_Sold"].apply(
        lambda x: "Fast Moving" if x >= avg_units else "Slow Moving"
    )

    fast_moving_count = product_summary[
        product_summary["Movement_Status"] == "Fast Moving"
    ]["Product_ID"].nunique()

    slow_moving_count = product_summary[
        product_summary["Movement_Status"] == "Slow Moving"
    ]["Product_ID"].nunique()

    total_products = product_summary["Product_ID"].nunique()
    total_units_moved = product_summary["Units_Sold"].sum()
    estimated_inventory_value = product_summary["Cost"].sum()

    stock_risk_products = product_summary[
        product_summary["Units_Sold"] >= product_summary["Units_Sold"].quantile(0.75)
    ]["Product_ID"].nunique()

    st.markdown("---")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        metric_card(
            "Tracked Products",
            f"{total_products:,}",
            "assets/icons/product_sold.png",
            "",
            "#666666",
        )

    with kpi_col2:
        metric_card(
            "Units Moved",
            f"{int(total_units_moved):,}",
            "assets/icons/unit_sold.png",
            "",
            "#666666",
        )

    with kpi_col3:
        metric_card(
            "Inventory Value",
            format_currency_short(estimated_inventory_value),
            "assets/icons/total_revenue.png",
            "",
            "#666666",
        )

    with kpi_col4:
        metric_card(
            "Fast Moving",
            f"{fast_moving_count:,}",
            "assets/icons/top_product.png",
            "",
            "#666666",
        )

    with kpi_col5:
        metric_card(
            "Stock Risk",
            f"{stock_risk_products:,}",
            "assets/icons/avg_profit_margin.png",
            "",
            "#666666",
        )

    st.markdown("---")

    st.subheader("Inventory Intelligence Summary")

    fastest_product = (
        product_summary.sort_values("Units_Sold", ascending=False).iloc[0]
        if not product_summary.empty else None
    )

    slowest_product = (
        product_summary.sort_values("Units_Sold", ascending=True).iloc[0]
        if not product_summary.empty else None
    )

    if fastest_product is not None and slowest_product is not None:
        st.markdown(
            f"""
            <div class="summary-card">
                <strong>{fastest_product["Product_Name"]}</strong> is the fastest-moving product,
                with <strong>{int(fastest_product["Units_Sold"]):,}</strong> units sold in the selected view.
                <strong>{slow_moving_count:,}</strong> products are moving below the average sales velocity
                and may require pricing, placement, or promotional review.
                <strong>{stock_risk_products:,}</strong> high-demand products should be monitored for possible
                replenishment risk.
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        movement_counts = (
            product_summary["Movement_Status"]
            .value_counts()
            .reset_index()
        )

        movement_counts.columns = ["Movement_Status", "Products"]

        fig = px.pie(
            movement_counts,
            names="Movement_Status",
            values="Products",
            title="Fast vs Slow Moving Products",
            hole=0.48,
            color_discrete_sequence=[
                "#5E6B4E",
                "#C47A55"
            ],
        )

        fig.update_layout(
            template="plotly_white",
            height=430,
            paper_bgcolor="#FFFDF8",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        category_units = (
            product_summary.groupby("Category")["Units_Sold"]
            .sum()
            .reset_index()
            .sort_values("Units_Sold", ascending=True)
        )

        fig = px.bar(
            category_units,
            x="Units_Sold",
            y="Category",
            orientation="h",
            title="Units Moved by Category"
        )

        fig.update_traces(marker_color="#C9A24D")

        fig.update_layout(
            template="plotly_white",
            height=430,
            paper_bgcolor="#FFFDF8",
            plot_bgcolor="#FFFDF8",
            xaxis_title="Units Moved",
            yaxis_title="",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        fast_products = (
            product_summary.sort_values("Units_Sold", ascending=False)
            .head(10)
            .sort_values("Units_Sold", ascending=True)
        )

        fig = px.bar(
            fast_products,
            x="Units_Sold",
            y="Product_Name",
            orientation="h",
            title="Fastest Moving Products"
        )

        fig.update_traces(marker_color="#5E6B4E")

        fig.update_layout(
            template="plotly_white",
            height=430,
            paper_bgcolor="#FFFDF8",
            plot_bgcolor="#FFFDF8",
            xaxis_title="Units Sold",
            yaxis_title="",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    with chart_col4:
        slow_products = (
            product_summary.sort_values("Units_Sold", ascending=True)
            .head(10)
            .sort_values("Units_Sold", ascending=True)
        )

        fig = px.bar(
            slow_products,
            x="Units_Sold",
            y="Product_Name",
            orientation="h",
            title="Slowest Moving Products"
        )

        fig.update_traces(marker_color="#C47A55")

        fig.update_layout(
            template="plotly_white",
            height=430,
            paper_bgcolor="#FFFDF8",
            plot_bgcolor="#FFFDF8",
            xaxis_title="Units Sold",
            yaxis_title="",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Inventory Movement Leaderboard")

    product_summary = product_summary.sort_values(
        by="Units_Sold",
        ascending=False
    ).reset_index(drop=True)

    for index, row in product_summary.head(15).iterrows():
        rank = index + 1

        if rank == 1:
            rank_display = "🥇"
            rank_type = "emoji"
            status = "Fastest Moving"
            status_color = "🟢"
        elif rank == 2:
            rank_display = "🥈"
            rank_type = "emoji"
            status = "High Demand"
            status_color = "🟢"
        elif rank == 3:
            rank_display = "🥉"
            rank_type = "emoji"
            status = "Strong Movement"
            status_color = "🟢"
        elif 4 <= rank <= 15:
            rank_display = f"assets/icons/{rank}th_place.png"
            rank_type = "image"

            if row["Movement_Status"] == "Fast Moving":
                status = "Fast Moving"
                status_color = "🟡"
            else:
                status = "Slow Moving"
                status_color = "🔴"
        else:
            rank_display = f"#{rank}"
            rank_type = "text"
            status = row["Movement_Status"]
            status_color = "🟡"

        with st.container(border=True):
            row_col1, row_col2, row_col3, row_col4, row_col5, row_col6 = st.columns(
                [0.6, 2.4, 1.3, 1.4, 1.4, 1.5]
            )

            with row_col1:
                if rank_type == "image":
                    st.image(rank_display, width=42)
                else:
                    st.markdown(f"### {rank_display}")

            with row_col2:
                st.markdown(f"**{row['Product_Name']}**")
                st.caption(row["Category"])

            with row_col3:
                st.caption("Units Sold")
                st.markdown(f"**{int(row['Units_Sold']):,}**")

            with row_col4:
                st.caption("Revenue")
                st.markdown(f"**{format_currency_short(row['Revenue'])}**")

            with row_col5:
                st.caption("Avg Monthly Units")
                st.markdown(f"**{row['Avg_Monthly_Units']:.1f}**")

            with row_col6:
                st.caption("Status")
                st.markdown(f"**{status_color} {status}**")

except Exception as e:
    st.error("❌ Inventory Intelligence page failed to load.")
    st.exception(e)