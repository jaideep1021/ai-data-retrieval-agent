#!/bin/zsh
# Launch an explicitly selected local review pack; no private run is bundled.
cd -- "$(dirname -- "$0")" || exit 1
if [[ $# -lt 2 ]]; then
  print 'Usage: zsh "Start Aviation Review.command" runs/PACK/review-pack.json runs/PACK/human-labels.csv'
  exit 1
fi
python aviation_review_server.py --pack "$1" --labels "$2" --port 8765 --open-browser
