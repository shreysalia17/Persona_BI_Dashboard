def generate_executive_summary(
    revenue_change,
    profit_change,
    margin_change,
    insights
):
    return (
        f"Revenue is currently {revenue_change} compared to the previous month, "
        f"while profit is {profit_change}. "
        f"The top-performing store is {insights['best_store']}, "
        f"and {insights['top_category']} is the leading category. "
        f"Profit margin is {margin_change}, helping leadership understand whether growth is efficient."
    )