# Changelog

## 0.3.0

Restructured as a git repo; fixes from the 0.2.0 review.

**New**
- `sas-theme run app.py`: applies the theme with zero code changes, using
  Streamlit 1.51's reusable theme files (`theme.base` = path/URL). Warns
  when the app's own config or env vars override SAS colors.
- `sas-theme check`: proves a conversion is style-only (syntax-tree
  comparison with kit calls removed; works on two files, two folders, or
  a git ref). Exits non-zero on logic changes, so it can gate CI.
- Theme now lives in one bundled file (`themes/sas-light.toml`) instead of
  being copied into every app. Added `linkColor`, `borderColor`, and the
  template's palette as `chartCategoricalColors`.
- `tokens/sas-tokens.css` for non-Streamlit apps, kept in sync with the
  TOML by a test.
- `examples/gallery_app.py` and three real test apps in `test_apps/`.

**Fixed**
- The theme (`config.toml`), example app, and `assets/README.md`
  referenced by the docs were missing from the 0.2.0 wheel/sdist; the
  sdist's own test suite failed as a result. The wheel now contains the
  theme, tokens and logos, and CI checks that it does.
- `sas_theme.__version__` reported `0.1.0`; it now reads the installed
  package version.
- Accessibility: footer text was ~3.3:1 contrast (now 6.2:1); banner
  subtitle used 85% opacity (now full white); grey-banner subtitle is now
  large/bold so white-on-Slate meets the AA large-text threshold.
- `render_banner(variant=…)` with an unknown value raised `ValueError`
  despite the docs saying it never raises; it now logs and falls back to
  blue.
- Footer `link_url` now only accepts `http(s)://` and `mailto:`.
- Logo is encoded once and cached instead of on every rerun.
- Banner title is no longer a raw `<h1>` (now `role="heading"`), so
  Streamlit's own heading styles and anchor links can't apply to it.
- Docs: removed the outdated claim that `config.toml` can't load custom
  fonts (Streamlit supports `[[theme.fontFaces]]`).

**Changed**
- Minimum Streamlit is now 1.51 (was 1.28).
- `src/` layout; `import sas_theme` no longer imports Streamlit (the
  checker runs in bare CI images).
