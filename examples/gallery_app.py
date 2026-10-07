"""Widget gallery: one page with most Streamlit elements, for eyeballing the theme.

    sas-theme run examples/gallery_app.py

Shows the banner (both variants) and footer, plus every widget type that
picks up theme colors: buttons, inputs, sliders, tabs, alerts, metrics,
dataframes and charts. Uses only numpy/pandas (no network).
"""

import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

from sas_theme import render_banner, render_footer

st.set_page_config(page_title="SAS Theme Gallery", page_icon=":material/palette:", layout="wide")

render_banner(title="SAS Theme Gallery", subtitle="Every common Streamlit element, SAS-themed")

# --- Sidebar ---------------------------------------------------------------
with st.sidebar:
    st.header("Filters")
    region = st.selectbox("Region", ["All", "Americas", "EMEA", "APAC"])
    products = st.multiselect("Products", ["Viya", "Enterprise Miner", "Visual Analytics"],
                              default=["Viya"])
    confidence = st.slider("Confidence level", 0.80, 0.99, 0.95)
    st.toggle("Show advanced options", value=True)
    st.caption("Sidebar uses secondaryBackgroundColor.")

# --- Text & links ----------------------------------------------------------
st.title("Heading 1 (st.title)")
st.header("Heading 2 (st.header)")
st.subheader("Heading 3 (st.subheader)")
st.markdown(
    "Body text with a [link](https://www.sas.com), **bold**, *italic*, `inline code`, "
    ":blue[blue text], :green[green text], :red[red text] and :gray[gray text]."
)
st.caption("A caption, used for secondary text.")

# --- Buttons & inputs --------------------------------------------------------
st.subheader("Buttons & inputs")
c1, c2, c3, c4 = st.columns(4)
c1.button("Primary button", type="primary")
c2.button("Secondary button")
c3.download_button("Download CSV", "a,b\n1,2\n", file_name="example.csv")
c4.link_button("Link button", "https://www.sas.com")

c1, c2, c3 = st.columns(3)
c1.text_input("Text input", placeholder="Type something")
c2.number_input("Number input", value=42)
c3.date_input("Date input", value=dt.date(2026, 1, 15))
c1, c2, c3 = st.columns(3)
c1.radio("Radio", ["Option A", "Option B", "Option C"], horizontal=True)
c2.checkbox("Checkbox", value=True)
c3.select_slider("Select slider", ["Low", "Medium", "High"], value="Medium")
st.text_area("Text area", "Multi-line text input.")

# --- Status ----------------------------------------------------------------
render_banner(title="Status & feedback", variant="grey", logo_path=None)
st.info("Info message.")
st.success("Success message.")
st.warning("Warning message.")
st.error("Error message.")
st.progress(0.65, text="Progress bar at 65%")

# --- Metrics, tabs, expanders ----------------------------------------------
render_banner(title="Data", subtitle="Metrics, tables and charts", variant="grey",
              logo_path=None)
m1, m2, m3 = st.columns(3)
m1.metric("Revenue", "$1.2M", "+8%")
m2.metric("Models deployed", "37", "+5")
m3.metric("Failed jobs", "3", "-2", delta_color="inverse")

rng = np.random.default_rng(7)
df = pd.DataFrame(
    {
        "month": pd.date_range("2026-01-01", periods=12, freq="MS"),
        "Americas": rng.normal(100, 15, 12).cumsum(),
        "EMEA": rng.normal(80, 12, 12).cumsum(),
        "APAC": rng.normal(60, 10, 12).cumsum(),
    }
)

tab1, tab2, tab3 = st.tabs(["Line chart", "Bar chart", "Table"])
with tab1:
    st.line_chart(df, x="month")
with tab2:
    st.bar_chart(df, x="month", stack=False)
with tab3:
    st.dataframe(df.round(1), hide_index=True)

with st.expander("Expander with a form"):
    with st.form("demo_form"):
        st.text_input("Name")
        st.slider("Score", 0, 100, 50)
        st.form_submit_button("Submit")

st.code("proc print data=sashelp.class;\nrun;", language="sas")

render_footer(text="Internal tool - test build", link_url="https://www.sas.com")
