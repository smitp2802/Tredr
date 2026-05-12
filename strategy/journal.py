from datetime import datetime


def log_trade(signal_data):

    now = datetime.now()

    print(
        f'[{now}] {signal_data}'
    )
