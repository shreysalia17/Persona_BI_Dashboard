import pandas as pd
import plotly.express as px

GOLD = "#C9A24D"
OLIVE = "#5E6B4E"
TERRACOTTA = "#C47A55"
SAGE = "#A9B49A"
BEIGE = "#D8C29D"
BROWN = "#7A5C3E"
CREAM = "#FFFDF8"


def apply_chart_style(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=CREAM,
        plot_bgcolor=CREAM,
        font=dict(color="#2F2A24", size=12),
        title=dict(font=dict(size=17, color="#2F2A24")),
        margin=dict(l=25, r=25, t=55, b=25),
    )

    fig.update_xaxes(
        gridcolor="#EFE6D8",
        zeroline=False,
        linecolor="#E2D3BC",
        tickfont=dict(color="#746B60"),
    )

    fig.update_yaxes(
        gridcolor="#EFE6D8",
        zeroline=False,
        linecolor="#E2D3BC",
        tickfont=dict(color="#746B60"),
    )

    return fig


def revenue_trend_chart(sales_df):
    df = sales_df.copy()
    df["Sale_Date"] = pd.to_datetime(df["Sale_Date"])

    monthly = (
        df.groupby(df["Sale_Date"].dt.to_period("M"))["Revenue"]
        .sum()
        .reset_index()
    )
    monthly["Sale_Date"] = monthly["Sale_Date"].astype(str)

    fig = px.line(
        monthly,
        x="Sale_Date",
        y="Revenue",
        title="Monthly Revenue Trend",
        markers=True,
    )

    fig.update_traces(
        line=dict(color=GOLD, width=3),
        marker=dict(size=7, color=GOLD),
    )

    fig.update_layout(
        height=380,
        xaxis_title="Month",
        yaxis_title="Revenue ($)",
        hovermode="x unified",
    )

    return apply_chart_style(fig)


def revenue_by_store_chart(sales_df):
    store_revenue = (
        sales_df.groupby("Store_Name")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Revenue", ascending=True)
    )

    fig = px.bar(
        store_revenue,
        x="Revenue",
        y="Store_Name",
        orientation="h",
        title="Revenue by Store",
    )

    fig.update_traces(marker_color=GOLD)

    fig.update_layout(
        height=380,
        xaxis_title="Revenue ($)",
        yaxis_title="",
    )

    return apply_chart_style(fig)


def revenue_by_category_chart(sales_df):
    category_revenue = (
        sales_df.groupby("Category")["Revenue"]
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
        color_discrete_sequence=[BEIGE, OLIVE, TERRACOTTA, SAGE, GOLD, BROWN],
    )

    fig.update_layout(height=380)

    return apply_chart_style(fig)


def top_products_chart(sales_df):
    product_revenue = (
        sales_df.groupby("Product_Name")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(10)
        .sort_values("Revenue", ascending=True)
    )

    fig = px.bar(
        product_revenue,
        x="Revenue",
        y="Product_Name",
        orientation="h",
        title="Top 10 Products by Revenue",
    )

    fig.update_traces(marker_color=OLIVE)

    fig.update_layout(
        height=380,
        xaxis_title="Revenue ($)",
        yaxis_title="",
    )

    return apply_chart_style(fig)