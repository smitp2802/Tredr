from telethon import TelegramClient
import os

API_ID=38739072

API_HASH="bfef56ad81b14a2a4266db4f0bdbbc5d"

CHANNEL = "candleking009"

client = TelegramClient(
    "tredr_session",
    API_ID,
    API_HASH
)

async def main():

    os.makedirs(
        "telegram/images",
        exist_ok=True
    )

    count = 0

    async for message in client.iter_messages(
        CHANNEL,
        limit=500
    ):

        if message.photo:

            path = await message.download_media(
                file="telegram/images/"
            )

            print(
                f"Downloaded: {path}"
            )

            count += 1

    print(
        f"Total images: {count}"
    )

with client:
    client.loop.run_until_complete(
        main()
    )

