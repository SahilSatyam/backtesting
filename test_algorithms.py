"""
Tests for the core backtesting algorithms: metrics, engine simulation,
and strategies (MA crossover, RSI, Bollinger Bands).

Runs with plain python (no pytest required):
    python test_algorithms.py
"""
import sys
import numpy as np
import pandas as pd

from backtesting.engine import BacktestEngine
from backtesting.metrics import metrics_calculator
from strategies.base_strategy import BaseStrategy
from strategies.moving_average_crossover import MovingAverageCrossover
from strategies.rsi_strategy import RSIMeanReversion
from strategies.bollinger_bands import BollingerBands


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ohlcv(closes, opens=None, highs=None, lows=None, start='2023-01-02'):
    """Build a deterministic OHLCV DataFrame from a sequence of closes."""
    closes = np.asarray(closes, dtype=float)
    opens = closes.copy() if opens is None else np.asarray(opens, dtype=float)
    if highs is None:
        highs = np.maximum(opens, closes) * 1.001
    if lows is None:
        lows = np.minimum(opens, closes) * 0.999
    idx = pd.bdate_range(start, periods=len(closes))
    return pd.DataFrame({
        'open': opens,
        'high': np.asarray(highs, dtype=float),
        'low': np.asarray(lows, dtype=float),
        'close': closes,
        'volume': np.full(len(closes), 100_000.0),
    }, index=idx)


def random_walk(n=600, seed=42, drift=0.0004, vol=0.015, start_price=500.0):
    """Synthetic trending price series."""
    rng = np.random.default_rng(seed)
    closes = start_price * np.exp(np.cumsum(rng.normal(drift, vol, n)))
    return make_ohlcv(closes)


def make_equity(values, start='2023-01-02', freq='B'):
    idx = pd.date_range(start, periods=len(values), freq=freq)
    return pd.Series(values, index=idx, dtype=float)


class ScriptedStrategy(BaseStrategy):
    """Strategy that returns a predefined signal column (for engine tests)."""

    def __init__(self, signals: pd.Series):
        super().__init__(name="Scripted Strategy")
        self._signals = signals

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = self._signals.reindex(data.index).fillna(0).astype(int)
        self.signals = signals
        return signals


def scripted_run(data, signal_at, **engine_kwargs):
    """Run the engine on data with a buy signal at one bar index."""
    sig = pd.Series(0, index=data.index)
    sig.iloc[signal_at] = 1
    engine = BacktestEngine()
    return engine.run_backtest('TEST', ScriptedStrategy(sig), data=data, **engine_kwargs)


# ---------------------------------------------------------------------------
# Metrics tests
# ---------------------------------------------------------------------------

def test_metrics_ratios():
    # Steady growth vs volatile path to a similar final value
    n = 500
    steady = make_equity(100 * np.cumprod(np.full(n, 1.001)))
    rng = np.random.default_rng(7)
    volatile = make_equity(100 * np.cumprod(1 + 0.001 + rng.normal(0, 0.02, n)))

    m_steady = metrics_calculator.calculate_all_metrics(steady)
    m_volatile = metrics_calculator.calculate_all_metrics(volatile)

    # Sharpe: steady path must beat the noisy one
    assert m_steady['sharpe_ratio'] > m_volatile['sharpe_ratio'], "Sharpe ordering failed"
    assert np.isfinite(m_steady['sharpe_ratio'])

    # A strictly rising curve has no losses -> Omega is infinite
    assert np.isinf(m_steady['omega_ratio']), "Omega should be inf for an always-gaining curve"
    assert m_volatile['omega_ratio'] > 0

    # Sortino downside deviation must use the full-sample downside formula
    daily = volatile.pct_change().dropna()
    excess = daily - metrics_calculator.risk_free_rate / 252
    expected_dd = np.sqrt(np.mean(np.minimum(excess, 0) ** 2))
    assert np.isclose(m_volatile['downside_deviation'], expected_dd), "Downside deviation formula mismatch"
    expected_sortino = excess.mean() / expected_dd * np.sqrt(252)
    assert np.isclose(m_volatile['sortino_ratio'], expected_sortino), "Sortino formula mismatch"

    # Drawdown sanity on a curve that halves
    crash = make_equity([100, 110, 120, 60, 65, 70])
    m_crash = metrics_calculator.calculate_all_metrics(crash)
    assert np.isclose(m_crash['max_drawdown'], (60 - 120) / 120)

    # Report renders the new metric
    report = metrics_calculator.generate_report(m_steady)
    assert 'Omega Ratio' in report
    print("  metrics: sharpe/sortino/omega/drawdown OK")


