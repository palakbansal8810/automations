# WhatsApp Web Group Scraper (Selenium)

Scrapes messages from WhatsApp Web groups using Selenium and saves results to CSV.

## Requirements
- Google Chrome
- WhatsApp account (QR login)

## Setup
```bash
pip install selenium pandas webdriver-manager
````

## Configure Groups

Edit in the script:

```python
group_list = ["Group Name 1", "Group Name 2"]
```

## Run

```bash
python whatsapp_messages.py
```

## Output

* `whatsapp_messages.csv` – all messages
* `whatsapp_users.csv` – unique users

## Notes

* Scan QR on first run.
* Increase `num_scrolls` to fetch older messages.
* It takes time to sync messages from your phone, you can increase the  `num_scrolls`
