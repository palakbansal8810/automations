from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

# Chrome setup
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
categories=['art-design','auto-moto','betting','blogs','books-magazine','business-startups','celebrities','communication','airdrop','cryptocurrencies','crypto-fx-trading','economics-politics','education'
          'entertainment','fashion-beauty','food','games-apps','health','languages','love','marketing','travel','telegram-miniapp-games','sports-fitness','music','videos-movies']

print(categories)

category= input("Choose any category from above categories, make sure it should be in the list\n")
category=category.lower()
if category in categories:
    MAIN_URL = f"https://telegramchannels.me/groups?category={category}&sort=members"
else:
    print("Category is not in the list, going with the airdrop")
    category='airdrop'
    MAIN_URL = f"https://telegramchannels.me/groups?category={category}&sort=members"
driver.get(MAIN_URL)
time.sleep(5)

group_page_links = []

# STEP 1: Collect all group detail page links
cards = driver.find_elements(By.CSS_SELECTOR, "div.card.media-card")

for card in cards:
    try:
        link = card.find_element(
            By.CSS_SELECTOR,
            "a[href^='https://telegramchannels.me/groups/']"
        ).get_attribute("href")

        group_page_links.append(link)
    except:
        continue

print(f"Found {len(group_page_links)} group pages")

results = []

# STEP 2: Visit each group page & extract t.me link
for link in group_page_links:
    driver.get(link)
    time.sleep(4)

    try:
        group_name = driver.find_element(By.TAG_NAME, "h1").text
    except:
        group_name = None

    telegram_link = None

    try:
        telegram_link = driver.find_element(
            By.CSS_SELECTOR,
            "a[href^='https://t.me/']"
        ).get_attribute("href")
    except:
        pass

    results.append({
        "group_name": group_name,
        "group_page": link,
        "telegram_link": telegram_link,
        "category":category
    })

    print(group_name, telegram_link)

driver.quit()

# Save to CSV
with open("telegram_groups_final.csv", "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["group_name", "group_page", "telegram_link",'category']
    )
    writer.writeheader()
    writer.writerows(results)
