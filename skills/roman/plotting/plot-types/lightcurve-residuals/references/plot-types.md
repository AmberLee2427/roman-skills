# Plot Types

## 1) Microlensing Lightcurve + Residuals
Required columns:
- `time`
- `flux` or `magnitude`
- `uncertainty`
Optional columns:
- `observatory`
- `model_flux` or `model_magnitude`
- Additional band columns (for multiband overlays), each with explicit y-kind semantics

Expected layout:
- Top panel: data + model curve(s)
- Bottom panel: residuals (`data - model`) with zero reference line
- Optional inset: anomaly zoom window
- Optional multiband normalization to a declared reference band (never mixed physical y-kinds)

## 2) Caustic and Source Trajectory
Required inputs:
- Caustic curve coordinates (`x_caustic`, `y_caustic`)
- Source path (`x_src`, `y_src`)
Optional:
- Time stamps along trajectory
- Finite source radius

Expected layout:
- Equal aspect ratio
- Caustic in high-contrast line color
- Trajectory with direction markers

## 3) Corner/Posterior Diagnostic Plot
Required inputs:
- Posterior samples array
- Parameter names
Optional:
- Truth/reference values

Expected layout:
- 1D histograms on diagonal
- 2D contours off-diagonal
- Units in parameter labels where relevant

## 4) Mass-Distance Inference Plot
Required inputs:
- Lens distance samples or contours
- Lens mass samples or contours
Optional:
- Priors/posteriors overlay
- Independent constraint curves (e.g., AO flux)

Expected layout:
- Distance on x-axis (kpc)
- Mass on y-axis (M_sun)
- Credible intervals clearly annotated
