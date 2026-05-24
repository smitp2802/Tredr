from datetime import datetime
import csv
import os

def log_trade(signal_data):

    now = datetime.now()

    print(
        f"[{now}] {signal_data}"
    )

    file_exists = os.path.isfile(
        "logs/trades.csv"
    )

    os.makedirs(
        "logs",
        exist_ok=True
    )

    with open(
        "logs/trades.csv",
        "a",
        newline=""
    ) as f:

        writer = csv.writer(f)

        if not file_exists:

            writer.writerow([
                "timestamp",
                "signal",
                "price",
                "score_long",
                "score_short",
                "rsi",
                "adx"
            ])

        writer.writerow([
            signal_data["timestamp"],
            signal_data["signal"],
            signal_data["price"],
            signal_data["score_long"],
            signal_data["score_short"],
            signal_data["rsi"],
            signal_data["adx"]
        ])
