import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.components.header import page_header
from src.components.metric_card import metric_card


st.set_page_config(
    page_title="Sales Forecasting",
    page_icon="📈",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/styles.css")

page_header(
    "Sales Forecasting",
    "Project future revenue using historical sales trends and moving-average forecasting."
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

    st.subheader("Forecast Filters")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    store_options = ["All Stores"] + sorted(
        sales_df["Store_Name"].dropna().unique().tolist()
    )

    category_options = ["All Categories"] + sorted(
        sales_df["Category"].dropna().unique().tolist()
    )

    forecast_month_options = [3, 6, 12]

    with filter_col1:
        selected_store = st.selectbox("Store", store_options)

    with filter_col2:
        selected_category = st.selectbox("Category", category_options)

    with filter_col3:
        forecast_months = st.selectbox("Forecast Horizon", forecast_month_options)

    filtered_df = sales_df.copy()

    if selected_store != "All Stores":
        filtered_df = filtered_df[filtered_df["Store_Name"] == selected_store]

    if selected_category != "All Categories":
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]

    monthly_revenue = (
        filtered_df.groupby("Month")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    monthly_revenue["Month_Date"] = pd.to_datetime(monthly_revenue["Month"] + "-01")

    monthly_revenue["Moving_Avg"] = (
        monthly_revenue["Revenue"]
        .rolling(window=3, min_periods=1)
        .mean()
    )

    last_month = monthly_revenue["Month_Date"].max()
    last_moving_avg = monthly_revenue["Moving_Avg"].iloc[-1]

    recent_growth = (
        monthly_revenue["Revenue"].pct_change().tail(3).mean()
        if len(monthly_revenue) > 3
        else 0
    )

    if pd.isna(recent_growth):
        recent_growth = 0

    forecast_rows = []

    previous_forecast = last_moving_avg

    for i in range(1, forecast_months + 1):
        forecast_date = last_month + pd.DateOffset(months=i)
        forecast_value = previous_forecast * (1 + recent_growth)

        forecast_rows.append(
            {
                "Month_Date": forecast_date,
                "Month": forecast_date.strftime("%Y-%m"),
                "Forecast_Revenue": forecast_value
            }
        )

        previous_forecast = forecast_value

    forecast_df = pd.DataFrame(forecast_rows)

    next_month_forecast = forecast_df["Forecast_Revenue"].iloc[0]
    total_forecast_revenue = forecast_df["Forecast_Revenue"].sum()
    avg_forecast_revenue = forecast_df["Forecast_Revenue"].mean()
    current_month_revenue = monthly_revenue["Revenue"].iloc[-1]

    forecast_growth = (
        (next_month_forecast - current_month_revenue) / current_month_revenue * 100
        if current_month_revenue else 0
    )

    if forecast_growth >= 0:
        growth_text = f"▲ {forecast_growth:.1f}%"
        growth_color = "#2E8B57"
    else:
        growth_text = f"▼ {abs(forecast_growth):.1f}%"
        growth_color = "#D9534F"

    st.markdown("---")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        metric_card(
            "Next Month Forecast",
            format_currency_short(next_month_forecast),
            "assets/icons/total_revenue.png",
            growth_text,
            growth_color,
        )

    with kpi_col2:
        metric_card(
            "Forecast Horizon",
            f"{forecast_months} Months",
            "assets/icons/calendar.png",
            "",
            "#666666",
        )

    with kpi_col3:
        metric_card(
            "Projected Revenue",
            format_currency_short(total_forecast_revenue),
            "assets/icons/product_revenue.png",
            "",
            "#666666",
        )

    with kpi_col4:
        metric_card(
            "Avg Forecast / Month",
            format_currency_short(avg_forecast_revenue),
            "assets/icons/avg_order_value.png",
            "",
            "#666666",
        )

    st.markdown("---")

    st.subheader("Forecast Summary")

    direction = "increase" if forecast_growth >= 0 else "decline"

    st.markdown(
        f"""
        <div class="summary-card">
            Based on recent monthly sales patterns, the next month is forecasted at
            <strong>{format_currency_short(next_month_forecast)}</strong>, representing a
            <strong>{abs(forecast_growth):.1f}% {direction}</strong> compared to the latest actual month.
            Over the next <strong>{forecast_months}</strong> months, projected revenue is estimated at
            <strong>{format_currency_short(total_forecast_revenue)}</strong>.
            This forecast uses a simple three-month moving average with recent growth adjustment.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.subheader("Revenue Forecast Trend")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_revenue["Month_Date"],
            y=monthly_revenue["Revenue"],
            mode="lines+markers",
            name="Actual Revenue",
            line=dict(color="#C9A24D", width=3),
            marker=dict(size=7),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=monthly_revenue["Month_Date"],
            y=monthly_revenue["Moving_Avg"],
            mode="lines",
            name="3-Month Moving Average",
            line=dict(color="#5E6B4E", width=3, dash="dot"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast_df["Month_Date"],
            y=forecast_df["Forecast_Revenue"],
            mode="lines+markers",
            name="Forecast Revenue",
            line=dict(color="#C47A55", width=3, dash="dash"),
            marker=dict(size=7),
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=520,
        paper_bgcolor="#FFFDF8",
        plot_bgcolor="#FFFDF8",
        xaxis_title="Month",
        yaxis_title="Revenue",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Forecast Table")

    forecast_table = forecast_df.copy()
    forecast_table["Forecast_Revenue"] = forecast_table["Forecast_Revenue"].apply(
        lambda x: f"${x:,.0f}"
    )

    forecast_table = forecast_table[["Month", "Forecast_Revenue"]]

    st.dataframe(
        forecast_table,
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("❌ Sales Forecasting page failed to load.")
    st.exception(e)