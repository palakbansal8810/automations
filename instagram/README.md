# 📸 Instagram Hashtag Lead Scraper (Selenium + Scrolling)

This script scrapes **Instagram usernames and contact info (emails)** from posts under specific **hashtags**.  
It automatically scrolls the hashtag page to load more posts, visits each post to extract the username, then checks the user’s profile bio for email/contact details.

Results are saved to `instagram_leads.csv` (append mode, so you don’t lose previous data).

---

## 🚀 Features

- Manual Instagram login (supports OTP / 2FA)
- Scrolls hashtag pages to load more posts
- Extracts:
  - Username from each post  
  - Bio text from profile  
  - Email addresses (real + obfuscated like `name [at] domain [dot] com`)  
- Avoids duplicates using existing CSV
- Saves results to CSV (and JSON-ready structure)

---

## 🛠 Requirements

- Google Chrome  
- ChromeDriver (auto-managed via `webdriver-manager`)

Install dependencies:

```bash
pip install selenium==4.35.0 webdriver-manager
```

 How to Run
```bash
cd instagram
```
```bash
python extracting_influencers.py
```
then run for removing duplicates and insta url

```bash
python remove_duplicates.py
```
## Steps:

- run the file via python extracting_influencers.py
- Log in manually
- Press ENTER in terminal after login

## Configuration
Hashtags to scrape
scrape_usernames(["fashion influencers", "digital creator", "content creator"])
Number of posts to collect
NUM_PHOTOS = 50
Scrolling behavior
MAX_SCROLLS  = 10
SCROLL_PAUSE = 2.5
Output file
OUTPUT_FILE = "instagram_leads.csv"

## Output Format (instagram_leads.csv)
Columns:

username

emails

bio

category (hashtag used)