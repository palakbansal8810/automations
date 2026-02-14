from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd
from selenium.webdriver.chrome.options import Options
import re

def wait_for_qr_scan(driver, timeout=60):
    """Wait for user to scan QR code"""
    print("📱 Please scan the QR code with your phone...")
    time.sleep(10)
    try:
        # Wait until chat list appears (means logged in)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox']"))
        )
        print("✅ Logged in successfully!")
        time.sleep(5)  # Wait a bit for everything to load
        return True
    except TimeoutException:
        print("❌ QR code scan timeout")
        return False

def open_group(driver, group_name):
    """Open a specific group chat"""
    try:
        print(f"🔍 Looking for group: {group_name}")
        
        # Click search
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']"))
        )
        search_box.click()
        time.sleep(1)
        
        # Clear any existing text
        search_box.clear()
        
        # Type group name
        search_box.send_keys(group_name)
        time.sleep(3)
        
        # Click first result
        first_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='gridcell']"))
        )
        first_result.click()
        
        print(f"✅ Opened group: {group_name}")
        time.sleep(15)  # Wait for messages to load
        return True
        
    except Exception as e:
        print(f"❌ Failed to open group: {e}")
        return False

def extract_single_message(msg, idx):
    """Extract data from a single message element"""
    try:
        # Determine if it's incoming or outgoing
        is_outgoing = 'message-out' in msg.get_attribute('class')
        
        # Extract sender name
        sender_name = "You" if is_outgoing else "Unknown"
            
        if not is_outgoing:
            try:
                # FIXED: Correct selector for sender name
                sender_elem = msg.find_element(By.CSS_SELECTOR, "span._ahx_[role='button']")
                sender_name = sender_elem.text.strip()
            except:
                try:
                    # Alternative: Look in the parent container
                    sender_elem = msg.find_element(By.CSS_SELECTOR, "div._ahxj._ahxz span._ahx_")
                    sender_name = sender_elem.text.strip()
                except:
                    try:
                        # Another fallback
                        sender_elem = msg.find_element(By.CSS_SELECTOR, "._ahxj ._ahx_")
                        sender_name = sender_elem.text.strip()
                        try:
                # Look for sender name in incoming messages
                            sender_elem = msg.find_element(By.CSS_SELECTOR, "span._ahxt")
                            sender_name = sender_elem.text.strip()
                        except:
                            try:
                                # Alternative selector for sender
                                sender_elem = msg.find_element(By.CSS_SELECTOR, "div._ahxj._ahxz.x78zum5.xijeqtt span._ahx_")
                                sender_name = sender_elem.text.strip()
                            except:
                                sender_name = "Unknown"
                    except:
                        sender_name = "Unknown"
        # Check if this message contains a quoted/replied message
        has_reply = False
        quoted_sender = ""
        quoted_text = ""
        
        try:
            # Look for the quoted message container
            quoted_container = msg.find_element(By.CSS_SELECTOR, "div._aju3[aria-label='Quoted message']")
            has_reply = True
            
            try:
                # Extract quoted sender name
                quoted_sender_elem = quoted_container.find_element(By.CSS_SELECTOR, "div._ahxj._ahxz.x78zum5.xijeqtt span._ahx_")
                quoted_sender = quoted_sender_elem.text.strip()
            except:
                try:
                    # Try alternate selector
                    quoted_sender_elem = quoted_container.find_element(By.CSS_SELECTOR, "div._ahxj span._ao3e")
                    quoted_sender = quoted_sender_elem.text.strip()
                except:
                    quoted_sender = "Unknown"
            
            try:
                # Extract quoted message text
                quoted_text_elem = quoted_container.find_element(By.CSS_SELECTOR, "span.quoted-mention._ao3e._aupe.copyable-text")
                quoted_text = quoted_text_elem.text.strip()
            except:
                try:
                    # Alternative selector for quoted text
                    quoted_text_elem = quoted_container.find_element(By.CSS_SELECTOR, "div.x104kibb span.copyable-text")
                    quoted_text = quoted_text_elem.text.strip()
                except:
                    quoted_text = ""
        except:
            # No quoted message found
            pass
        
        # Extract the ACTUAL message text (not the quoted part)
        message_text = ""
        try:
            # The actual message is in the div._akbu container
            actual_msg_container = msg.find_element(By.CSS_SELECTOR, "div._akbu")
            
            # Get the text from the actual message span
            text_elem = actual_msg_container.find_element(By.CSS_SELECTOR, "span.copyable-text")
            message_text = text_elem.text.strip()
        except:
            try:
                # Fallback: try to get any copyable-text that's NOT inside the quoted container
                all_text_spans = msg.find_elements(By.CSS_SELECTOR, "span[data-testid='selectable-text'].copyable-text")
                
                # If there's a reply, the first span is the quoted text, second is actual message
                if has_reply and len(all_text_spans) > 1:
                    message_text = all_text_spans[-1].text.strip()  # Take the last one (actual message)
                elif all_text_spans:
                    message_text = all_text_spans[0].text.strip()
            except:
                pass
        
        # Extract timestamp and date
        timestamp = ""
        date = ""
        full_datetime = ""
        
        try:
            # Try to get the full timestamp from data-pre-plain-text attribute
            copyable_text_div = msg.find_element(By.CSS_SELECTOR, "div.copyable-text[data-pre-plain-text]")
            pre_plain_text = copyable_text_div.get_attribute("data-pre-plain-text")
            
            if pre_plain_text:
                # Extract datetime from format: [6:05 PM, 2/4/2026]
                datetime_match = re.search(r'\[(.*?)\]', pre_plain_text)
                if datetime_match:
                    full_datetime = datetime_match.group(1).strip()
                    
                    # Split into time and date
                    parts = full_datetime.split(', ')
                    if len(parts) == 2:
                        timestamp = parts[0].strip()  # e.g., "6:05 PM"
                        date = parts[1].strip()  # e.g., "2/4/2026"
        except:
            pass
        
        # Fallback: Try to get just the time from visible elements
        if not timestamp:
            try:
                time_elem = msg.find_element(By.CSS_SELECTOR, "span.x1c4vz4f.x2lah0s")
                timestamp = time_elem.text.strip()
            except:
                try:
                    # Alternative time selector
                    time_elem = msg.find_element(By.CSS_SELECTOR, "span.x193iq5w")
                    timestamp = time_elem.text.strip()
                except:
                    pass
        
        # Only return if there's actual message text
        if message_text and len(message_text) > 0:
            # Clean the message
            cleaned_message = re.sub(r'\s+', ' ', message_text)
            
            # Create unique identifier for deduplication
            message_id = f"{sender_name}_{full_datetime}_{cleaned_message[:50]}"
            
            message_entry = {
                'message_id': message_id,
                'sender': sender_name,
                'message': cleaned_message,
                'date': date,
                'timestamp': timestamp,
                'full_datetime': full_datetime,
                'type': 'outgoing' if is_outgoing else 'incoming',
                'is_reply': has_reply,
                'quoted_sender': quoted_sender if has_reply else '',
                'quoted_text': quoted_text if has_reply else ''
            }
            
            return message_entry
        
        return None
        
    except Exception as e:
        # Silently skip messages that can't be extracted
        return None

