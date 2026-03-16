import requests
from bs4 import BeautifulSoup
import time
import json

BOT_TOKEN = "8644838935:AAHCnQk96pNv-EFTqwsRL4LBTC2XzzvFGCQ"
CHAT_ID = "8040018117"

search_urls = {
    "LinkedIn Hamburg": "https://www.linkedin.com/jobs/search/?keywords=quality%20manager%20OR%20quality%20engineer%20OR%20qualit%C3%A4tsmanager%20OR%20qualit%C3%A4tsingenieur%20OR%20continuous%20improvement&location=Hamburg%2C%20Germany&f_TPR=r28800",
    "LinkedIn Remote": "https://www.linkedin.com/jobs/search/?keywords=quality%20manager%20OR%20quality%20engineer%20OR%20qualit%C3%A4tsmanager%20OR%20qualit%C3%A4tsingenieur%20OR%20continuous%20improvement&location=Germany&f_WT=2&f_TPR=r28800",
    "Stepstone": "https://www.stepstone.de/jobs/quality/in-22525-hamburg?radius=10&searchOrigin=Resultlist_top-search"
}

keywords = ["quality", "qualitäts", "iso", "continuous improvement", "operational excellence", "process improvement", "ISO 9001"]
exclude_keywords = ["software", "qa tester", "automation tester", "selenium", "javascript", "developer", "software engineer", "test engineer"]

def load_sent_jobs():
    try:
        with open("sent_jobs.json", "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_sent_jobs(sent_jobs):
    with open("sent_jobs.json", "w") as f:
        json.dump(list(sent_jobs), f)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text,
            "disable_web_page_preview": True
        }, timeout=10)
    except Exception as e:
        print(f"Telegram send failed: {e}")

sent_jobs = load_sent_jobs()

def scan_jobs():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    for site, url in search_urls.items():
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"[{site}] HTTP {r.status_code} — skipping")
                time.sleep(30)  # back off on errors
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            jobs = soup.select("a.base-card__full-link")
            print(f"[{site}] Found {len(jobs)} job elements")  # helpful for Railway logs

            for job in jobs:
                title = job.text.strip()
                href = job.get("href", "")
                job_id = f"{title}_{href}".lower()
                title_lower = title.lower()

                if any(k in title_lower for k in keywords) and not any(x in title_lower for x in exclude_keywords):
                    if job_id not in sent_jobs:
                        sent_jobs.add(job_id)
                        if len(sent_jobs) > 2000:
                            sent_jobs.pop()  # still random but non-critical
                        save_sent_jobs(sent_jobs)
                        message = f"🆕 {site}\n\n{title}\n{href}"
                        send_telegram(message)

        except Exception as e:
            print(f"[{site}] Error: {e}")
            send_telegram(f"⚠️ Bot error on {site}:\n{e}")

        time.sleep(10)  # slightly longer delay between sites

while True:
    try:
        scan_jobs()
    except Exception as e:
        print(f"Outer loop error: {e}")
        send_telegram(f"⚠️ Bot crashed and restarted:\n{e}")
    time.sleep(900)
