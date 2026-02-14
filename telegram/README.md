

## It will extract groups from telegram
python extracting_telegram_groups.py

## It will extract all members from the groups present in telegram_groups_final.csv 
python extracting_all_members.py

## It will extract all recent users and their messages from the groups present in telegram_groups_final.csv 
# It does everything except automating messages
python recentusers.py

## It removes duplicate users from leads.csv which has all members
python returning_only_usernames.py

## It automates messages 
python telemessage.py