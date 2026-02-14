import time
import csv
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

BASE_URL = "https://www.facebook.com"

# 🔗 Put your group or page URL here
TARGET_URL = ["https://www.facebook.com/groups/673107963266720"]

OUTPUT_FILE = "facebook_posts.csv"

SCROLLS = 10        # how many times to scroll
SCROLL_DELAY = 3     # seconds between scrolls


def setup_driver():
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    return driver


def manual_login(driver):
    print("🌐 Opening Facebook login page...")
    driver.get("https://www.facebook.com/login")

    print("\n🔐 Please log in manually in the browser window.")
    print("👉 If OTP / 2FA / checkpoint appears, complete it.")
    print("👉 After you see your Facebook home/feed, come back here.")
    input("\n✅ Press ENTER here after successful login...")


def scroll_page(driver, times=1):
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_DELAY)


def expand_see_more(post_container, driver):
    try:
        see_more = post_container.find_element(
            By.XPATH, ".//div[normalize-space()='See more' or .//span[normalize-space()='See more']]"
        )
        driver.execute_script("arguments[0].click();", see_more)
        time.sleep(0.4)
    except:
        pass


def extract_author(metadata_container):
    """Extract author name and profile link from metadata container"""
    author_name, author_link = "", ""
    try:
        # Find the profile_name div
        profile_div = metadata_container.find_element(
            By.XPATH, 
            ".//div[@data-ad-rendering-role='profile_name']"
        )
        
        # Get the author name from the span inside the <b> tag
        name_span = profile_div.find_element(
            By.XPATH,
            ".//b/span[@class='html-span xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x1hl2dhg x16tdsg8 x1vvkbs']"
        )
        author_name = name_span.text.strip()
        
        
        # Get the profile link from the <a> tag
        author_link_element = profile_div.find_element(
            By.XPATH,
            ".//a[contains(@href, '/user/') or contains(@href, '/profile.php')]"
        )
        href = author_link_element.get_attribute("href")
        if href:
            author_link = urljoin(BASE_URL, href)
            
    except Exception as e:
        print(f"    ⚠️ Error extracting author: {e}")
    
    return author_name, author_link


def extract_post_link(story_msg):
    """Extract post link from the story message element"""
    post_link = ""
    try:
        # Find the parent container first
        current = story_msg
        for _ in range(15):
            current = current.find_element(By.XPATH, "./..")
            try:
                # Look for all links in this container
                all_links = current.find_elements(By.XPATH, ".//a[@href]")
                
                for link in all_links:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    
                    # Check if this is a post link (contains /posts/ or /permalink/)
                    if '/posts/' in href or '/permalink/' in href:
                        post_link = urljoin(BASE_URL, href)
                        return post_link
                    
                    # Alternative: look for photo links that might indicate a post
                    if '/photo/' in href and 'fbid=' in href:
                        post_link = urljoin(BASE_URL, href)
                        return post_link
                        
            except:
                continue
                
    except Exception as e:
        print(f"    ⚠️ Error extracting post link: {e}")
    
    return post_link

def extract_date_from_post_link(driver, post_link):
    """Open post in a new tab, extract date, then return to feed"""
    original_window = driver.current_window_handle

    try:
        # Open new tab
        driver.execute_script("window.open(arguments[0], '_blank');", post_link)
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)

        # Switch to new tab
        new_window = [w for w in driver.window_handles if w != original_window][0]
        driver.switch_to.window(new_window)

        # Wait for hidden __fb-light-mode block
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, '__fb-light-mode')]"))
        )

        date_span = driver.find_element(
            By.XPATH, "//div[contains(@class, '__fb-light-mode')]//span[starts-with(@id, '_R_') or starts-with(@id, '_r_')]"
        )

        date_text = driver.execute_script(
            "return arguments[0].textContent;", date_span
        ).strip()

        return date_text

    except Exception as e:
        print(f"    ⚠️ Failed to extract date from post page: {e}")
        return ""

    finally:
        # Close new tab and switch back to feed
        try:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(original_window)
        except:
            pass


