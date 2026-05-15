PAPER_TRADING = True


def place_order(signal_data, pair):

    signal = signal_data['signal']

    if signal == "BUY":

        if PAPER_TRADING:
            print(f"[PAPER] BUY {pair}")

        else:
            exchange.create_market_buy_order(...)

    print(
        f"""
        =========================
        SIGNAL: {signal}
        PAIR: {PAIR}
        PRICE: {signal_data['price']}
        SCORE LONG: {signal_data['score_long']}
        RSI: {signal_data['rsi']}
        ADX: {signal_data['adx']}
        TIME: {signal_data['timestamp']}
        =========================
        """
    )
