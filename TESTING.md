# Manual test plan

About 20 minutes. Commands are PowerShell, run from the repo root unless
noted. The automated tests cover the checker, CLI and HTML output; this
plan covers what only a person looking at a browser can confirm.

## 0. Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,demos]"
python -m pytest -q
```

Expect everything to pass. Two Uber tests are skipped unless you set
`$env:SAS_THEME_NETWORK_TESTS=1` (they download data).

## 1. Widget gallery: does the theme look right?

```powershell
sas-theme run examples/gallery_app.py
```

Check:
- [ ] Primary button, slider, toggle, checkbox, radio, tabs underline and progress bar are SAS Blue `#0766D1`, not Streamlit red.
- [ ] Sidebar and input backgrounds are pale grey `#F0F1F4`.
- [ ] The link in the body text is SAS Blue.
- [ ] Line/bar chart series use SAS Blue, then teal, then purple (the `chartCategoricalColors` palette).
- [ ] The blue banner shows a white SAS logo; the two grey section banners have no logo and large bold text.
- [ ] The banner title has no hover "link" icon next to it.
- [ ] The footer has a blue SAS logo (it links to sas.com) and readable grey text.
- [ ] Resize the window narrow: the banner wraps cleanly.

## 2. Zero-touch theme on an unmodified app

Run the same original app both ways and compare:

```powershell
streamlit run test_apps/streamlit_hello/streamlit_app.py      # stock look
sas-theme run test_apps/streamlit_hello/streamlit_app.py      # SAS look, same file
```

- [ ] Every page (Hello, DataFrame, Plotting, Mapping, Animation) is SAS-themed.
- [ ] Everything behaves the same: multiselect filters the table, the sliders change the fractal, "Rerun" works.

## 3. Banner + footer on a multipage app

```powershell
sas-theme run test_apps/streamlit_hello/streamlit_app_sas.py
sas-theme check test_apps/streamlit_hello/streamlit_app.py test_apps/streamlit_hello/streamlit_app_sas.py
```

- [ ] Banner appears at the top of **every** page; footer at the bottom.
- [ ] No "set_page_config" warning or error when switching pages (the pages call it *after* the banner, which Streamlit 1.51 allows).
- [ ] On Plotting/Animation, the footer appears once the animation finishes (expected; the page runs top to bottom).
- [ ] `check` prints PASS.

## 4. Logic preserved on a stateful app

```powershell
sas-theme run test_apps/nyc_uber/streamlit_app_sas.py
```

- [ ] Move the hour slider: maps and histogram update, and the URL gets `?pickup_hour=N`.
- [ ] Open the app with `?pickup_hour=5` in the URL: the slider starts at 5 (session state + query params untouched).
- [ ] The histogram at the bottom is still **red**. That's expected: it's hard-coded in the app, and the conversion must not change it.
- [ ] The maps may show no basemap (they use a Mapbox style); same in the original. Not a theme issue.

## 5. The checker catches bad conversions

```powershell
cd test_apps/nyc_uber
sas-theme check streamlit_app.py streamlit_app_sas.py              # PASS, exit 0
sas-theme check streamlit_app.py streamlit_app_bad_conversion.py   # FAIL, exit 1
$LASTEXITCODE
cd ../..
```

- [ ] The FAIL output shows a diff with both `nrows=50000` and `color='#0766D1'`.

Also try git mode on a scratch copy of an app: commit it, convert it,
run `sas-theme check --against HEAD`, then add a stray `.py` file and run
it again (should FAIL on the new file).

## 6. An app that fights the theme

```powershell
cd test_apps/legacy_conflict
sas-theme run app.py
cd ../..
```

- [ ] The terminal shows a WARNING listing `theme.primaryColor` and `theme.secondaryBackgroundColor` from the app's own config.
- [ ] The app is partly orange: its config and hand-written CSS win. That's the point: the kit reports conflicts and leaves the decision to the app owner.
- [ ] Adding orders, the metrics, and "Clear all orders" still work.

## 7. The no-CLI path (for deployments that must call `streamlit run`)

```powershell
sas-theme theme-path      # copy this path
```

Create `test_apps/nyc_uber/.streamlit/config.toml` with the path, using
forward slashes:

```toml
[theme]
base = 'C:/.../sas_theme/themes/sas-light.toml'
```

```powershell
cd test_apps/nyc_uber
streamlit run streamlit_app.py
cd ../..
```

- [ ] SAS theme applies with plain `streamlit run`. Delete that config file afterwards.

## Things I couldn't verify (no Streamlit in my build environment)

These are the assumptions most likely to need a tweak. If one fails,
note the Streamlit version (`streamlit version`) and the error.

1. `streamlit run --theme.base=<local file path>` is accepted on the
   command line (the documented `theme.base` file support is shown for
   `config.toml`; CLI flags normally accept every config option). If it
   isn't, step 7's config-file route still works, and `cli.py` would need
   to switch to an env var or a temp config.
2. A theme file that itself says `base = "light"` is accepted as a base.
3. `chartCategoricalColors` also recolors `st.line_chart` / `st.bar_chart`
   (documented for Plotly/Altair/Vega-Lite, which those use internally).
4. The exact visual spacing of the banner and footer (I reviewed the
   CSS but couldn't render it).
