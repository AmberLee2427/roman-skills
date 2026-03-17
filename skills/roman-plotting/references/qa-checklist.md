# QA Checklist

## Data Integrity
- [ ] Column names mapped correctly.
- [ ] Missing values handled explicitly.
- [ ] Error bars represent stated uncertainties.

## Scientific Conventions
- [ ] Magnitude axis inverted when plotting magnitude.
- [ ] Time offset correctly reflected in axis label.
- [ ] Residual panel included for model-fit diagnostics.
- [ ] Units included for all physical quantities.

## Visual Quality
- [ ] Legend readable and does not hide key data.
- [ ] Text size readable at final publication size.
- [ ] Colors remain distinguishable in grayscale/colorblind contexts.

## Export and Reproducibility
- [ ] Vector export created (`pdf` or `svg`).
- [ ] Raster export created (`png`, >=300 dpi).
- [ ] Script invocation and inputs recorded in output metadata/log.
- [ ] TeX preflight passed (or `--no-tex` explicitly documented).