def test_metrics_empty():
    assert metrics_calculator.calculate_all_metrics(pd.Series(dtype=float)) == {}
    print("  metrics: empty input handled")


# ---------------------------------------------------------------------------
# Engine tests
# ---------------------------------------------------------------------------

def test_engine_position_sizing_never_negative():
    # Price just below the affordable limit: the old sizing logic bought 1 share
    # and pushed capital negative once fees were applied.
    data = make_ohlcv([999_900.0] * 10)
    result = scripted_run(data, signal_at=2)

    equity = result['equity_curve']
    assert (equity >= 0).all(), "Equity went negative"

    trades = result['trades']
    if not trades.empty:
        cost = trades.iloc[0]['shares'] * trades.iloc[0]['entry_price'] * (1 + 0.001 + 0.0005)
        assert cost <= result['initial_capital'], "Position cost exceeded available capital"
    print("  engine: position sizing stays within capital")


def test_engine_stop_loss():
    # Buy at 100, then a gap down through the 5% stop: fill at the (worse) open
    closes = [100.0] * 5 + [90.0, 88.0, 87.0, 86.0, 85.0]
    data = make_ohlcv(closes)
    result = scripted_run(data, signal_at=4, stop_loss_pct=0.05)

    trades = result['trades']
    assert len(trades) == 1
    trade = trades.iloc[0]
    assert trade['exit_reason'] == 'stop_loss'
    assert trade['exit_price'] == 90.0, "Gap-down stop should fill at the open"
    assert (result['equity_curve'] >= 0).all()
    print("  engine: stop-loss exit with gap-aware fill")


def test_engine_take_profit():
    closes = [100.0] * 5 + [104.0, 108.0]
    highs = [100.5] * 5 + [106.0, 112.0]
    data = make_ohlcv(closes, highs=highs)
    result = scripted_run(data, signal_at=4, take_profit_pct=0.05)

    trades = result['trades']
    assert len(trades) == 1
    trade = trades.iloc[0]
    assert trade['exit_reason'] == 'take_profit'
    assert trade['exit_price'] == 105.0, "Take-profit should fill at the 5% target"
    print("  engine: take-profit exit")


def test_engine_end_of_data_close():
    closes = [100.0] * 5 + [102.0, 103.0, 104.0, 105.0]
    data = make_ohlcv(closes)
    result = scripted_run(data, signal_at=4)

    trades = result['trades']
    assert len(trades) == 1
    assert trades.iloc[0]['exit_reason'] == 'end_of_data'
    assert trades.iloc[0]['exit_price'] == 105.0
    print("  engine: open position closed at end of data")


def test_engine_report():
    data = random_walk()
    engine = BacktestEngine()
    result = engine.run_backtest('TEST', MovingAverageCrossover(10, 40), data=data)
    report = engine.generate_report(result)
    assert 'BACKTESTING REPORT' in report and 'Sharpe Ratio' in report
    print("  engine: report generates with new metrics")


# ---------------------------------------------------------------------------
# Strategy tests
# ---------------------------------------------------------------------------

def test_ma_crossover():
    uptrend = random_walk(n=600, seed=3, drift=0.001, vol=0.01)

    for ma_type in ('sma', 'ema'):
        strategy = MovingAverageCrossover(10, 50, ma_type=ma_type)
        signals = strategy.generate_signals(uptrend)
        assert not signals.empty
        assert (signals['signal'] == 1).sum() >= 1, f"No buy signals for {ma_type}"
        assert set(signals['signal'].unique()) <= {-1, 0, 1}
        assert signals['signal'].isna().sum() == 0

    # EMA reacts faster than SMA -> earlier first crossover
    sma = MovingAverageCrossover(10, 50, 'sma').generate_signals(uptrend)
    ema = MovingAverageCrossover(10, 50, 'ema').generate_signals(uptrend)
    assert ema[ema['signal'] == 1].index[0] <= sma[sma['signal'] == 1].index[0]

    # Parameter validation
    for bad in [dict(short_window=50, long_window=10), dict(ma_type='kama')]:
        try:
            MovingAverageCrossover(**bad)
            raise AssertionError(f"Expected ValueError for {bad}")
        except ValueError:
            pass
    print("  ma crossover: SMA/EMA signals and validation OK")


