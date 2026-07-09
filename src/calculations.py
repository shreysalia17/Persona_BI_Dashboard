import pandas as pd


def calculate_kpis(sales_df):
    total_revenue = sales_df["Revenue"].sum()
    total_cost = sales_df["Cost"].sum()
    total_profit = total_revenue - total_cost
    total_orders = len(sales_df)
    average_order_value = total_revenue / total_orders if total_orders else 0
    profit_margin = (total_profit / total_revenue) * 100 if total_revenue else 0
    unique_customers = sales_df["Customer_ID"].nunique()

    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "average_order_value": average_order_value,
        "profit_margin": profit_margin,
        "unique_customers": unique_customers,
    }


def filter_sales_data(
    sales_df,
    selected_store,
    selected_category,
    selected_year,
    selected_quarter,
):
    filtered_df = sales_df.copy()

    filtered_df["Sale_Date"] = pd.to_datetime(filtered_df["Sale_Date"])

    if selected_store != "All Stores":
        filtered_df = filtered_df[
            filtered_df["Store_Name"] == selected_store
        ]

    if selected_category != "All Categories":
        filtered_df = filtered_df[
            filtered_df["Category"] == selected_category
        ]

    if selected_year != "All Years":
        filtered_df = filtered_df[
            filtered_df["Sale_Date"].dt.year == selected_year
        ]

    if selected_quarter != "All Quarters":
        filtered_df = filtered_df[
            filtered_df["Sale_Date"].dt.quarter == int(selected_quarter[-1])
        ]

    return filtered_df


def format_currency_short(value):
    value = float(value)

    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.1f}K"
    else:
        return f"${value:,.0f}"


def calculate_kpi_change(current, previous):
    if previous == 0:
        return "0.0%", "#666666"

    change = ((current - previous) / previous) * 100

    if change >= 0:
        return f"▲ {change:.1f}%", "#2E8B57"
    else:
        return f"▼ {abs(change):.1f}%", "#D9534F"


def get_current_previous_month_kpis(sales_df):
    df = sales_df.copy()
    df["Sale_Date"] = pd.to_datetime(df["Sale_Date"])

    latest_month = df["Sale_Date"].dt.to_period("M").max()
    previous_month = latest_month - 1

    current_df = df[df["Sale_Date"].dt.to_period("M") == latest_month]
    previous_df = df[df["Sale_Date"].dt.to_period("M") == previous_month]

    current_kpis = calculate_kpis(current_df)
    previous_kpis = calculate_kpis(previous_df)

    return current_kpis, previous_kpis