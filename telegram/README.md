# Steps to follow:

## It will extract groups from telegram

```bash
python extracting_telegram_groups.py
```

1. input the category from the categories list
2. if any 'verify as human' pops up come on browser, please confirm it manually
3. it will create the `(telegram_groups_final.csv)` which has group links based on the given category

## It will extract all recent users and their messages from the groups present in telegram_groups_final.csv and save the data in telegram_users.csv and telegram_messages.csv 

1. First you have to get api_id & api_hash (Telethon)

Steps For this
* Go to 👉 https://my.telegram.org
* Enter the OTP you receive on Telegram
* Click “API development tools”
* Login with your Telegram phone number
* Fill the form:
App title: anything (e.g., scraper)
Short name: anything (e.g., scraper_app)

* Platform: Desktop
* Click Create application

* You’ll see:
- App api_id
- App api_hash

2. Copy both. Paste it in `.env` file

3. Then run 
```bash   
python recentusers.py
```

## It automates messages from telegram_user.csv

Replace values according to your login details.

COUNTRY = "India"  # Country name
PHONE_NUMBER = "+918810447061"  
MESSAGE_TEXT = "Hello, Just wanted to connect."

When it asks for otp, enter the otp you recieved on telegram in the terminal 
```bash
python telemessage.py
```

