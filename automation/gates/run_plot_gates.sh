#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <plot_metadata.json> <profile> <gate_output_dir>" >&2
  exit 2
fi

META="$1"
PROFILE="$2"
OUTDIR="$3"

mkdir -p "$OUTDIR"

python skills/plotting/accessibility-checks/scripts/check_accessibility.py \
  --metadata "$META" \
  --output "$OUTDIR/accessibility.json"

python skills/plotting/style-profiles/scripts/check_style_profile.py \
  --metadata "$META" \
  --profile "$PROFILE" \
  --output "$OUTDIR/style.json"

echo "Saved gate outputs in: $OUTDIR"
