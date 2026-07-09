import pandas as pd
import plotly.express as px
import streamlit as st

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.components.header import page_header
from src.components.metric_card import metric_card


st.set_page_config(
    page_title="Product Analytics",
    page_icon="💎",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/styles.css")

page_header(
    "Product Analytics",
    "Analyze product performance, profitability, demand, and category trends."
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

    st.subheader("Product Filters")

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

    product_summary = (
        filtered_df.groupby(["Product_ID", "Product_Name", "Category"])
        .agg(
            Revenue=("Revenue", "sum"),
            Cost=("Cost", "sum"),
            Units_Sold=("Quantity", "sum"),
            Orders=("Sale_ID", "count"),
            Avg_Order_Value=("Revenue", "mean")
        )
        .reset_index()
    )

    product_summary["Profit"] = (
        product_summary["Revenue"] - product_summary["Cost"]
    )

    product_summary["Profit_Margin"] = (
        product_summary["Profit"] / product_summary["Revenue"] * 100
    )

    total_products = product_summary["Product_ID"].nunique()
    total_units_sold = product_summary["Units_Sold"].sum()
    total_revenue = product_summary["Revenue"].sum()
    avg_margin = product_summary["Profit_Margin"].mean() if total_products else 0

    top_product = (
        product_summary.sort_values("Revenue", ascending=False)
        .iloc[0]["Product_Name"]
        if total_products else "N/A"
    )

    top_product_display = (
        top_product[:18] + "..."
        if len(top_product) > 18
        else top_product
    )

    st.markdown("---")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        metric_card(
            "Products Sold",
            f"{total_products:,}",
            "assets/icons/product_sold.png",
            "",
            "#666666",
        )

    with kpi_col2:
        metric_card(
            "Units Sold",
            f"{int(total_units_sold):,}",
            "assets/icons/unit_sold.png",
            "",
            "#666666",
        )

    with kpi_col3:
        metric_card(
            "Revenue",
            format_currency_short(total_revenue),
            "assets/icons/total_revenue.png",
            "",
            "#666666",
        )

    with kpi_col4:
        metric_card(
            "Avg Profit Margin",
            f"{avg_margin:.1f}%",
            "assets/icons/avg_profit_margin.png",
            "",
            "#666666",
        )

    with kpi_col5:
        metric_card(
            "Top Product",
            top_product_display,
            "assets/icons/top_product.png",
            "",
            "#666666",
        )

    st.markdown("---")

    st.subheader("Product Performance Summary")

    best_product = product_summary.sort_values(
        "Revenue",
        ascending=False
    ).iloc[0]

    highest_margin_product = product_summary.sort_values(
        "Profit_Margin",
        ascending=False
    ).iloc[0]

    lowest_selling_product = product_summary.sort_values(
        "Units_Sold",
        ascending=True
    ).iloc[0]

    st.markdown(
        f"""
        <div class="summary-card">
            <strong>{best_product["Product_Name"]}</strong> is the highest
            revenue-generating product, producing
            <strong>{format_currency_short(best_product["Revenue"])}</strong>
            in sales.
            <strong>{highest_margin_product["Product_Name"]}</strong> has the
            strongest profit margin at
            <strong>{highest_margin_product["Profit_Margin"]:.1f}%</strong>.
            <strong>{lowest_selling_product["Product_Name"]}</strong> has the
            lowest unit sales and may need pricing, placement, or promotion review.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        top_selling = (
            product_summary.sort_values("Units_Sold", ascending=False)
            .head(10)
            .sort_values("Units_Sold", ascending=True)
        )

        fig = px.bar(
            top_selling,
            x="Units_Sold",
            y="Product_Name",
            orientation="h",
            title="Top Selling Products",
        )

        fig.update_traces(marker_color="#C9A24D")

        fig.update_layout(
            template="plotly_white",
            height=420,
            paper_bgcolor="#FFFDF8",
            plot_bgcolor="#FFFDF8",
            xaxis_title="Units Sold",
            yaxis_title="",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        least_selling = (
            product_summary.sort_values("Units_Sold", ascending=True)
            .head(10)
            .sort_values("Units_Sold", ascending=True)
        )

        fig = px.bar(
            least_selling,
            x="Units_Sold",
            y="Product_Name",
            orientation="h",
            title="Least Selling Products",
        )

        fig.update_traces(marker_color="#C47A55")

        fig.update_layout(
            template="plotly_white",
            height=420,
            paper_bgcolor="#FFFDF8",
            plot_bgcolor="#FFFDF8",
            xaxis_title="Units Sold",
            yaxis_title="",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        profitable_products = (
            product_summary.sort_values("Profit", ascending=False)
            .head(10)
            .sort_values("Profit", ascending=True)
        )

        fig = px.bar(
            profitable_products,
            x="Profit",
            y="Product_Name",
            orientation="h",
            title="Most Profitable Products",
        )

        fig.update_traces(marker_color="#5E6B4E")

        fig.update_layout(
            template="plotly_white",
            height=420,
            paper_bgcolor="#FFFDF8",
            plot_bgcolor="#FFFDF8",
            xaxis_title="Profit",
            yaxis_title="",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    with chart_col4:
        category_revenue = (
            product_summary.groupby("Category")["Revenue"]
            .sum()
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )

        fig = px.pie(
            category_revenue,
            names="Category",
            values="Revenue",
            title="Revenue by Category",
            hole=0.48,
            color_discrete_sequence=[
                "#D8C29D",
                "#5E6B4E",
                "#C47A55",
                "#A9B49A",
                "#C9A24D",
                "#7A5C3E"
            ],
        )

        fig.update_layout(
            template="plotly_white",
            height=420,
            paper_bgcolor="#FFFDF8",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Product Leaderboard")

    product_summary = product_summary.sort_values(
        by="Revenue",
        ascending=False
    ).reset_index(drop=True)

    for index, row in product_summary.head(15).iterrows():
        rank = index + 1

        if rank == 1:
            rank_display = "🥇"
            rank_type = "emoji"
            status = "Revenue Leader"
            status_color = "🟢"
        elif rank == 2:
            rank_display = "🥈"
            rank_type = "emoji"
            status = "Strong Performer"
            status_color = "🟢"
        elif rank == 3:
            rank_display = "🥉"
            rank_type = "emoji"
            status = "High Demand"
            status_color = "🟢"
        elif 4 <= rank <= 15:
            rank_display = f"assets/icons/{rank}th_place.png"
            rank_type = "image"

            if row["Profit_Margin"] >= avg_margin:
                status = "Healthy Margin"
                status_color = "🟡"
            else:
                status = "Review Needed"
                status_color = "🔴"
        else:
            rank_display = f"#{rank}"
            rank_type = "text"
            status = "Review Needed"
            status_color = "🔴"

        with st.container(border=True):
            row_col1, row_col2, row_col3, row_col4, row_col5, row_col6, row_col7 = st.columns(
                [0.6, 2.4, 1.3, 1.2, 1.2, 1.2, 1.4]
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
                st.caption("Revenue")
                st.markdown(f"**{format_currency_short(row['Revenue'])}**")

            with row_col4:
                st.caption("Profit")
                st.markdown(f"**{format_currency_short(row['Profit'])}**")

            with row_col5:
                st.caption("Units Sold")
                st.markdown(f"**{int(row['Units_Sold']):,}**")

            with row_col6:
                st.caption("Margin")
                st.markdown(f"**{row['Profit_Margin']:.1f}%**")

            with row_col7:
                st.caption("Status")
                st.markdown(f"**{status_color} {status}**")

except Exception as e:
    st.error("❌ Product Analytics page failed to load.")
    st.exception(e)