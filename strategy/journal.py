"""Trade logging utilities."""
import csv
import os

DEFAULT_TRADE_LOG = "trades.csv"


def log_trade(signal_data, filepath=None):
    """Append a signal to the CSV trade log.

    Args:
        signal_data: Dict returned by generate_signal().
        filepath: Optional path to the log file.  Defaults to trades.csv in the
            current working directory.
    """
    filepath = filepath or DEFAULT_TRADE_LOG
    file_exists = os.path.isfile(filepath)

    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp",
                "signal",
                "price",
                "score_long",
                "score_short",
                "rsi",
                "adx",
                "atr",
                "sl",
                "tp",
            ])
        writer.writerow([
            signal_data["timestamp"],
            signal_data["signal"],
            signal_data["price"],
            signal_data["score_long"],
            signal_data["score_short"],
            signal_data["rsi"],
            signal_data["adx"],
            signal_data["atr"],
            signal_data.get("sl"),
            signal_data.get("tp"),
        ])
