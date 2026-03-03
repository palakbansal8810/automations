"""
Instagram Hashtag Username + Email/Contact Scraper (WITH SCROLLING)
====================================================================
Usage:
  1. pip install selenium webdriver-manager
  2. python instagram_scraper_with_scroll.py
  3. Log in manually in the browser, then press ENTER
  4. Results saved to instagram_leads.csv and .json
"""

import re
import time
import csv
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

NUM_PHOTOS   = 200
OUTPUT_FILE  = "new_instagram_leads.csv"
WAIT_TIMEOUT = 15
SCROLL_PAUSE = 2.5
MAX_SCROLLS  = 50

SKIP_PATHS = ["/explore/", "/p/", "/reel/", "/stories/", "/tags/", "/locations/"]

EMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
OBFUSC_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+\s*[\[\(]?\s*at\s*[\]\)]?\s*[a-zA-Z0-9.\-]+"
    r"\s*[\[\(]?\s*dot\s*[\]\)]?\s*[a-zA-Z]{2,}",
    re.IGNORECASE,
)


def save_to_csv(collected, output_file=OUTPUT_FILE):
    if not collected:
        return

    fields = ["username", "followers", "emails", "bio", "profile_category", "hashtag"]
    file_exists = os.path.isfile(output_file)

    try:
        with open(output_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            if not file_exists:
                writer.writeheader()
            writer.writerows(collected)
        print(f"\nSaved {len(collected)} record(s) to {output_file}")

    except Exception as e:
        backup_file = f"instagram_leads_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        print(f"\n Could not write to {output_file}: {e}")
        print(f"   Attempting backup save to {backup_file} ...")
        try:
            with open(backup_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(collected)
            print(f"  Backup saved to {backup_file}")
        except Exception as backup_err:
            print(f"  Backup also failed: {backup_err}")


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
    Accumulates hrefs into a persistent set to survive DOM virtualization.
    """
    print(f"Scrolling page to load more posts (target: {num_photos_needed})...")

    all_hrefs = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0
    no_new_scrolls = 0

    while scrolls < MAX_SCROLLS:
        try:
            current_posts = driver.find_elements(By.XPATH, '//a[contains(@href, "/p/")]')
            before = len(all_hrefs)
            for link in current_posts:
                href = link.get_attribute("href")
                if href and "/p/" in href:
                    all_hrefs.add(href)
            newly_added = len(all_hrefs) - before

            print(f"   Scroll {scrolls + 1}: +{newly_added} new  |  {len(all_hrefs)} total accumulated")

            if len(all_hrefs) >= num_photos_needed:
                print(f"   Reached target of {num_photos_needed} posts!")
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE)
            close_popups(driver)

            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                no_new_scrolls += 1
                if no_new_scrolls >= 8:
                    break
            else:
                no_new_scrolls = 0

            last_height = new_height
            scrolls += 1

        except Exception as e:
            scrolls += 1
            continue

    print(f"  Total scrolls: {scrolls} | Accumulated posts: {len(all_hrefs)}\n")
    return all_hrefs


def get_username_from_post(driver):
    """Extract the post author username with multiple fallback strategies."""
    username = None

    # Strategy 1 (PRIMARY)
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

    # Strategy 2
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

    # Strategy 3
    if not username:
        try:
            img = driver.find_element(By.CSS_SELECTOR, "header img[alt*=\"profile picture\"]")
            alt = img.get_attribute("alt") or ""
            if "'s profile picture" in alt:
                username = alt.split("'s profile picture")[0].strip()
        except Exception:
            pass

    # Strategy 4
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
    try:
        more_btn = driver.find_element(
            By.XPATH,
            '//div[@role="button"][.//span[contains(text(),"more")]]'
        )
        more_btn.click()
        time.sleep(1)
    except Exception:
        pass


def get_followers(driver):
    """Extract follower count from a profile page already loaded in the driver."""

    # Strategy 1 — title attribute carries the raw integer with commas
    for xpath in [
        '//span[contains(text(),"followers")]//span[@title]',
        '//span[contains(text(),"followers")]/preceding-sibling::span[@title]',
        '//span[@title][following-sibling::span[contains(text(),"followers")]]',
    ]:
        try:
            el = driver.find_element(By.XPATH, xpath)
            title = el.get_attribute("title")
            if title:
                return title.replace(",", "")
        except Exception:
            pass

    # Strategy 2 — visible abbreviated label (38.2K, 1.1M …)
    try:
        el = driver.find_element(
            By.XPATH,
            '//span[contains(text(),"followers")]//span[contains(@class,"html-span")]'
        )
        text = el.text.strip()
        if text:
            return text
    except Exception:
        pass

    # Strategy 3 — meta description fallback
    try:
        meta = driver.find_element(By.XPATH, '//meta[@name="description"]')
        content = meta.get_attribute("content") or ""
        m = re.search(r"([\d,]+)\s+Followers", content, re.IGNORECASE)
        if m:
            return m.group(1).replace(",", "")
    except Exception:
        pass

    return ""


def get_profile_category(driver):
    """
    Extract the account category label shown on Instagram profiles.
    e.g. "Digital creator", "Musician/band", "Public figure", etc.

    The element sits in a <div> with classes including _ap3a _aaco _aacu _aacy _aad6 _aade
    and a dir="auto" attribute — distinct from the bio span which shares _ap3a _aaco _aacu
    but lacks _aacy _aad6 _aade.

    Falls back to a broader XPath search if the CSS classes ever change.
    """
    # Strategy 1 — exact CSS class fingerprint from the inspected element
    for selector in [
        "div._ap3a._aaco._aacu._aacy._aad6._aade[dir='auto']",
        "div._ap3a._aaco._aacu._aad6._aade[dir='auto']",
    ]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            text = el.text.strip()
            if text:
                return text
        except Exception:
            pass

    # Strategy 2 — look for the inner span with those same distinctive classes
    try:
        el = driver.find_element(
            By.CSS_SELECTOR,
            "span._ap3a._aaco._aacu._aacy._aad6._aade[dir='auto']"
        )
        text = el.text.strip()
        if text:
            return text
    except Exception:
        pass

    # Strategy 3 — XPath: find a div/span with dir=auto that sits OUTSIDE the bio section
    # and contains only a short label (category labels are rarely > 50 chars)
    try:
        candidates = driver.find_elements(
            By.XPATH,
            '//*[@dir="auto" and contains(@class,"_aad6") and contains(@class,"_aade")]'
        )
        for el in candidates:
            text = el.text.strip()
            if text and len(text) <= 60:
                return text
    except Exception:
        pass

    return ""


def get_bio_and_contact(driver, username):
    """
    Visit instagram.com/{username}/, read bio, extract emails, contact info,
    follower count, and profile category.
    """
    result = {"bio_text": "", "emails": "", "followers": "", "profile_category": ""}

    try:
        driver.get(f"https://www.instagram.com/{username}/")
        time.sleep(3)
        close_popups(driver)
        expand_bio(driver)

        result["followers"] = get_followers(driver)
        ans=get_profile_category(driver)
        if ans=='Follow':
            result["profile_category"]=''
        else:
            result['profile_category']= ans

        bio_text = ""
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span._ap3a._aaco._aacu[dir='auto']"))
            )
            bio_spans = driver.find_elements(
                By.CSS_SELECTOR, "span._ap3a._aaco._aacu[dir='auto']"
            )
            bio_text = max((s.text.strip() for s in bio_spans), key=len, default="")
        except Exception as e:
            print(f"   Could not read bio for @{username}: {e}")

        result["bio_text"] = bio_text

        if bio_text:
            emails_found = EMAIL_RE.findall(bio_text)
            obfusc_found = OBFUSC_RE.findall(bio_text)
            all_emails   = list(dict.fromkeys(emails_found + obfusc_found))
            result["emails"] = " | ".join(all_emails)

    except Exception as e:
        print(f"    Error visiting profile @{username}: {e}")

    return result


def scrape_usernames(SEARCH_LIST):
    driver = make_driver()
    collected = []
    existing_usernames = set()
    if os.path.isfile(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_usernames = {row["username"] for row in reader if "username" in row}
            print(f"\n Loaded {len(existing_usernames)} existing usernames from {OUTPUT_FILE}")
        except Exception as e:
            print(f"     Could not read existing CSV: {e}")

    try:
        print("\n📸 Opening Instagram...")
        driver.get("https://www.instagram.com/")
        time.sleep(2)
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

            hashtag_collected = []

            try:
                tag_url = f"https://www.instagram.com/explore/tags/{SEARCH_THING}/"
                print(f"\n Navigating to #{SEARCH_THING} ...")
                driver.get(tag_url)
                time.sleep(2)
                close_popups(driver)

                accumulated_hrefs = scroll_page(driver, NUM_PHOTOS)
                post_hrefs = list(accumulated_hrefs)[:NUM_PHOTOS]

                print(f" Collected {len(post_hrefs)} unique post link(s) to visit.\n")

                for i, post_url in enumerate(post_hrefs, start=1):
                    try:
                        print(f" [{i}/{len(post_hrefs)}] Opening post: {post_url}")
                        driver.get(post_url)
                        time.sleep(3)
                        close_popups(driver)

                        username = get_username_from_post(driver)

                        if not username:
                            print(f"  Could not extract username, skipping.")
                            driver.back()
                            time.sleep(2)
                            continue

                        if username in existing_usernames:
                            print(f"   @{username} already in CSV, skipping...")
                            driver.back()
                            time.sleep(2)
                            continue

                        print(f" Username found: @{username}")
                        print(f"   Going back to #{SEARCH_THING} page...")
                        driver.back()
                        time.sleep(2)

                        print(f"    Checking bio/followers/category for @{username}...")
                        contact = get_bio_and_contact(driver, username)

                        if contact["followers"]:
                            print(f"  Followers: {contact['followers']}")
                        if contact["profile_category"]:
                            print(f"  Category:  {contact['profile_category']}")
                        if contact["emails"]:
                            print(f"  Email:     {contact['emails']}")
                        else:
                            print(f"   —   No contact info found in bio")

                        record = {
                            "username":         username,
                            "followers":        contact["followers"],
                            "emails":           contact["emails"],
                            "bio":              contact["bio_text"].replace("\n", " "),
                            "profile_category": contact["profile_category"],   # ← NEW column
                            "hashtag":          SEARCH_THING,                  # renamed from "category"
                        }

                        hashtag_collected.append(record)
                        collected.append(record)
                        existing_usernames.add(username)

                        if len(hashtag_collected) % 10 == 0:
                            print(f"\n Auto-saving checkpoint ({len(hashtag_collected)} records for #{SEARCH_THING})...")
                            save_to_csv([record], OUTPUT_FILE)

                        print(f"    Back to #{SEARCH_THING}...")
                        driver.get(tag_url)
                        time.sleep(3)

                    except KeyboardInterrupt:
                        raise

                    except Exception as post_err:
                        print(f"\n Error on post [{i}] {post_url}: {post_err}")
                        print(f"  Saving progress and skipping this post...")
                        if hashtag_collected:
                            save_to_csv(hashtag_collected, OUTPUT_FILE)
                            existing_usernames.update(r["username"] for r in hashtag_collected)
                            hashtag_collected = []
                        try:
                            driver.get(tag_url)
                            time.sleep(3)
                        except Exception as nav_err:
                            print(f"    Could not navigate back to #{SEARCH_THING}: {nav_err}")
                        continue

            except KeyboardInterrupt:
                raise

            except Exception as hashtag_err:
                print(f"\n Fatal error while processing #{SEARCH_THING}: {hashtag_err}")
                if hashtag_collected:
                    print(f" Saving {len(hashtag_collected)} record(s) collected before the error...")
                    save_to_csv(hashtag_collected, OUTPUT_FILE)
                    hashtag_collected = []
                print(f"    Moving on to next hashtag...\n")
                continue

            finally:
                if hashtag_collected:
                    print(f"\n Final save for #{SEARCH_THING} ({len(hashtag_collected)} record(s))...")
                    save_to_csv(hashtag_collected, OUTPUT_FILE)
                    hashtag_collected = []

    except KeyboardInterrupt:
        print("\n Interrupted by user — saving all collected data...")
        save_to_csv(collected, OUTPUT_FILE)

    except Exception as fatal_err:
        print(f"\n Unexpected session-level error: {fatal_err}")
        print("  Attempting emergency save...")
        save_to_csv(collected, OUTPUT_FILE)

    finally:
        print(f"\n Session ended. Total records collected this session: {len(collected)}")
        try:
            driver.quit()
        except Exception:
            pass

    return collected


if __name__ == "__main__":
    scrape_usernames(['Tamil influencers', 'tamil content creators', 'Tamil digital creator'])