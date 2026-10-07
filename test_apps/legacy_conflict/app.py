"""A small "legacy" internal app that already has its own styling.

Written for sas-theme-kit testing (not from Streamlit's gallery). It shows
the two things the SAS theme can't fix without a code change, and that the
kit should report rather than silently override:

1. Its own .streamlit/config.toml sets theme colors (red/orange). Run
   `sas-theme run app.py` from THIS folder and you should get a warning
   listing those keys, and the app will stay partly red.
2. It injects hand-written CSS that hard-codes colors on buttons/headers.
   No theme can beat that; a person has to decide whether to remove it.
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Legacy Sales Tracker", layout="wide")

# Hand-rolled CSS, typical of older apps. Hard-coded colors win over any theme.
st.markdown(
    """
    <style>
    h1 { color: #B22222 !important; }
    div.stButton > button { background-color: #FF8C00; color: white; border: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Legacy Sales Tracker")

if "orders" not in st.session_state:
    st.session_state.orders = []

with st.form("new_order"):
    customer = st.text_input("Customer")
    amount = st.number_input("Amount ($)", min_value=0.0, step=50.0)
    region = st.selectbox("Region", ["East", "West", "North", "South"])
    if st.form_submit_button("Add order") and customer:
        st.session_state.orders.append(
            {"customer": customer, "amount": amount, "region": region}
        )

df = pd.DataFrame(st.session_state.orders, columns=["customer", "amount", "region"])
c1, c2 = st.columns(2)
c1.metric("Orders", len(df))
c2.metric("Total ($)", f"{df['amount'].sum():,.2f}")

if df.empty:
    st.info("No orders yet. Add one above.")
else:
    st.dataframe(df, hide_index=True)
    st.bar_chart(df.groupby("region")["amount"].sum())

if st.button("Clear all orders"):
    st.session_state.orders = []
    st.rerun()
