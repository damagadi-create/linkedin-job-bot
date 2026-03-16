import requests
from bs4 import BeautifulSoup
import time
import json

BOT_TOKEN = "8644838935:AAHCnQk96pNv-EFTqwsRL4LBTC2XzzvFGCQ"
CHAT_ID = "8040018117"

search_urls = {
    "LinkedIn Hamburg": "https://www.linkedin.com/jobs/search/?keywords=quality%20manager%20OR%20quality%20engineer%20OR%20qualit%C3%A4tsmanager%20OR%20qualit%C3%A4tsingenieur%20OR%20continuous%20improvement&location=Hamburg%2C%20Germany&f_TPR=r28800",
    "LinkedIn Remote": "https://www.linkedin.com/jobs/search/?keywords=quality%20manager%20OR%20quality%20engineer%20OR%20qualit%C3%A4tsmanager%20OR%20qualit%C3%A4tsingenieur%20OR%20continuous%20improvement&location=Germany&f_WT=2&f_TPR=r28800",
    "Stepstone": "https://www.stepstone.de/jobs/quality-manager/in-hamburg?radius=30&searchOrigin=Resultlist_top-search",
    "Xing": "https://www.xing.com/jobs/search?keywords=quality+manager+OR+quality+engineer+OR+qualit%C3%A4tsmanager&location=Hamburg&radius=30"
}

keywords = [
    "quality", "qualitäts", "iso", "continuous improvement",
    "operational excellence", "process improvement", "iso 9001",
    "qualitätsmanager", "qualitätsingenieur", "lean", "six sigma"
]
exclude_keywords = [
    "software", "qa tester", "automation tester", "selenium",
    "javascript", "developer", "software engineer", "test engineer",
    "frontend", "backend", "devops"
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

def scrape_stepstone(soup, site):
    """Stepstone job cards — title in data-testid or class selectors"""
    jobs = []
    # Try multiple selectors for resilience
    for card in soup.select("article[data-testid='job-item'], .ResultItem, [class*='JobCard']"):
        title_tag = (
            card.select_one("[data-testid='job-item-title']") or
            card.select_one("h2 a") or
            card.select_one("a[class*='title']") or
            card.select_one("a")
        )
        if not title_tag:
            continue
        title = title_tag.text.strip()
        href = title_tag.get("href", "")
        if href and not href.startswith("http"):
            href = "https://www.stepstone.de" + href
        if title and href:
            jobs.append((title, href))
    print(f"[{site}] Found {len(jobs)} jobs")
    return jobs

def scrape_xing(soup, site):
    """Xing job listings"""
    jobs = []
    for card in soup.select("[data-testid='job-posting-title'], .job-posting-title, [class*='JobPosting'] a, [class*='job-result'] a"):
        title = card.text.strip()
        href = card.get("href", "")
        if href and not href.startswith("http"):
            href = "https://www.xing.com" + href
        if title and href:
            jobs.append((title, href))
    print(f"[{site}] Found {len(jobs)} jobs")
    return jobs

SCRAPERS = {
    "LinkedIn Hamburg": scrape_linkedin,
    "LinkedIn Remote": scrape_linkedin,
    "Stepstone": scrape_stepstone,
    "Xing": scrape_xing,
}

SITE_EMOJI = {
    "LinkedIn Hamburg": "💼",
    "LinkedIn Remote": "🌍",
    "Stepstone": "🟧",
    "Xing": "🔵",
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
                    any(k in title_lower for k in keywords)
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

while True:
    try:
        scan_jobs()
    except Exception as e:
        print(f"Outer loop error: {e}")
        send_telegram(f"⚠️ Bot crashed and restarted:\n<code>{e}</code>")
    time.sleep(900)
