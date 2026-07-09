import pandas as pd
import plotly.express as px
import streamlit as st

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.components.header import page_header
from src.components.metric_card import metric_card


st.set_page_config(
    page_title="Sales Analytics",
    page_icon="📈",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/styles.css")

page_header(
    "Sales Analytics",
    "Monitor sales trends, seasonal performance, and revenue growth across the business."
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
    sales_df["Quarter"] = "Q" + sales_df["Sale_Date"].dt.quarter.astype(str)
    sales_df["Weekday"] = sales_df["Sale_Date"].dt.day_name()

    st.subheader("Sales Filters")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    store_options = ["All Stores"] + sorted(
        sales_df["Store_Name"].dropna().unique().tolist()
    )

    category_options = ["All Categories"] + sorted(
        sales_df["Category"].dropna().unique().tolist()
    )

    year_options = ["All Years"] + sorted(
        sales_df["Year"].dropna().unique().tolist()
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

    filtered_df = sales_df.copy()

    if selected_store != "All Stores":
        filtered_df = filtered_df[filtered_df["Store_Name"] == selected_store]

    if selected_category != "All Categories":
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]

    if selected_year != "All Years":
        filtered_df = filtered_df[filtered_df["Year"] == selected_year]

    if selected_quarter != "All Quarters":
        filtered_df = filtered_df[filtered_df["Quarter"] == selected_quarter]

    total_revenue = filtered_df["Revenue"].sum()
    total_orders = len(filtered_df)
    total_units = filtered_df["Quantity"].sum()
    avg_order_value = total_revenue / total_orders if total_orders else 0

    monthly_sales = (
        filtered_df.groupby("Month")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    best_month = (
        monthly_sales.sort_values("Revenue", ascending=False).iloc[0]["Month"]
        if not monthly_sales.empty else "N/A"
    )

    best_month_revenue = (
        monthly_sales.sort_values("Revenue", ascending=False).iloc[0]["Revenue"]
        if not monthly_sales.empty else 0
    )

    daily_sales = (
        filtered_df.groupby("Sale_Date")["Revenue"]
        .sum()
        .reset_index()
    )

    st.markdown("---")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        metric_card(
            "Total Revenue",
            format_currency_short(total_revenue),
            "assets/icons/total_revenue.png",
            "",
            "#666666",
        )

    with kpi_col2:
        metric_card(
            "Total Orders",
            f"{total_orders:,}",
            "assets/icons/total_order.png",
            "",
            "#666666",
        )

    with kpi_col3:
        metric_card(
            "Units Sold",
            f"{int(total_units):,}",
            "assets/icons/unit_sold.png",
            "",
            "#666666",
        )

    with kpi_col4:
        metric_card(
            "Avg Order Value",
            format_currency_short(avg_order_value),
            "assets/icons/avg_order_value.png",
            "",
            "#666666",
        )

    with kpi_col5:
        metric_card(
            "Best Sales Month",
            str(best_month),
            "assets/icons/top_product.png",
            format_currency_short(best_month_revenue),
            "#666666",
        )

    st.markdown("---")

    st.subheader("Sales Performance Summary")

    top_store = (
        filtered_df.groupby("Store_Name")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    top_category = (
        filtered_df.groupby("Category")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    top_weekday = (
        filtered_df.groupby("Weekday")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    top_store_name = top_store.index[0] if not top_store.empty else "N/A"
    top_category_name = top_category.index[0] if not top_category.empty else "N/A"
    top_weekday_name = top_weekday.index[0] if not top_weekday.empty else "N/A"

    st.markdown(
        f"""
        <div class="summary-card">
            The selected view generated <strong>{format_currency_short(total_revenue)}</strong>
            across <strong>{total_orders:,}</strong> orders and
            <strong>{int(total_units):,}</strong> units sold.
            <strong>{top_store_name}</strong> is the strongest sales location,
            while <strong>{top_category_name}</strong> leads category revenue.
            Sales activity is strongest on <strong>{top_weekday_name}</strong>,
            helping leadership understand sales timing and demand patterns.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig = px.line(
            monthly_sales,
            x="Month",
            y="Revenue",
            title="Monthly Revenue Trend",
            markers=True
        )

        fig.update_traces(line_color="#C9A24D", marker_color="#C9A24D")

        fig.update_layout(
            template="plotly_white",
            height=430,
            paper_bgcolor="#FFFDF8",
            plot_bgcolor="#FFFDF8",
            xaxis_title="Month",
            yaxis_title="Revenue",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        revenue_by_store = (
            filtered_df.groupby("Store_Name")["Revenue"]
            .sum()
            .reset_index()
            .sort_values("Revenue", ascending=True)
        )

        fig = px.bar(
            revenue_by_store,
            x="Revenue",
            y="Store_Name",
            orientation="h",
            title="Sales by Store"
        )

        fig.update_traces(marker_color="#C9A24D")

        fig.update_layout(
            template="plotly_white",
            height=430,
            paper_bgcolor="#FFFDF8",
            plot_bgcolor="#FFFDF8",
            xaxis_title="Revenue",
            yaxis_title="",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        category_sales = (
            filtered_df.groupby("Category")["Revenue"]
            .sum()
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )

        fig = px.pie(
            category_sales,
            names="Category",
            values="Revenue",
            title="Sales Contribution by Category",
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
            height=430,
            paper_bgcolor="#FFFDF8",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    with chart_col4:
        weekday_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ]

        weekday_sales = (
            filtered_df.groupby("Weekday")["Revenue"]
            .sum()
            .reindex(weekday_order)
            .reset_index()
            .dropna()
        )

        fig = px.bar(
            weekday_sales,
            x="Weekday",
            y="Revenue",
            title="Sales by Weekday"
        )

        fig.update_traces(marker_color="#5E6B4E")

        fig.update_layout(
            template="plotly_white",
            height=430,
            paper_bgcolor="#FFFDF8",
            plot_bgcolor="#FFFDF8",
            xaxis_title="Weekday",
            yaxis_title="Revenue",
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Monthly Sales Leaderboard")

    monthly_summary = (
        filtered_df.groupby("Month")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("Sale_ID", "count"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .reset_index(drop=True)
    )

    monthly_summary["Avg_Order_Value"] = (
        monthly_summary["Revenue"] / monthly_summary["Orders"]
    )

    for index, row in monthly_summary.head(10).iterrows():
        rank = index + 1

        if rank == 1:
            rank_display = "🥇"
            rank_type = "emoji"
            status = "Peak Sales Month"
            status_color = "🟢"
        elif rank == 2:
            rank_display = "🥈"
            rank_type = "emoji"
            status = "Strong Month"
            status_color = "🟢"
        elif rank == 3:
            rank_display = "🥉"
            rank_type = "emoji"
            status = "High Performing"
            status_color = "🟢"
        elif rank <= 10:
            rank_display = f"assets/icons/{rank}th_place.png"
            rank_type = "image"
            status = "Above Average" if row["Revenue"] >= monthly_summary["Revenue"].mean() else "Below Average"
            status_color = "🟡" if row["Revenue"] >= monthly_summary["Revenue"].mean() else "🔴"
        else:
            rank_display = f"#{rank}"
            rank_type = "text"
            status = "Below Average"
            status_color = "🔴"

        with st.container(border=True):
            row_col1, row_col2, row_col3, row_col4, row_col5, row_col6 = st.columns(
                [0.7, 1.7, 1.5, 1.3, 1.4, 1.5]
            )

            with row_col1:
                if rank_type == "image":
                    st.image(rank_display, width=42)
                else:
                    st.markdown(f"### {rank_display}")

            with row_col2:
                st.markdown(f"**{row['Month']}**")
                st.caption("Monthly Sales Performance")

            with row_col3:
                st.caption("Revenue")
                st.markdown(f"**{format_currency_short(row['Revenue'])}**")

            with row_col4:
                st.caption("Orders")
                st.markdown(f"**{int(row['Orders']):,}**")

            with row_col5:
                st.caption("Avg Order")
                st.markdown(
                    f"**{format_currency_short(row['Avg_Order_Value'])}**"
                )

            with row_col6:
                st.caption("Status")
                st.markdown(f"**{status_color} {status}**")

except Exception as e:
    st.error("❌ Sales Analytics page failed to load.")
    st.exception(e)