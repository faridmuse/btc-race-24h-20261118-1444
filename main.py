"""Dip-buy mean-reversion bot for the make.fun BTC race (agent-fun/bars-replay/v1).

Strategy (long only, one asset CBBTC/USDC, full size, few trades):

  Entry — either of two independent dip signals fires:
    (a) the latest close is at least 110 bps below the 120-bar simple moving
        average of closes (a slow drift-away from the medium-term mean), or
    (b) the 30-bar return is at least -150 bps (a sharp half-hour fall).
    Both are mean-reversion signals: on the two published 24h windows, 30-120
    minute falls of ~100 bps or more revert toward the average within hours,
    while 1-minute closes are mostly noise (per-bar log-return std ~7 bps,
    lag-1 autocorrelation near 0). A full round trip costs ~26 bps in fees,
    slippage and impact, so the thresholds sit far above the noise and the
    cost: only swings of ~140+ bps are traded.

  Exit — a trailing stop plus a hard stop, both read off the position's cost:
    * once the position is worth more than its cost, sell the whole position
      when the close retraces 70 bps or more from the highest close seen
      since entry. Winners are allowed to run past a fixed target; the
      retracement banks them when the bounce fades.
    * hard stop: sell if the position is worth 250 bps or more below its cost.

Why this shape over a plain SMA dip-buy: the same entry with a fixed exit
was tested on the two published 24h windows (this race's dev window and the
previous race's) and the trailing exit beat the fixed exit on both. The
parameters sit in the middle of a wide positive plateau, not on a tuned
spike: trailing 65-75 bps, SMA 110-130, entry 100-120 bps and 30-bar fall
140-160 bps are all profitable on both windows, with 2-3 trades per window.

Determinism: no randomness, no wall clock, no files, no environment reads.
All state is the closes seen so far plus the account the harness reports.
Indicator math is plain float arithmetic in a fixed order, so the same bars
give the same orders on every run.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
SMA_BARS = 120          # slow mean the close must drift away from, in bars
ENTRY_BELOW_BPS = 110   # (a) buy when close is this far below the SMA, in bps
FALL_BARS = 30          # window for the sharp-fall signal, in bars
FALL_BELOW_BPS = 150    # (b) buy when the FALL_BARS return is this far down, in bps
TRAIL_BELOW_BPS = 70    # sell when close retraces this far from the peak since entry, in bps
STOP_BELOW_BPS = 250    # sell when the position is this far under its cost, in bps
MAX_SLIPPAGE_BPS = 100
# No new entries in the last hour of the 1440-bar window: a position opened
# there has no time for the dip to revert before the forced flatten at the
# last close, so on average it only pays the ~26 bps round-trip cost.
NO_BUY_AFTER_SEQ = 1380

closes = []
peak_close = None  # highest close seen since the current position was opened


def _sma():
    """The mean of the last SMA_BARS closes, or None before that many bars."""
    if len(closes) < SMA_BARS:
        return None
    return sum(closes[-SMA_BARS:]) / SMA_BARS


def _fall_bps():
    """The return over the last FALL_BARS bars, in bps, or None before then."""
    if len(closes) <= FALL_BARS:
        return None
    then = closes[-FALL_BARS - 1]
    return (closes[-1] - then) * 10000.0 / then


def on_batch(state, batch):
    global peak_close
    bar = state.latest.get(SYMBOL)
    if bar is None:
        # No bar for CBBTC yet (or on this batch): nothing to decide on.
        return []
    close = int(bar["c"])
    closes.append(close)
    if state.warming_up:
        return []
    held = state.positions.get(SYMBOL)
    if held is None:
        peak_close = None
    if held is not None:
        if peak_close is None or close > peak_close:
            peak_close = close
        value = state.value(SYMBOL, held.qty)
        # Hard stop first: the position has fallen too far under its cost.
        if value * 10000 <= held.cost * (10000 - STOP_BELOW_BPS):
            peak_close = None
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        # Trailing stop: only once the position is above its cost, sell on a
        # retracement from the best close since entry.
        if value > held.cost and peak_close is not None:
            retrace_bps = (peak_close - close) * 10000.0 / peak_close
            if retrace_bps >= TRAIL_BELOW_BPS:
                peak_close = None
                return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []
    sma = _sma()
    if sma is None:
        return []
    dev_bps = (close - sma) * 10000.0 / sma
    fall_bps = _fall_bps()
    dip_vs_mean = dev_bps <= -ENTRY_BELOW_BPS
    sharp_fall = fall_bps is not None and fall_bps <= -FALL_BELOW_BPS
    if (dip_vs_mean or sharp_fall) and state.cash > 0 and state.seq < NO_BUY_AFTER_SEQ:
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