def extract_and_scroll(driver, num_scrolls=50):
    """Extract messages incrementally while scrolling"""
    print(f"📜 Starting incremental extraction with {num_scrolls} scrolls...")
    
    all_messages = {}  # Use dict to avoid duplicates (key = message_id)
    
    try:
        # Find message container
        message_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.x10l6tqk.x13vifvy[data-scrolltracepolicy='wa.web.conversation.messages']"))
        )
        
        for scroll_num in range(num_scrolls):
            print(f"\n🔄 Scroll {scroll_num + 1}/{num_scrolls}")
            
            # First, extract messages currently visible
            print("  📥 Extracting visible messages...")
            try:
                messages = driver.find_elements(By.CSS_SELECTOR, "div.message-in, div.message-out")
                
                extracted_count = 0
                for idx, msg in enumerate(messages):
                    message_data = extract_single_message(msg, idx)
                    if message_data:
                        msg_id = message_data['message_id']
                        if msg_id not in all_messages:
                            all_messages[msg_id] = message_data
                            extracted_count += 1
                
                print(f"  ✅ Extracted {extracted_count} new messages (Total unique: {len(all_messages)})")
                
            except Exception as e:
                print(f"  ⚠️ Extraction error: {e}")
            
            # Then scroll up to load more
            if scroll_num < num_scrolls - 1:  # Don't scroll after last extraction
                print("  ⬆️ Scrolling up...")
                driver.execute_script("arguments[0].scrollTop = 0", message_container)
                time.sleep(2)  # Wait for new messages to load
        
        # Final extraction after all scrolling
        print(f"\n🔍 Final extraction pass...")
        try:
            messages = driver.find_elements(By.CSS_SELECTOR, "div.message-in, div.message-out")
            
            extracted_count = 0
            for idx, msg in enumerate(messages):
                message_data = extract_single_message(msg, idx)
                if message_data:
                    msg_id = message_data['message_id']
                    if msg_id not in all_messages:
                        all_messages[msg_id] = message_data
                        extracted_count += 1
            
            print(f"✅ Final pass extracted {extracted_count} new messages")
            
        except Exception as e:
            print(f"⚠️ Final extraction error: {e}")
        
        print(f"\n✅ Finished! Total unique messages: {len(all_messages)}")
        
        # Convert dict to list
        return list(all_messages.values())
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return list(all_messages.values())


