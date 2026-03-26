import pandas as pd
import numpy as np
from datetime import timedelta

try:
    import pyxirr
except:
    pyxirr = None


# -----------------------------
# Load Type Curve Library
# -----------------------------
def load_type_curve_library(file_path="type_curve_library.xlsx"):
    tc_monthly = pd.read_excel(file_path, sheet_name="tc_monthly")
    tc_metadata = pd.read_excel(file_path, sheet_name="tc_metadata")
    return tc_monthly, tc_metadata


# -----------------------------
# Get Type Curve
# -----------------------------
def get_type_curve(tc_name, tc_monthly, tc_metadata):
    tc = tc_monthly[tc_monthly["tc_name"] == tc_name].copy()

    base_length = tc_metadata.loc[
        tc_metadata["tc_name"] == tc_name, "base_lateral"
    ].values[0]

    return tc, base_length


# -----------------------------
# Build Production Timeline
# -----------------------------
def build_production(tc, lateral_length, base_length, start_date):
    scale_factor = lateral_length / base_length

    tc = tc.copy()
    tc["oil"] = tc["oil"] * scale_factor
    tc["gas"] = tc["gas"] * scale_factor

    tc["date"] = tc["month"].apply(
        lambda x: start_date + pd.DateOffset(months=int(x - 1))
    )

    return tc


# -----------------------------
# NGL Calculations (improved)
# -----------------------------
def calc_ngl(gas_series, ngl_yield, shrink=0.85):
    gas_sales = gas_series * shrink
    ngl_bbls = gas_series * ngl_yield / 6
    return gas_sales, ngl_bbls


# -----------------------------
# Revenue
# -----------------------------
def calc_revenue(df, oil_price, gas_price, ngl_price=25):
    df = df.copy()

    df["oil_rev"] = df["oil"] * oil_price
    df["gas_rev"] = df["gas_sales"] * gas_price
    df["ngl_rev"] = df["ngl"] * ngl_price

    df["total_revenue"] = df["oil_rev"] + df["gas_rev"] + df["ngl_rev"]

    return df


# -----------------------------
# Costs
# -----------------------------
def calc_costs(df, loe_per_month=5000, tax_rate=0.07):
    df = df.copy()

    df["loe"] = loe_per_month
    df["tax"] = df["total_revenue"] * tax_rate

    df["total_cost"] = df["loe"] + df["tax"]

    return df


# -----------------------------
# Slot Cash Flow
# -----------------------------
def build_slot_cashflow(
    row,
    tc_monthly,
    tc_metadata,
    deal_inputs,
):
    tc_name = row["tc_name"]
    lateral_length = row["lateral_length"]

    tc, base_length = get_type_curve(tc_name, tc_monthly, tc_metadata)

    # timing assumptions (can expose later)
    spud_date = pd.to_datetime("2027-01-01")
    flowback_delay = 4

    start_date = spud_date + pd.DateOffset(months=flowback_delay)

    prod = build_production(tc, lateral_length, base_length, start_date)

    # NGL + shrink
    gas_sales, ngl = calc_ngl(prod["gas"], ngl_yield=5.2, shrink=0.85)
    prod["gas_sales"] = gas_sales
    prod["ngl"] = ngl

    # revenue
    prod = calc_revenue(
        prod,
        oil_price=deal_inputs["oil_price"],
        gas_price=deal_inputs["gas_price"],
    )

    # costs
    prod = calc_costs(prod)

    # net revenue interest
    nri = row["net_revenue_interest"]
    prod["net_cash_flow"] = (prod["total_revenue"] - prod["total_cost"]) * nri

    # capex + acquisition
    acquisition = row["net_acres"] * row["bid_per_acre"]
    capex = row["gross_wells"] * row["lateral_length"] * row["dc_cost_per_ft"]

    first_date = prod["date"].min()
    prod.loc[prod["date"] == first_date, "net_cash_flow"] -= (acquisition + capex)

    prod["slot_id"] = row["slot_id"]

    return prod


# -----------------------------
# Build All Slots
# -----------------------------
def build_all_slots(slot_df, tc_monthly, tc_metadata, deal_inputs):
    all_slots = []

    for _, row in slot_df.iterrows():
        slot_cf = build_slot_cashflow(row, tc_monthly, tc_metadata, deal_inputs)
        all_slots.append(slot_cf)

    return pd.concat(all_slots).reset_index(drop=True)


# -----------------------------
# Roll Up Deal
# -----------------------------
def roll_up_deal(all_slots_df):
    deal_df = (
        all_slots_df.groupby("date")
        .sum(numeric_only=True)
        .reset_index()
    )
    return deal_df


# -----------------------------
# IRR
# -----------------------------
def calc_irr(df):
    if pyxirr is None:
        return None

    try:
        return pyxirr.xirr(df["date"], df["net_cash_flow"])
    except:
        return None


# -----------------------------
# MOIC
# -----------------------------
def calc_moic(df):
    invested = abs(df["net_cash_flow"][df["net_cash_flow"] < 0].sum())
    returned = df["net_cash_flow"][df["net_cash_flow"] > 0].sum()

    if invested == 0:
        return None

    return returned / invested


# -----------------------------
# Run Deal Model
# -----------------------------
def run_deal_model(slot_df, deal_inputs):
    tc_monthly, tc_metadata = load_type_curve_library()

    all_slots_df = build_all_slots(slot_df, tc_monthly, tc_metadata, deal_inputs)

    deal_df = roll_up_deal(all_slots_df)

    irr = calc_irr(deal_df)
    moic = calc_moic(deal_df)

    return all_slots_df, deal_df, irr, moic
