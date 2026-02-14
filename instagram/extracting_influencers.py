"""
Instagram Hashtag Username + Email/Contact Scraper (WITH SCROLLING)
====================================================================
Usage:
  1. pip install selenium webdriver-manager
  2. python instagram_scraper_with_scroll.py
  3. Log in manually in the browser, then press ENTER
  4. Results saved to instagram_leads.csv and .json

Flow:
  - Goes to instagram.com/explore/tags/{SEARCH_THING}
  - SCROLLS PAGE to load more posts
  - Clicks each post -> extracts username from span._ap3a._aaco._aacw
  - Goes back -> visits instagram.com/{username}/
  - Reads bio from span._ap3a._aaco._aacu -> extracts email / contact info
  - Saves: username, email, bio_text, post_url
"""

import re
import time
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

NUM_PHOTOS   = 50
OUTPUT_FILE  = "instagram_leads.csv"
WAIT_TIMEOUT = 15
SCROLL_PAUSE = 2.5  # seconds to wait between scrolls
MAX_SCROLLS  = 10   # maximum number of scroll attempts

SKIP_PATHS = ["/explore/", "/p/", "/reel/", "/stories/", "/tags/", "/locations/"]

# Regex: real emails
EMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
# Regex: obfuscated emails like "name [at] domain [dot] com"
OBFUSC_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+\s*[\[\(]?\s*at\s*[\]\)]?\s*[a-zA-Z0-9.\-]+"
    r"\s*[\[\(]?\s*dot\s*[\]\)]?\s*[a-zA-Z]{2,}",
    re.IGNORECASE,
)



def wait_for_element(driver, by, selector, timeout=WAIT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )


def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
    except ImportError:
        driver = webdriver.Chrome(options=options)
    return driver


def close_popups(driver):
    """Dismiss common Instagram popups."""
    for xpath in [
        '//button[contains(text(),"Not Now")]',
        '//button[contains(text(),"Not now")]',
        '//button[contains(text(),"Allow all cookies")]',
        '//button[contains(text(),"Accept All")]',
        '//div[@role="dialog"]//button[contains(text(),"Not Now")]',
    ]:
        try:
            driver.find_element(By.XPATH, xpath).click()
            time.sleep(0.8)
        except Exception:
            pass


def scroll_page(driver, num_photos_needed):
    """
    Scroll the Instagram hashtag page to load more posts.
    
    Returns the number of unique post links found after scrolling.
    """
    print(f"📜 Scrolling page to load more posts (target: {num_photos_needed})...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0
    post_links_found = 0
    
    while scrolls < MAX_SCROLLS:
        # Get current number of posts
        current_posts = driver.find_elements(By.XPATH, '//a[contains(@href, "/p/")]')
        post_links_found = len(set(link.get_attribute("href") for link in current_posts if link.get_attribute("href")))
        
        print(f"   Scroll {scrolls + 1}: Found {post_links_found} posts so far...")
        
        # Check if we have enough posts
        if post_links_found >= num_photos_needed:
            print(f"   ✅ Reached target of {num_photos_needed} posts!")
            break
        
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        
        # Close any popups that might appear during scrolling
        close_popups(driver)
        
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            print(f"   ⚠️  Reached bottom of page (no new content loaded)")
            break
            
        last_height = new_height
        scrolls += 1
    
    print(f"   📊 Total scrolls: {scrolls}, Total posts found: {post_links_found}\n")
    return post_links_found


def get_username_from_post(driver):
    """
    Extract the post author username.

    PRIMARY: <span class="_ap3a _aaco _aacw _aacx _aad7 _aade" dir="auto">username</span>
    Fallbacks use the profile anchor href and img alt attribute.
    """
    username = None

    # ── Strategy 1 (PRIMARY): span._ap3a._aaco._aacw[dir='auto'] ──────────
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span._ap3a._aaco._aacw[dir='auto']"))
        )
        span = driver.find_element(By.CSS_SELECTOR, "span._ap3a._aaco._aacw[dir='auto']")
        text = span.text.strip()
        if text and " " not in text and len(text) > 1:
            username = text
    except Exception:
        pass

    # ── Strategy 2: a._a6hd href inside div._aaqt ─────────────────────────
    if not username:
        try:
            container = driver.find_element(By.CSS_SELECTOR, "div._aaqt")
            for a in container.find_elements(By.CSS_SELECTOR, "a._a6hd[href][role='link']"):
                href = a.get_attribute("href") or ""
                if href and not any(s in href for s in SKIP_PATHS):
                    part = href.rstrip("/").split("/")[-1]
                    if part:
                        username = part
                        break
        except Exception:
            pass

    # ── Strategy 3: img alt "username's profile picture" ──────────────────
    if not username:
        try:
            img = driver.find_element(By.CSS_SELECTOR, "header img[alt*=\"profile picture\"]")
            alt = img.get_attribute("alt") or ""
            if "'s profile picture" in alt:
                username = alt.split("'s profile picture")[0].strip()
        except Exception:
            pass

    # ── Strategy 4: any profile anchor in article (widest fallback) ───────
    if not username:
        try:
            for a in driver.find_elements(By.CSS_SELECTOR, 'article a[role="link"][href^="/"]'):
                href = a.get_attribute("href") or ""
                if href and not any(s in href for s in SKIP_PATHS):
                    part = href.rstrip("/").split("/")[-1]
                    if part and len(part) > 1:
                        username = part
                        break
        except Exception:
            pass

    return username


