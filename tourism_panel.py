"""Retrieve tourism candidates using the validated World Bank collector.

Names in the reference are hypotheses until checked against historical values.
"""
from pathlib import Path
from worldbank_panel import run
SERIES = ('ST.INT.ARVL', 'ST.INT.RCPT.XP.ZS', 'ST.INT.XPND.MP.ZS')
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', type=Path, required=True)
    run(p.parse_args().folder, series=SERIES)
