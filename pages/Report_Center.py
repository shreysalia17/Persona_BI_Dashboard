import os
from io import BytesIO
from datetime import datetime

import pandas as pd
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)

from src.google_sheets import load_sheet
from src.calculations import format_currency_short
from src.components.header import page_header


st.set_page_config(
    page_title="Executive Report Center",
    page_icon="📄",
    layout="wide"
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def clean_store_name(name):
    corrections = {
        "Perosna Magnificent Mle": "Persona Magnificent Mile"
    }
    return corrections.get(name, name)


def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6F655B"))

    footer_text = "Persona Intelligence | Confidential Executive Report"
    page_number = f"Page {doc.page}"

    canvas.drawString(42, 24, footer_text)
    canvas.drawRightString(570, 24, page_number)

    canvas.restoreState()


def build_table(data, col_widths=None):
    if col_widths is None:
        col_count = len(data[0])
        total_width = 7.0 * inch
        col_widths = [total_width / col_count] * col_count

    table = Table(data, colWidths=col_widths)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D8C29D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2F2A24")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FFFDF8")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8CBB8")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
    ]))

    return table


def create_pdf_report(report_data):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PersonaTitle",
        parent=styles["Title"],
        fontSize=25,
        leading=32,
        textColor=colors.HexColor("#2F2A24"),
        alignment=1,
        spaceAfter=14,
    )

    subtitle_style = ParagraphStyle(
        "PersonaSubtitle",
        parent=styles["BodyText"],
        fontSize=11,
        leading=17,
        textColor=colors.HexColor("#6F655B"),
        alignment=1,
    )

    heading_style = ParagraphStyle(
        "PersonaHeading",
        parent=styles["Heading2"],
        fontSize=16,
        leading=21,
        textColor=colors.HexColor("#2F2A24"),
        spaceBefore=14,
        spaceAfter=10,
    )

    body_style = ParagraphStyle(
        "PersonaBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#2F2A24"),
    )

    story = []

    # -------------------------
    # COVER PAGE
    # -------------------------

    logo_path = "assets/logo/persona_1.png"

    story.append(Spacer(1, 1.25 * inch))

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=3.2 * inch, height=0.95 * inch)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 36))

    story.append(Paragraph("Executive Business Performance Report", title_style))

    story.append(
        Paragraph(
            "Persona Intelligence | Enterprise Business Intelligence Platform",
            subtitle_style
        )
    )

    story.append(Spacer(1, 18))

    story.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y')}",
            subtitle_style
        )
    )

    story.append(Spacer(1, 115))

    story.append(
        Paragraph(
            "Confidential report prepared for leadership review, business planning, and performance decision-making.",
            subtitle_style
        )
    )

    story.append(PageBreak())

    # -------------------------
    # PAGE 2: SUMMARY
    # -------------------------

    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(report_data["summary"], body_style))
    story.append(Spacer(1, 18))

    story.append(Paragraph("KPI Snapshot", heading_style))

    story.append(build_table([
        ["Metric", "Value"],
        ["Total Revenue", report_data["total_revenue"]],
        ["Total Profit", report_data["total_profit"]],
        ["Total Orders", report_data["total_orders"]],
        ["Unique Customers", report_data["unique_customers"]],
        ["Average Order Value", report_data["avg_order_value"]],
        ["Profit Margin", report_data["profit_margin"]],
    ]))

    story.append(Spacer(1, 18))

    story.append(Paragraph("Business Insights", heading_style))

    for insight in report_data["insights"]:
        story.append(Paragraph(f"• {insight}", body_style))
        story.append(Spacer(1, 5))

    story.append(Spacer(1, 12))

    story.append(Paragraph("Recommended Actions", heading_style))

    for action in report_data["actions"]:
        story.append(Paragraph(f"• {action}", body_style))
        story.append(Spacer(1, 5))

    story.append(PageBreak())

    # -------------------------
    # PAGE 3: SNAPSHOTS
    # -------------------------

    story.append(Paragraph("Store Performance Snapshot", heading_style))
    story.append(build_table(report_data["store_rows"]))
    story.append(Spacer(1, 22))

    story.append(Paragraph("Product Performance Snapshot", heading_style))
    story.append(build_table(report_data["product_rows"]))
    story.append(Spacer(1, 22))

    story.append(Paragraph("Customer Snapshot", heading_style))

    story.append(build_table([
        ["Metric", "Value"],
        ["Unique Customers", report_data["unique_customers"]],
        ["Repeat Customers", report_data["repeat_customers"]],
        ["Repeat Rate", report_data["repeat_rate"]],
        ["Top Customer Spend", report_data["top_customer_spend"]],
    ]))

    story.append(PageBreak())

    # -------------------------
    # PAGE 4: FORECAST + CLOSE
    # -------------------------

    story.append(Paragraph("Forecast Snapshot", heading_style))

    story.append(build_table([
        ["Metric", "Value"],
        ["Next Month Forecast", report_data["next_month_forecast"]],
        ["3-Month Forecast Revenue", report_data["three_month_forecast"]],
        ["Forecast Method", "3-month moving average with recent growth adjustment"],
    ]))

    story.append(Spacer(1, 26))

    story.append(Paragraph("Leadership Note", heading_style))

    story.append(
        Paragraph(
            "This report summarizes executive-level business performance, revenue concentration, store performance, customer value, product performance, and forward-looking sales estimates. It is intended to support leadership review, planning discussions, and strategic decision-making.",
            body_style
        )
    )

    doc.build(
        story,
        onFirstPage=add_footer,
        onLaterPages=add_footer
    )

    buffer.seek(0)
    return buffer


load_css("assets/styles.css")

