# SAS Theme Kit

Gives internal Streamlit apps the SAS look (SAS Blue theme, brand chart
palette, an optional banner and footer with the real SAS logo) **without
changing what the app does**. Includes a checker that proves it.

> **Scope.** This is the SAS *brand* as defined by the approved PowerPoint
> template in `brand-source/` (colors, logo). It makes a Streamlit app look
> SAS-branded; it does not make it look like SAS Viya's own UI. It's for
> Streamlit apps; other frameworks can use `tokens/sas-tokens.css` (see
> Level 3).

## Install

```powershell
# from the shared git repo (pin a tag so brand updates are deliberate)
pip install "sas-theme-kit @ git+https://<your-git-host>/<group>/sas-theme-kit.git@v0.3.0"

# or from a local clone, for development
pip install -e ".[dev]"
```

Requires Streamlit 1.51+ (the first version with reusable theme files).

## Three levels of adoption

### Level 1: theme only, zero code changes

```powershell
sas-theme run app.py            # instead of: streamlit run app.py
sas-theme run app.py --server.port 8502 -- --app-arg   # options pass through
```

This launches Streamlit with `--theme.base=<bundled sas-light.toml>`. The
app's files are not touched. Every built-in widget, the sidebar, links,
borders, and Plotly/Altair/Vega-Lite chart colors pick up the theme.

If the folder you run from has a `.streamlit/config.toml` with its own
`[theme]` colors (or `STREAMLIT_THEME_*` env vars are set), those override
the SAS values. `sas-theme run` lists them as a warning so you can decide.

**Without the CLI** (e.g. a deployment that must call `streamlit run`),
add one line to the app's `.streamlit/config.toml`:

```toml
[theme]
base = 'C:/path/printed/by/sas-theme theme-path/sas-light.toml'
```

Use forward slashes or single quotes on Windows: in a double-quoted TOML
string, backslashes are escape characters. `base` may also be an
`https://` URL, but the Streamlit *server* has to be able to fetch it
without logging in, which internal git hosts often don't allow.

### Level 2: banner and footer (two added lines)

```python
from sas_theme import render_banner, render_footer

st.set_page_config(page_title="My App", layout="wide")
render_banner(title="My App", subtitle="What it does")   # variant="grey" for section dividers
# ... the app, unchanged ...
render_footer(text="Internal tool")
```

Both are purely presentational (HTML via `st.markdown`; no widgets, no
session state) and never raise. Bad inputs are logged and they degrade
gracefully. For `st.navigation` multipage apps, put both calls in the
entry-point file around `page.run()` and every page gets them (see
`test_apps/streamlit_hello/streamlit_app_sas.py`).

### Level 3: non-Streamlit apps

`sas-theme tokens-path` prints the location of `sas-tokens.css`: the same
colors as CSS custom properties (`--sas-primary`, `--sas-navy`, …) for
Dash, Shiny, Gradio or plain HTML templates. Only the colors are shared;
there are no banner/footer components for those frameworks yet.

## Converting an existing app (and proving it's style-only)

1. **Inventory.** Find the entry point(s), any `.streamlit/config.toml`,
   and any hand-written CSS (`st.markdown("<style>…")`). Don't delete or
   recolor existing CSS or hard-coded chart colors as part of the
   conversion. List them for the app owner instead.
2. **Theme.** Start with Level 1. If that's enough, you're done, and
   nothing in the app changed.
3. **Banner/footer** (optional). Add the import, `render_banner()` after
   `set_page_config`, `render_footer()` at the end. Add `sas-theme-kit` to
   `requirements.txt`.
4. **Verify the change is style-only.**
   ```powershell
   sas-theme check --against main         # git: working tree vs. main
   sas-theme check old_app/ new_app/      # or two folders / two files
   ```
   It compares syntax trees with the `sas_theme` import and calls removed,
   so the result must be *identical* to the original. Formatting and
   comments don't matter; anything else fails with a diff. In
   `.streamlit/config.toml` only `[theme]` may change; in
   `requirements*.txt` only a `sas-theme-kit` line may be added.
5. **Look at it.** Run it and click through every page. (The checker
   proves logic didn't change, not that it looks right.)

To enforce this in an app's CI, add one step to its merge-request
pipeline: `pip install sas-theme-kit … && sas-theme check --against origin/main`.

## What's in the repo

```
src/sas_theme/
  themes/sas-light.toml    single source of truth for the Streamlit theme
  tokens/sas-tokens.css    same colors as CSS variables (kept in sync by a test)
  banner.py, footer.py     the two components
  style_check.py, cli.py   `sas-theme check` / `sas-theme run`
  assets/sas-brand/        SAS logos extracted from the template
examples/gallery_app.py    every common widget on one page, for eyeballing
test_apps/                 real Streamlit demo apps + converted copies (see its README)
tests/                     pytest suite (style checker, tokens, CLI, components)
brand-source/              the approved PowerPoint template the colors come from
TESTING.md                 manual test plan
```

## Releasing

1. Update `version` in `pyproject.toml` and add a `CHANGELOG.md` entry.
2. `python -m pytest`, then `git tag v0.X.Y && git push --tags`.
3. Apps upgrade by changing the tag in their `requirements.txt`. If
   someone needs a single file instead, `python -m build` produces a
   `.whl` in `dist/` that includes the theme, tokens and logos.

## Known limitations

- **Hard-coded colors in app code and custom CSS win** over any theme
  (e.g. the red chart in `test_apps/nyc_uber`). Changing those is a code
  change, so `sas-theme check` will flag it. That's intentional: the app
  owner decides.
- **Light theme only.** No SAS dark theme is defined; the footer and
  banner colors are tuned for light backgrounds.
- **Grey banner contrast.** White on Slate is 3.6:1, which only meets WCAG AA
  for large text. The grey banner therefore renders its title and
  subtitle large and bold; don't put small text on Slate.
- **`sas-theme run` and `$CWD`.** Streamlit reads `.streamlit/config.toml`
  from the folder you launch from, not the app's folder. Run from the
  app's project root, as usual.

## Open branding items

- **Font.** The template specifies **Anova**, but no font file ships with
  it, so the theme uses the default sans-serif. Once licensed web-font
  files are available, uncomment the `fontFaces` block in
  `sas-light.toml`.
- **Chart palette order** in `chartCategoricalColors` follows the
  template's slide 5 (SAS Blue first). Confirm with the brand owner if
  charts are customer-facing.
- **Footer disclaimer wording** (e.g. "Internal tool") is still a placeholder.
- **Logo rules.** Minimum size and clear-space rules for the logo aren't
  specified in the template.
