import asyncio
import csv
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.errors import FloodWaitError
from dotenv import load_dotenv
import os
load_dotenv()
import asyncio


api_id=os.getenv("api_id")
api_hash=os.getenv("api_hash")
INPUT_CSV = "telegram_groups_final.csv"
OUTPUT_CSV = "leads.csv"

async def main():
    async with TelegramClient("session", api_id, api_hash) as client:

        with open(INPUT_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            groups = [row["telegram_link"] for row in reader if row["telegram_link"]]

        results = []

        for group_url in groups:
            print(f"\n🔍 Processing: {group_url}")

            try:
                channel = await client.get_entity(group_url)
                offset = 0
                limit = 100

                while True:
                    participants = await client(GetParticipantsRequest(
                        channel=channel,
                        filter=ChannelParticipantsSearch(""),
                        offset=offset,
                        limit=limit,
                        hash=0
                    ))

                    if not participants.users:
                        break

                    for user in participants.users:
                        if user.username:
                            results.append({
                                "group_url": group_url,
                                "t_me_member_url": f"https://t.me/{user.username}"
                            })

                    offset += len(participants.users)
                    await asyncio.sleep(2)  # safety delay

            except FloodWaitError as e:
                print(f"⏳ Flood wait: sleeping {e.seconds}s")
                await asyncio.sleep(e.seconds)

            except Exception as e:
                print(f"❌ Failed for {group_url}: {e}")

        # Save output
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["group_url", "t_me_member_url"]
            )
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ Saved {len(results)} rows to {OUTPUT_CSV}")

asyncio.run(main())