page_header(
    "Executive Report Center",
    "Generate downloadable executive reports for leadership review and business decision-making."
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

    sales_df["Store_Name"] = sales_df["Store_Name"].apply(clean_store_name)
    sales_df["Sale_Date"] = pd.to_datetime(sales_df["Sale_Date"])
    sales_df["Year"] = sales_df["Sale_Date"].dt.year
    sales_df["Month"] = sales_df["Sale_Date"].dt.to_period("M").astype(str)

    st.subheader("Report Filters")

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
    unique_customers = filtered_df["Customer_ID"].nunique()
    avg_order_value = total_revenue / total_orders if total_orders else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0

    store_perf = (
        filtered_df.groupby("Store_Name")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    category_perf = (
        filtered_df.groupby("Category")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    product_perf = (
        filtered_df.groupby("Product_Name")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    best_store = store_perf.index[0] if not store_perf.empty else "N/A"
    lowest_store = store_perf.index[-1] if not store_perf.empty else "N/A"
    best_category = category_perf.index[0] if not category_perf.empty else "N/A"
    best_product = product_perf.index[0] if not product_perf.empty else "N/A"

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
        repeat_customers / unique_customers * 100
    ) if unique_customers else 0

    top_customer_spend = (
        customer_summary["Revenue"].max()
        if not customer_summary.empty
        else 0
    )

    monthly_revenue = (
        filtered_df.groupby("Month")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    if not monthly_revenue.empty:
        monthly_revenue["Moving_Avg"] = (
            monthly_revenue["Revenue"]
            .rolling(window=3, min_periods=1)
            .mean()
        )

        next_month_forecast = monthly_revenue["Moving_Avg"].iloc[-1]
        three_month_forecast = next_month_forecast * 3
    else:
        next_month_forecast = 0
        three_month_forecast = 0

    summary = (
        f"The selected business view generated {format_currency_short(total_revenue)} "
        f"in revenue and {format_currency_short(total_profit)} in profit across "
        f"{total_orders:,} orders. Profit margin stands at {profit_margin:.1f}%. "
        f"{best_store} is the top-performing store, while {best_category} leads "
        f"category performance. {best_product} is the strongest product by revenue."
    )

    insights = [
        f"{best_store} is the strongest-performing store in the selected view.",
        f"{lowest_store} should be reviewed for improvement opportunities.",
        f"{best_category} is the leading product category.",
        f"{best_product} is the highest revenue-generating product.",
        f"The business served {unique_customers:,} unique customers, with a repeat rate of {repeat_rate:.1f}%.",
    ]

    actions = [
        f"Prioritize inventory and campaign planning around {best_category}.",
        f"Review store strategy, local marketing, and conversion performance for {lowest_store}.",
        f"Monitor demand and replenishment planning for {best_product}.",
        "Create VIP and repeat-customer campaigns to increase customer lifetime value.",
        "Review profitability before expanding promotions or discounts.",
    ]

    store_summary = (
        filtered_df.groupby("Store_Name")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("Sale_ID", "count"),
            Customers=("Customer_ID", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(5)
    )

    store_rows = [["Store", "Revenue", "Orders", "Customers"]]

    for _, row in store_summary.iterrows():
        store_rows.append([
            row["Store_Name"],
            format_currency_short(row["Revenue"]),
            f"{int(row['Orders']):,}",
            f"{int(row['Customers']):,}",
        ])

    product_summary = (
        filtered_df.groupby(["Product_Name", "Category"])
        .agg(
            Revenue=("Revenue", "sum"),
            Cost=("Cost", "sum"),
            Units=("Quantity", "sum")
        )
        .reset_index()
    )

    product_summary["Profit"] = (
        product_summary["Revenue"] - product_summary["Cost"]
    )

    product_summary["Margin"] = (
        product_summary["Profit"] / product_summary["Revenue"] * 100
    )

    product_summary = (
        product_summary.sort_values("Revenue", ascending=False)
        .head(5)
    )

    product_rows = [["Product", "Category", "Revenue", "Units", "Margin"]]

    for _, row in product_summary.iterrows():
        product_rows.append([
            row["Product_Name"],
            row["Category"],
            format_currency_short(row["Revenue"]),
            f"{int(row['Units']):,}",
            f"{row['Margin']:.1f}%",
        ])

    report_data = {
        "summary": summary,
        "total_revenue": format_currency_short(total_revenue),
        "total_profit": format_currency_short(total_profit),
        "total_orders": f"{total_orders:,}",
        "unique_customers": f"{unique_customers:,}",
        "avg_order_value": format_currency_short(avg_order_value),
        "profit_margin": f"{profit_margin:.1f}%",
        "repeat_customers": f"{repeat_customers:,}",
        "repeat_rate": f"{repeat_rate:.1f}%",
        "top_customer_spend": format_currency_short(top_customer_spend),
        "next_month_forecast": format_currency_short(next_month_forecast),
        "three_month_forecast": format_currency_short(three_month_forecast),
        "insights": insights,
        "actions": actions,
        "store_rows": store_rows,
        "product_rows": product_rows,
    }

    st.markdown("---")
    st.subheader("Report Preview")

    st.markdown(
        f"""
        <div class="summary-card">
            <strong>Executive Summary:</strong><br><br>
            {summary}
        </div>
        """,
        unsafe_allow_html=True
    )

    pdf_file = create_pdf_report(report_data)

    st.download_button(
        label="📄 Download Executive PDF Report",
        data=pdf_file,
        file_name="persona_executive_report.pdf",
        mime="application/pdf",
    )

except Exception as e:
    st.error("❌ Report Center failed to load.")
    st.exception(e)