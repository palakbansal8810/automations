## Features

- Manual Facebook login (supports OTP / 2FA)
- Auto scroll to load more posts
- Extracts:
  - Author name & profile link  
  - Post content  
  - Post permalink  
  - Date posted  
- Deduplication of posts  
- Saves data to `facebook_posts.csv`
## Requirements

- Google Chrome  
- ChromeDriver (matching your Chrome version)

Install dependencies:

```bash
pip install selenium==4.35.0
```
How to Run

```bash
python facebook_scraper.py
```

## Steps:

1. Browser opens Facebook login page

2. Login manually (OTP / 2FA if required)

3. Press ENTER in terminal after login

4. Script opens the target group and starts scraping

## Output saved to facebook_posts.csv

## Configuration
Set target groups/pages:

TARGET_URL = ["https://www.facebook.com/groups/{group_id}"]
Adjust scrolling:

SCROLLS = 10
SCROLL_DELAY = 3

## Output
facebook_posts.csv contains:

author_name

author_link

post_link

date_posted

content