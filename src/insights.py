def get_executive_insights(sales_df):
    best_store = (
        sales_df.groupby("Store_Name")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    best_category = (
        sales_df.groupby("Category")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    best_product = (
        sales_df.groupby("Product_Name")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    return {
        "best_store": best_store.index[0],
        "best_store_revenue": best_store.iloc[0],
        "top_category": best_category.index[0],
        "top_category_revenue": best_category.iloc[0],
        "top_product": best_product.index[0],
        "top_product_revenue": best_product.iloc[0],
        "lowest_store": best_store.index[-1],
        "lowest_store_revenue": best_store.iloc[-1],
    }