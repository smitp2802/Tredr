import os
import shutil
import easyocr

RAW_DIR = "telegram/images/"

BTC_DIR = "telegram/images/btcusd"
XAU_DIR = "telegram/images/xauusd"
REVIEW_DIR = "telegram/images/review"

reader = easyocr.Reader(['en'])

BTC_WORDS = [
    "BTC",
    "BTCUSD",
    "BTCUSDT",
    "BITCOIN",
    "XBT"
]

XAU_WORDS = [
    "XAU",
    "XAUUSD",
    "GOLD"
]

print("RAW_DIR =", RAW_DIR)
print("Files found =", len(os.listdir(RAW_DIR)))

for filename in os.listdir(RAW_DIR):

    filepath = os.path.join(
        RAW_DIR,
        filename
    )

    try:

        text = " ".join(
            reader.readtext(
                filepath,
                detail=0
            )
        ).upper()

        if any(
            word in text
            for word in BTC_WORDS
        ):

            shutil.move(
                filepath,
                os.path.join(
                    BTC_DIR,
                    filename
                )
            )

            print(
                f"[BTC] {filename}"
            )

        elif any(
            word in text
            for word in XAU_WORDS
        ):

            shutil.move(
                filepath,
                os.path.join(
                    XAU_DIR,
                    filename
                )
            )

            print(
                f"[XAU] {filename}"
            )

        else:

            shutil.move(
                filepath,
                os.path.join(
                    REVIEW_DIR,
                    filename
                )
            )

    except Exception as e:

        print(
            f"Failed: {filename}"
        )