def test_ma_optimizer_uses_real_performance():
    data = random_walk(n=500, seed=11, drift=0.0006, vol=0.012)
    result = MovingAverageCrossover(10, 50).optimize_parameters(
        data, short_range=(5, 25, 5), long_range=(20, 80, 10))

    assert result['best_parameters'] is not None
    assert result['best_parameters']['short_window'] < result['best_parameters']['long_window']
    assert result['all_results'], "No optimization results"

    best = max(r['sharpe_ratio'] for r in result['all_results'])
    assert np.isclose(result['best_metric'], best), "best_metric is not the best Sharpe"
    for r in result['all_results']:
        assert 'total_return' in r and 'max_drawdown' in r and 'final_capital' in r
    print(f"  ma crossover: optimizer found {result['best_parameters']} "
          f"(Sharpe {result['best_metric']:.3f})")


def test_rsi_strategy():
    # Oscillating series guarantees oversold/overbought crossings
    n = 400
    t = np.arange(n)
    closes = 100 + 15 * np.sin(2 * np.pi * t / 40) + 0.01 * t
    data = make_ohlcv(closes)

    strategy = RSIMeanReversion(period=14, oversold=30, overbought=70)
    signals = strategy.generate_signals(data)
    assert not signals.empty
    assert (signals['signal'] == 1).sum() >= 1
    assert (signals['signal'] == -1).sum() >= 1

    rsi = signals['rsi'].dropna()
    assert ((rsi >= 0) & (rsi <= 100)).all(), "RSI outside [0, 100]"

    summary = strategy.get_strategy_summary()
    assert summary['buy_signals'] >= 1 and 'avg_buy_rsi' in summary

    for bad in [dict(oversold=70, overbought=30), dict(period=1)]:
        try:
            RSIMeanReversion(**bad)
            raise AssertionError(f"Expected ValueError for {bad}")
        except ValueError:
            pass
    print("  rsi: signals, bounds and validation OK")


def test_bollinger_strategy():
    data = random_walk(n=500, seed=13, drift=0.0002, vol=0.02)

    strategy = BollingerBands(window=20, num_std=2.0)
    signals = strategy.generate_signals(data)
    assert not signals.empty
    assert (signals['signal'] == 1).sum() >= 1
    assert (signals['signal'] == -1).sum() >= 1

    # Bands ordered correctly wherever defined
    valid = signals.dropna(subset=['bb_upper'])
    assert (valid['bb_upper'] >= valid['bb_middle']).all()
    assert (valid['bb_middle'] >= valid['bb_lower']).all()

    # Buy signals fire on a close at/under the lower band
    buys = signals[signals['signal'] == 1]
    assert (buys['close'] >= buys['bb_lower'] - 1e-9).all()

    for bad in [dict(window=1), dict(num_std=0)]:
        try:
            BollingerBands(**bad)
            raise AssertionError(f"Expected ValueError for {bad}")
        except ValueError:
            pass
    print("  bollinger: signals, band ordering and validation OK")


def test_new_strategies_backtest_end_to_end():
    data = random_walk(n=600, seed=17, drift=0.0005, vol=0.018)
    engine = BacktestEngine()
    for strategy in (RSIMeanReversion(), BollingerBands()):
        result = engine.run_backtest('TEST', strategy, data=data)
        assert result, f"Backtest failed for {strategy.name}"
        assert result['metrics']['total_return'] is not None
        assert (result['equity_curve'] >= 0).all()
    print("  new strategies: end-to-end backtests OK")


# ---------------------------------------------------------------------------

def main():
    tests = [
        test_metrics_ratios,
        test_metrics_empty,
        test_engine_position_sizing_never_negative,
        test_engine_stop_loss,
        test_engine_take_profit,
        test_engine_end_of_data_close,
        test_engine_report,
        test_ma_crossover,
        test_ma_optimizer_uses_real_performance,
        test_rsi_strategy,
        test_bollinger_strategy,
        test_new_strategies_backtest_end_to_end,
    ]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            failures += 1
            print(f"FAIL {test.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passed")
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