def extract_post_datetime(metadata_container, driver):
    """Extract post date (robust for different FB post types)"""
    # 1) Try __fb-light-mode date
    try:
        date_span = metadata_container.find_element(
            By.XPATH,
            ".//div[contains(@class, '__fb-light-mode')]//span[starts-with(@id, '_r_')]"
        )
        date_text = driver.execute_script(
            "return arguments[0].textContent;", date_span
        ).strip()
        if date_text:
            return date_text
    except:
        pass

    # 2) Fallback: timestamp anchor (works for photo/share posts)
    try:
        time_anchor = metadata_container.find_element(
            By.XPATH,
            ".//a[contains(@href, 'multi_permalinks') or contains(@href, '/permalink/') or contains(@href, '/posts/') or contains(@href, 'fbid=')]"
        )
        return (time_anchor.get_attribute("aria-label") or time_anchor.text.strip() or "")
    except Exception as e:
        print(f"    ⚠️ Error extracting datetime: {e}")
        return ""


def extract_post_text_from_story_message(story_message_container):
    """Extract post content from story_message container"""
    lines = []
    try:
        text_nodes = story_message_container.find_elements(
            By.XPATH, ".//div[contains(@class,'html-div')]//span"
        )
        for node in text_nodes:
            t = node.text.strip()
            if not t:
                continue
            low = t.lower()
            if low in ["facebook", "see more"]:
                continue
            lines.append(t)
    except:
        pass

    # dedupe while keeping order
    clean = []
    for l in lines:
        if l not in clean:
            clean.append(l)

    return "\n".join(clean)


def find_metadata_container(story_message_element):
    """
    Find the parent container that has profile_name data.
    We need to go up from story_message to find the metadata section.
    """
    try:
        # Go up multiple levels to find the container with profile_name
        # Usually it's a few levels up from story_message
        current = story_message_element
        for _ in range(10):  # Try going up 10 levels max
            current = current.find_element(By.XPATH, "./..")
            try:
                # Check if this level has profile_name
                current.find_element(By.XPATH, ".//div[@data-ad-rendering-role='profile_name']")
                return current
            except:
                continue
    except:
        pass
    return None


def extract_posts(driver, seen_links):
    posts_data = []

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[@data-ad-rendering-role='story_message']"))
        )
    except TimeoutException:
        print("    ⚠️ No story_message elements found")
        return posts_data

    # Get all story_message containers (for content)
    story_message_cards = driver.find_elements(By.XPATH, "//*[@data-ad-rendering-role='story_message']")
    
    print(f"    Found {len(story_message_cards)} story_message elements")

    for idx, story_msg in enumerate(story_message_cards, 1):
        try:
            # Extract content from story_message
            content = extract_post_text_from_story_message(story_msg)
            if not content:
                print(f"    Post {idx}: No content, skipping")
                continue

            # Find the parent container that has metadata
            metadata_container = find_metadata_container(story_msg)
            if not metadata_container:
                print(f"    Post {idx}: Could not find metadata container, skipping")
                continue

            # Expand "See more" in the metadata container
            expand_see_more(metadata_container, driver)

            # Extract metadata
            author_name, author_link = extract_author(metadata_container)
            post_link = extract_post_link(story_msg)
            date_text = extract_date_from_post_link(driver, post_link)
            
            print(f"    Post {idx}: Author={author_name}, Date={date_text}, Link={post_link[:50] if post_link else 'None'}...")

            # Skip duplicates
            if post_link and post_link in seen_links:
                print(f"    Post {idx}: Duplicate, skipping")
                continue

            if post_link:
                seen_links.add(post_link)

            posts_data.append({
                "author_name": author_name,
                "author_link": author_link,
                "post_link": post_link,
                "date_posted": date_text,
                "content": content
            })

        except StaleElementReferenceException:
            print(f"    Post {idx}: Stale element, skipping")
            continue
        except Exception as e:
            print(f"    Post {idx}: Error - {e}")
            continue

    return posts_data


def save_to_csv(rows, filename):
    if not rows:
        print("⚠️ No posts to save.")
        return

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Saved {len(rows)} posts to {filename}")


def main():
    driver = setup_driver()

    try:
        manual_login(driver)
        all_posts = []
        seen_links = set()
        print("➡️ Opening target feed...")
        for group in TARGET_URL:
            print(f"Opening group: {group}")
            driver.get(group)
            time.sleep(5)

            

            for i in range(SCROLLS):
                print(f"\n🔄 Scroll {i+1}/{SCROLLS}")
                scroll_page(driver, 1)

                posts = extract_posts(driver, seen_links)
                all_posts.extend(posts)

                print(f"📦 Total unique posts collected: {len(all_posts)}")

        save_to_csv(all_posts, OUTPUT_FILE)

    finally:
        input("\nPress ENTER to close the browser...")
        driver.quit()


if __name__ == "__main__":
    main()