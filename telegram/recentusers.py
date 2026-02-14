from telethon import TelegramClient
from telethon.errors import UserNotParticipantError, ChannelPrivateError
import asyncio
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import re

load_dotenv()
api_id = int(os.getenv("api_id"))
api_hash = os.getenv("api_hash")

async def main():
    client = TelegramClient("session_name", api_id, api_hash)
    await client.start()
    
    messages_data = []
    seen_users = set()
    
    group_csv = pd.read_csv("telegram_groups_final.csv", dtype=str)
    groups = group_csv['telegram_link'].dropna().astype(str).tolist()
    
    for group in groups:
        try:
            async for msg in client.iter_messages(group, limit=200):
                if msg.sender_id and msg.sender:
                    # Check if user has a username
                    if hasattr(msg.sender, 'username') and msg.sender.username:
                        # Skip if no text or only whitespace
                        if not msg.text or not msg.text.strip():
                            continue
                        
                        # Clean the message: remove extra whitespace and newlines
                        cleaned_message = re.sub(r'\s+', ' ', msg.text.strip())
                        
                        messages_data.append({
                            'username': msg.sender.username,
                            'user_id': msg.sender.id,
                            'name': getattr(msg.sender, 'first_name', ''),
                            'message': cleaned_message,
                            'date': msg.date.strftime('%Y-%m-%d %H:%M:%S') if msg.date else '',
                            'group': group,
                            'message_id': msg.id
                        })
                        seen_users.add(msg.sender.username)
                          
        except (ChannelPrivateError, UserNotParticipantError) as e:
            print(f"Error accessing group {group}: {e}")
            continue
    
    print(f"Found {len(messages_data)} messages from {len(seen_users)} unique users with usernames")
    
    # Save messages to CSV
    if messages_data:
        df = pd.DataFrame(messages_data)
        df.to_csv("telegram_messages.csv", index=False)
        print(f"Saved {len(messages_data)} messages to telegram_messages.csv")
        
        # Also create a unique users CSV
        users_df = df[['username', 'user_id', 'name']].drop_duplicates(subset=['user_id'])
        users_df.to_csv("telegram_users.csv", index=False)
        print(f"Saved {len(users_df)} unique users to telegram_users.csv")
    else:
        print("No messages found.")
    
    await client.disconnect()

asyncio.run(main())