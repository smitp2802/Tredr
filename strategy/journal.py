import csv
import os

FILE = "trades.csv"

def log_trade(signal_data):

    file_exists = os.path.isfile(FILE)

    with open(FILE, "a", newline="") as f:

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
                "atr"
            ])

        writer.writerow([
            signal_data["timestamp"],
            signal_data["signal"],
            signal_data["price"],
            signal_data["score_long"],
            signal_data["score_short"],
            signal_data["rsi"],
            signal_data["adx"],
            signal_data["atr"]
        ])
