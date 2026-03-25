import requests
from bs4 import BeautifulSoup
import time
import json

BOT_TOKEN = "7965984943:AAF1b6ORfIhwJkL9ACf7qWfYckX4dbwBqqU"
CHAT_ID = "806465871"

search_urls = {
    "LinkedIn Hamburg": "https://www.linkedin.com/jobs/search/?keywords=Senior%20Counsel%20OR%20Commercial%20Counsel%20OR%20Legal%20Counsel&location=Hamburg%2C%20Germany&f_TPR=r86400",
    
    "LinkedIn USA Remote": "https://www.linkedin.com/jobs/search/?keywords=Senior%20Counsel%20OR%20Commercial%20Counsel%20OR%20Legal%20Counsel&location=United%20States&f_WT=2&f_TPR=r86400",
}

keywords = [
    "senior counsel", "commercial counsel", "legal counsel",
    "msa", "rfp", "nda", "mro", "oem",
    "saas", "licensing", "contracts", "sales",
    "ai governance", "negotiation"
]

exclude_keywords = [
    "junior", "assistant", "paralegal", "intern",
    "working student", "werkstudent",
    "software engineer", "developer", "qa", "tester"
]

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
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=10)
    except Exception as e:
        print(f"Telegram send failed: {e}")

def scrape_linkedin(soup, site):
    """LinkedIn uses anchor tags with class base-card__full-link"""
    jobs = []
    for tag in soup.select("a.base-card__full-link"):
        title = tag.text.strip()
        href = tag.get("href", "").split("?")[0]  # strip tracking params
        if title and href:
            jobs.append((title, href))
    print(f"[{site}] Found {len(jobs)} jobs")
    return jobs

SCRAPERS = {
    "LinkedIn Miami": scrape_linkedin,
    "LinkedIn Remote": scrape_linkedin,
    }

SITE_EMOJI = {
    "LinkedIn Miami": "💼",
    "LinkedIn Remote": "🌍",
  }

sent_jobs = load_sent_jobs()

def scan_jobs():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    for site, url in search_urls.items():
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"[{site}] HTTP {r.status_code} — skipping")
                time.sleep(30)
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            scraper_fn = SCRAPERS[site]
            jobs = scraper_fn(soup, site)

            if not jobs:
                print(f"[{site}] No jobs parsed — site structure may have changed")

            for title, href in jobs:
                title_lower = title.lower()
                job_id = f"{title_lower}_{href}"

                if (
                    any(k in title_lower for k in ["counsel", "legal"])
                    and not any(x in title_lower for x in exclude_keywords)
                    and job_id not in sent_jobs
                ):
                    sent_jobs.add(job_id)
                    if len(sent_jobs) > 2000:
                        oldest = next(iter(sent_jobs))  # remove oldest (insertion order)
                        sent_jobs.discard(oldest)
                    save_sent_jobs(sent_jobs)

                    emoji = SITE_EMOJI.get(site, "📌")
                    message = f"{emoji} <b>{site}</b>\n\n{title}\n{href}"
                    send_telegram(message)
                    print(f"[{site}] Sent: {title}")

        except Exception as e:
            print(f"[{site}] Error: {e}")
            send_telegram(f"⚠️ Bot error on <b>{site}</b>:\n{e}")

        time.sleep(10)

if __name__ == "__main__":
    scan_jobs()
