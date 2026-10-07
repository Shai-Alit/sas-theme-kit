# Test apps

Real apps to try the kit on. Two come from Streamlit's own open-source
demos (Apache 2.0, license headers kept in each file); one I wrote to
cover the messy cases.

| Folder | Source | What it tests |
|---|---|---|
| `streamlit_hello/` | Streamlit's built-in `streamlit hello` demo ([source](https://github.com/streamlit/streamlit/tree/develop/lib/streamlit/hello)) | Multipage app (`st.navigation`), sidebar widgets, dataframe, Altair, line chart, pydeck map, animation |
| `nyc_uber/` | [streamlit/demo-uber-nyc-pickups](https://github.com/streamlit/demo-uber-nyc-pickups) | Wide layout, columns, session state + URL query params, pydeck maps, an Altair chart with a **hard-coded red** color |
| `legacy_conflict/` | Written for this kit | An app with its **own theme** in `.streamlit/config.toml` and **hand-written CSS**, which are the cases the kit must report, not silently override |

Files ending in `_sas.py` are converted copies: the original plus a banner
and a footer, nothing else. `nyc_uber/streamlit_app_bad_conversion.py` is
a deliberately bad conversion (it recolors the chart and changes how much
data loads) so you can see `sas-theme check` catch it.

The upstream files are unmodified copies. The Hello pages import
`streamlit.hello.utils`, which ships inside Streamlit, so nothing else is
needed. Both upstream apps download demo data from the internet when they
start.

See [../TESTING.md](../TESTING.md) for the step-by-step test plan.
