import csv

MEMBERS_CSV = "leads.csv"
GROUPS_CSV = "telegram_groups_final.csv"
OUTPUT_CSV = "final_dedup_output.csv"

# Step 1: build group_url -> group_name map
group_map = {}

with open(GROUPS_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("telegram_link") and row.get("group_name"):
            group_map[row["telegram_link"]] = row["group_name"]

seen_users = set()
results = []

# Step 2: process members + deduplicate
with open(MEMBERS_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        member_url = (row.get("t_me_member_url") or "").strip().lower()
        group_url = (row.get("group_url") or "").strip()

        if not member_url or not group_url:
            continue

        # ❌ skip bots
        if "bot" in member_url:
            continue

        group_name = group_map.get(group_url)
        if not group_name:
            continue

        username = member_url.replace("https://t.me/", "").strip()
        if not username:
            continue

        # ❌ skip duplicate users (global dedup)
        if username in seen_users:
            continue

        seen_users.add(username)

        results.append({
            "group_name": group_name,
            "member_user_id": username
        })

# Step 3: save output (pipe-separated)
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="|")
    writer.writerow(["group_name", "member_user_id"])
    for r in results:
        writer.writerow([r["group_name"], r["member_user_id"]])

print(f"✅ Saved {len(results)} unique users to {OUTPUT_CSV}")