def expand_bio(driver):
    """Click 'more' if the bio is truncated."""
    try:
        more_btn = driver.find_element(
            By.XPATH,
            '//div[@role="button"][.//span[contains(text(),"more")]]'
        )
        more_btn.click()
        time.sleep(1)
    except Exception:
        pass


def get_bio_and_contact(driver, username):
    """
    Visit instagram.com/{username}/, read bio, extract emails and contact info.

    Bio selector: span._ap3a._aaco._aacu[dir='auto']
    Also clicks 'more' to expand truncated bios.

    Returns dict: {bio_text, emails, has_contact, contact_keywords_found}
    """
    result = {
        "bio_text": "",
        "emails": ""
    }

    driver.get(f"https://www.instagram.com/{username}/")
    time.sleep(3)
    close_popups(driver)
    expand_bio(driver)

    # Bio container: span._ap3a._aaco._aacu[dir='auto']
    bio_text = ""
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span._ap3a._aaco._aacu[dir='auto']"))
        )
        bio_spans = driver.find_elements(
            By.CSS_SELECTOR, "span._ap3a._aaco._aacu[dir='auto']"
        )
        # Pick the longest text (inner spans may duplicate)
        bio_text = max((s.text.strip() for s in bio_spans), key=len, default="")
    except Exception:
        pass

    result["bio_text"] = bio_text
    if not bio_text:
        return result

    # Extract real + obfuscated emails
    emails_found = EMAIL_RE.findall(bio_text)
    obfusc_found = OBFUSC_RE.findall(bio_text)
    all_emails   = list(dict.fromkeys(emails_found + obfusc_found))
    result["emails"] = " | ".join(all_emails)

    # Check for contact keywords
    bio_lower = bio_text.lower()

    return result


