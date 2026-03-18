# Convergence Diagnostics

## R-hat (Gelman-Rubin)
- Preferred near 1.0.
- Typical warning threshold: `R-hat > 1.01`.

## ESS Proxy
- This implementation emits an ESS proxy derived from chain count, draw count, and R-hat.
- Use as a gate signal, not a full replacement for autocorrelation-aware ESS.

## Data Requirements
- Two or more chains.
- Numeric parameter columns.
- Sufficient draws per chain after alignment.
