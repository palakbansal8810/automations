from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import pandas as pd
from selenium.webdriver.chrome.options import Options
import pyperclip

COUNTRY = "India"  # Country name
PHONE_NUMBER = "+918810447061"  # Just the number without country code
MESSAGE_TEXT = "Hello, Just wanted to connect."
CSV_FILE = "telegram_users.csv"
DELAY_BETWEEN_MESSAGES = (4, 10)


def send_message_with_js(driver, element, message):
    """Send message using JavaScript to support emojis"""
    try:
        driver.execute_script("""
            arguments[0].innerText = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        """, element, message)
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"JavaScript method failed: {e}")
        return False

def login_to_telegram(driver, phone_number):
    """Automate Telegram Web login"""
    try:
        print("\n🔐 Starting Telegram login process...")
        
        # Wait for the page to load
        time.sleep(5)
        
        # Step 1: Click "Log in by phone number"
        try:
            login_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary.btn-secondary"))
            )
            # Alternative selectors if the first one fails
            if not login_button:
                login_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary')]//span[contains(text(), 'Log in by phone number')]")
            
            login_button.click()
            print("✅ Clicked 'Log in by phone number'")
            time.sleep(7)
        except Exception as e:
            print(f"❌ Could not find login button: {e}")
            return False
        
        # Step 2: Enter phone number
        try:
            phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.input-field-phone .input-field-input[contenteditable='true']"))
        )
            
            # Clear existing content and enter phone number
            phone_input.click()
            time.sleep(2)
            
            # Use JavaScript to set the phone number
            driver.execute_script("""
                arguments[0].innerText = '';
            """, phone_input)
            time.sleep(0.5)
            
            driver.execute_script("""
                arguments[0].innerText = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            """, phone_input, phone_number)
            
            print(f"✅ Entered phone number: {phone_number}")
            time.sleep(2)
            
            # Press Enter or click Next button
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button//span[contains(text(), 'Next')]/ancestor::button"))
            )

            driver.execute_script("arguments[0].click();", next_button)
            print("✅ Clicked Next (JS)")
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Could not enter phone number: {e}")
            return False
        
        # Step 3: Wait for OTP and get it from user
        try:
            otp_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[inputmode='numeric'][autocomplete='one-time-code']"))
            )
            
            print("\n📱 OTP has been sent to your phone!")
            otp = input("Enter the OTP you received: ").strip()
            
            # Enter OTP
            otp_input.click()
            time.sleep(5)
            otp_input.send_keys(otp)
            
            print(f"✅ Entered OTP: {otp}")
            time.sleep(15)
            
            # Check if 2FA password is required
            try:
                password_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                )
                print("\n🔒 2FA Password required!")
                password = input("Enter your 2FA password: ").strip()
                password_input.send_keys(password)
                password_input.send_keys(Keys.RETURN)
                print("✅ Entered 2FA password")
                time.sleep(3)
            except TimeoutException:
                print("✅ No 2FA required")
            
            print("✅ Login successful!")
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"❌ Could not enter OTP: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def send_telegram_messages():
    # Setup Chrome driver
    options = Options()
    # options.add_argument("--user-data-dir=./telegram_profile")
    # options.add_argument("--headless")  # Don't use headless for login
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Open Telegram Web
        print("Opening Telegram Web (https://web.telegram.org/k/)...")
        driver.get("https://web.telegram.org/k/")
        time.sleep(5)
        
        # Check if already logged in
        try:
            # Look for search input (indicates logged in)
            search_input = driver.find_element(By.CSS_SELECTOR, "input.input-search")
            print("✅ Already logged in!")
        except NoSuchElementException:
            # Need to login
            print("⏳ Not logged in, starting login process...")
            if not login_to_telegram(driver, PHONE_NUMBER):
                print("❌ Login failed. Exiting...")
                return
        
        print("\n" + "="*50)
        print("Starting message automation...")
        print("="*50 + "\n")
        
        # Load users from CSV
        df = pd.read_csv(CSV_FILE)
        usernames = df['username'].tolist()
        
        print(f"Loaded {len(usernames)} users\n")
        
        for idx, username in enumerate(usernames, start=1):
            try:
                print(f"[{idx}/{len(usernames)}] Messaging @{username}")
                
                # Go to https://t.me/{username}
                driver.get(f"https://t.me/{username}")
                time.sleep(3)
                
                # Click "Open in Web" button
                try:
                    open_web_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.tgme_action_web_button, a.tgme_action_button_new.tgme_action_web_button"))
                    )
                    open_web_button.click()
                    print(f"✅ Clicked 'Open in Web' for @{username}")
                    time.sleep(5)
                    
                    # Switch to new tab if opened
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                    
                except TimeoutException:
                    print(f"❌ Could not find 'Open in Web' button for @{username}")
                    continue
                
                # Wait for message input and send message
                try:
                    message_input = None
                    selectors = [
                        "#editable-message-text",
                        "div[contenteditable='true']#editable-message-text",
                        "div.input-message-input[contenteditable='true']"
                    ]
                    
                    for selector in selectors:
                        try:
                            message_input = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            break
                        except:
                            continue
                    
                    if not message_input:
                        print(f"❌ Could not find message input for @{username}")
                        continue
                    
                    # Check for privacy restrictions
                    try:
                        privacy_elements = driver.find_elements(By.XPATH, 
                            "//*[contains(text(), 'privacy') or contains(text(), 'cannot') or contains(text(), 'restrict')]")
                        if privacy_elements:
                            print(f"❌ @{username} has privacy restrictions")
                            continue
                    except:
                        pass
                    
                    # Send message using JavaScript
                    if send_message_with_js(driver, message_input, MESSAGE_TEXT):
                        time.sleep(1)
                        message_input.send_keys(Keys.RETURN)
                        print(f"✅ Message sent to @{username}")
                    else:
                        print(f"❌ Could not send message to @{username}")
                        continue
                    
                except Exception as e:
                    print(f"❌ Error with message: {e}")
                    continue
                
                # Delay between messages
                if idx < len(usernames):
                    delay = random.randint(*DELAY_BETWEEN_MESSAGES)
                    print(f"⏳ Waiting {delay} seconds...\n")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"❌ Error with @{username}: {e}\n")
                continue
        
        print("\n✅ All messages sent!")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    send_telegram_messages()