def scrape_usernames(SEARCH_LIST):
    driver = make_driver()
    
    collected = []
    
    # ── Load existing usernames from CSV to avoid duplicates ──────────────
    import os
    existing_usernames = set()
    if os.path.isfile(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_usernames = {row["username"] for row in reader if "username" in row}
            print(f"\n📋 Loaded {len(existing_usernames)} existing usernames from {OUTPUT_FILE}")
        except Exception as e:
            print(f"   ⚠️  Could not read existing CSV: {e}")

    try:
        # ── Step 1: Open Instagram, wait for manual login ──────────────────
        print("\n📸 Opening Instagram...")
        driver.get("https://www.instagram.com/")
        time.sleep(3)
        close_popups(driver)

        input(
            "\n🔐 Please log in to Instagram in the browser window.\n"
            "   When fully logged in, come back here and press ENTER to continue... "
        )
        time.sleep(2)
        close_popups(driver)
        
        for SEARCH_THING in SEARCH_LIST:
            if " " in SEARCH_THING:
                SEARCH_THING = SEARCH_THING.replace(" ", "")
            print(f"\n{'='*60}")
            print(f"Processing: #{SEARCH_THING}")
            print('='*60)
            
            # ── Step 2: Navigate to hashtag page ──────────────────────────────
            tag_url = f"https://www.instagram.com/explore/tags/{SEARCH_THING}/"
            print(f"\n🔍 Navigating to #{SEARCH_THING} ...")
            driver.get(tag_url)
            time.sleep(4)
            close_popups(driver)

            # ── Step 3: SCROLL to load more posts ──────────────────────────────
            scroll_page(driver, NUM_PHOTOS)

            # ── Step 4: Collect post URLs from the grid ────────────────────────
            print("🖼️  Collecting post URLs from grid...")
            time.sleep(2)
            wait_for_element(driver, By.XPATH, '//a[contains(@href, "/p/")]')

            post_links = driver.find_elements(By.XPATH, '//a[contains(@href, "/p/")]')
            post_hrefs = []
            seen = set()

            for link in post_links:
                href = link.get_attribute("href")
                if href and "/p/" in href and href not in seen:
                    seen.add(href)
                    post_hrefs.append(href)
                if len(post_hrefs) >= NUM_PHOTOS:
                    break

            print(f"   ✅ Collected {len(post_hrefs)} unique post link(s) to visit.\n")

            # ── Step 5: Visit each post, get username, check profile bio ───────
            for i, post_url in enumerate(post_hrefs, start=1):
                print(f"📷 [{i}/{len(post_hrefs)}] Opening post: {post_url}")
                driver.get(post_url)
                time.sleep(3)
                close_popups(driver)

                username = get_username_from_post(driver)

                if not username:
                    print(f"   ⚠️  Could not extract username, skipping.")
                    driver.back()
                    time.sleep(2)
                    continue

                # Check if username already exists in CSV
                if username in existing_usernames:
                    print(f"   ⏭️  @{username} already in CSV, skipping...")
                    driver.back()
                    time.sleep(2)
                    continue

                print(f"   ✅ Username found: @{username}")

                # Go back to hashtag page
                print(f"   ↩️  Going back to #{SEARCH_THING} page...")
                driver.back()
                time.sleep(2)

                # Visit profile and check bio for contact info
                print(f"   🔎  Checking bio for @{username}...")
                contact = get_bio_and_contact(driver, username)

                if contact["emails"]:
                    print(f"   📧  Email: {contact['emails']}")
                else:
                    print(f"   —   No contact info found in bio")

                collected.append({
                    "username":         username,
                    "emails":           contact["emails"],
                    "bio":              contact["bio_text"].replace("\n", " "),
                    "category":         SEARCH_THING
                })
                
                # Add to existing usernames set to avoid re-scraping in same session
                existing_usernames.add(username)

                # Back to hashtag for next iteration
                print(f"   ↩️  Back to #{SEARCH_THING}...")
                driver.get(tag_url)
                time.sleep(3)

    except KeyboardInterrupt:
        print("\n⛔ Interrupted.")
    finally:
        driver.quit()

    # ── Step 6: Save results (APPEND mode - preserves existing data) ──────
    if collected:
        fields = ["username", "emails", "bio", 'category']
        
        # Check if file exists to determine if we need to write headers
        import os
        file_exists = os.path.isfile(OUTPUT_FILE)
        
        # Append new profiles to CSV
        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            # Only write header if file is new
            if not file_exists:
                writer.writeheader()
            writer.writerows(collected)
        
        print(f"\n✅ Done! Added {len(collected)} new profiles to {OUTPUT_FILE}")

    else:
        print("\n⚠️  No new data collected.")

    return collected


if __name__ == "__main__":
    scrape_usernames(["fashion influencers","digital creator", "content creator"])