def main():
    # Setup Chrome
    options = Options()
    # Uncomment to use saved session
    # options.add_argument("--user-data-dir=./whatsapp_profile")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Open WhatsApp Web
        print("🌐 Opening WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        # Wait for QR scan
        if not wait_for_qr_scan(driver):
            return
        
        # Group name to extract from
        group_name = "PromoPe AI automation intern"
        
        # Open the group
        if open_group(driver, group_name):
            # Extract messages incrementally while scrolling
            messages = extract_and_scroll(driver, num_scrolls=50)
            
            # Save to CSV
            if messages:
                df = pd.DataFrame(messages)
                
                # Remove the message_id column before saving (it was just for deduplication)
                df = df.drop('message_id', axis=1)
                
                # Sort by datetime if available
                if len(df[df['full_datetime'] != '']) > 0:
                    # Create a sortable datetime column
                    df['sort_key'] = pd.to_datetime(df['full_datetime'], format='%I:%M %p, %m/%d/%Y', errors='coerce')
                    df = df.sort_values('sort_key', na_position='first')
                    df = df.drop('sort_key', axis=1)
                
                df.to_csv('whatsapp_messages.csv', index=False, encoding='utf-8')
                print(f"\n✅ Saved {len(messages)} messages to whatsapp_messages.csv")
                
                # Show some sample messages with replies
                if len(df[df['is_reply'] == True]) > 0:
                    print("\n📝 Sample messages with replies:")
                    reply_messages = df[df['is_reply'] == True].head(3)
                    for _, row in reply_messages.iterrows():
                        print(f"\n[{row['full_datetime']}] {row['sender']} replied to {row['quoted_sender']}:")
                        print(f"  Quoted: '{row['quoted_text'][:100]}...'")
                        print(f"  Reply: '{row['message'][:100]}...'")
                
                # Extract unique senders (excluding "You")
                users_df = df[df['sender'] != 'You'][['sender']].drop_duplicates()
                users_df.to_csv('whatsapp_users.csv', index=False, encoding='utf-8')
                print(f"\n✅ Found {len(users_df)} unique users (excluding you)")
                
                # Show summary
                print(f"\n📊 Summary:")
                print(f"Total messages: {len(messages)}")
                print(f"Your messages: {len(df[df['type'] == 'outgoing'])}")
                print(f"Others' messages: {len(df[df['type'] == 'incoming'])}")
                print(f"Messages with replies: {len(df[df['is_reply'] == True])}")
                print(f"Messages with date info: {len(df[df['date'] != ''])}")
                
                # Show date range if available
                dates_available = df[df['date'] != '']['date'].unique()
                if len(dates_available) > 0:
                    print(f"Date range: {dates_available[0]} to {dates_available[-1]}")
                
                print(f"\nTop 5 most active users:")
                print(df[df['sender'] != 'You']['sender'].value_counts().head())
                
                # Show sample messages with full datetime
                if len(df[df['full_datetime'] != '']) > 0:
                    print("\n📅 Sample messages with date/time:")
                    sample_with_date = df[df['full_datetime'] != ''].head(3)
                    for _, row in sample_with_date.iterrows():
                        print(f"  [{row['full_datetime']}] {row['sender']}: {row['message'][:100]}...")
            else:
                print("\n❌ No messages extracted")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    main()
    