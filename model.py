def run_deal_model(deal_inputs):
    oil_price = deal_inputs["oil_price"]
    gas_price = deal_inputs["gas_price"]
    gross_wells = deal_inputs["gross_wells"]
    net_acres = deal_inputs["net_acres"]
    bid_per_acre = deal_inputs["bid_per_acre"]
    lateral_length = deal_inputs["lateral_length"]
    dc_cost_per_ft = deal_inputs["dc_cost_per_ft"]
    unit_acres = deal_inputs["unit_acres"]
    pct_unitized = deal_inputs["pct_unitized"]
    nri = deal_inputs["net_revenue_interest"]
    flowback_delay = deal_inputs["flowback_delay"]
    acq_cost_override = deal_inputs["acq_cost_override"]

    working_interest = (net_acres / unit_acres) * pct_unitized if unit_acres != 0 else 0
    net_wells_calc = gross_wells * working_interest

    revenue_per_well = (oil_price * 1000 + gas_price * 5000) * (lateral_length / 10000)
    gross_revenue = revenue_per_well * gross_wells
    net_revenue = gross_revenue * nri

    acquisition_cost = (
        acq_cost_override
        if acq_cost_override is not None
        else net_acres * bid_per_acre
    )

    gross_capex = gross_wells * lateral_length * dc_cost_per_ft

    return {
        "working_interest": working_interest,
        "net_wells_calc": net_wells_calc,
        "revenue_per_well": revenue_per_well,
        "gross_revenue": gross_revenue,
        "net_revenue": net_revenue,
        "acquisition_cost": acquisition_cost,
        "gross_capex": gross_capex,
        "flowback_delay": flowback_delay,
    }
