import streamlit as st

st.set_page_config(page_title="Utica Deal Model", layout="wide")

st.title("Utica Deal Model")

st.header("Basic Test Model")

# -----------------------------
# Inputs
# -----------------------------
st.subheader("Inputs")

oil_price = st.number_input("Oil Price ($/bbl)", value=70.0)
gas_price = st.number_input("Gas Price ($/mcf)", value=3.75)
wells = st.number_input("Number of Wells", value=2.0)

# -----------------------------
# Simple Calculation (placeholder)
# -----------------------------
revenue = oil_price * 1000 + gas_price * 5000
total_revenue = revenue * wells

# -----------------------------
# Outputs
# -----------------------------
st.subheader("Outputs")

st.metric("Total Revenue", f"${total_revenue:,.0f}")
