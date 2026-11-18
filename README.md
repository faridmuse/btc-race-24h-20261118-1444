# btc-race-24h-20261118-1444

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/faridmuse/btc-race-24h-20261118-1444/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/faridmuse/btc-race-24h-20261118-1444/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

Dip-buy mean-reversion bot with a trailing exit for the make.fun competition `btc-race-24h-20261118-1444`: it trades Coinbase Wrapped BTC (cbBTC) against USDC on 1-minute on-chain bars, starting from 1,000 USDC, in the `agent-fun/bars-replay/v1` protocol (`python3 -P -s /bot/main.py`, standard library only).

## Strategy

Long only, full size, few trades. Two independent dip signals can open a position:

- **Slow drift:** the latest close is at least **110 bps below** the 120-bar simple moving average of closes.
- **Sharp fall:** the 30-bar return is at least **−150 bps**.

The position is exited by a **trailing stop**: once it is worth more than its cost, sell the whole position when the close retraces **70 bps** from the highest close since entry — winners run past a fixed target and are banked when the bounce fades. A **hard stop** sells if the position falls **250 bps** below its cost. No new entries are opened in the last hour of the 1440-bar window, since a fresh position has no time to revert before the forced flatten. Orders cap slippage at 100 bps from the latest close.

## Why this shape

On the dev window the 1-minute closes are noise-dominated (per-bar log-return std ~7 bps, lag-1 autocorrelation near 0), while 30–120 minute moves mean-revert. A full round trip costs ~26 bps in fees, slippage and impact, so the entry thresholds (110–150 bps) sit far above both the noise and the cost. The parameters were picked in the middle of a wide positive plateau, not on a tuned spike: trailing 65–75 bps, SMA 110–130, entry 100–120 bps and 30-bar fall 140–160 bps are all profitable on both published 24-hour windows (this race's dev window and the previous race's). Local trial (exact replay of the harness fill math, driving the real bot over the protocol): **+$15.57 net PnL on this race's dev window** and **+$8.93 on the previous race's dev window**, 1 round trip each, maximum drawdown under 90 bps on both. The bot is fully deterministic: no randomness, no wall clock, no files, no environment reads.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=ms3zd0fn&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
