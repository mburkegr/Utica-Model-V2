def run_simple_model(oil_price, gas_price, wells):
    revenue_per_well = oil_price * 1000 + gas_price * 5000
    total_revenue = revenue_per_well * wells

    return {
        "revenue_per_well": revenue_per_well,
        "total_revenue": total_revenue
    }
