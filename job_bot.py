import requests
from bs4 import BeautifulSoup
import time
import json
def load_sent_jobs():
    sent_jobs = load_sent_jobs()

def save_sent_jobs(sent_jobs):
    with open("sent_jobs.json", "w") as f:
        json.dump(list(sent_jobs), f)

BOT_TOKEN = "8644838935:AAHCnQk96pNv-EFTqwsRL4LBTC2XzzvFGCQ"
CHAT_ID = "8040018117"

search_urls = {

"LinkedIn Hamburg": "https://www.linkedin.com/jobs/search/?keywords=quality%20manager%20OR%20quality%20engineer%20OR%20qualit%C3%A4tsmanager%20OR%20qualit%C3%A4tsingenieur%20OR%20continuous%20improvement&location=Hamburg%2C%20Germany&f_TPR=r28800",

"LinkedIn Remote": "https://www.linkedin.com/jobs/search/?keywords=quality%20manager%20OR%20quality%20engineer%20OR%20qualit%C3%A4tsmanager%20OR%20qualit%C3%A4tsingenieur%20OR%20continuous%20improvement&location=Germany&f_WT=2&f_TPR=r28800",
    
"Stepstone" "https://www.stepstone.de/jobs/quality/in-22525-hamburg?radius=10&searchOrigin=Resultlist_top-search"
    
}

keywords = [
"quality",
"qualitäts",
"iso",
"continuous improvement",
"operational excellence",
"process improvement",
"ISO 9001"
]

exclude_keywords = [
"software",
"qa tester",
"automation tester",
"selenium",
"javascript",
"developer",
"software engineer",
"test engineer"
]

try:
    with open("sent_jobs.json", "r") as f:
        sent_jobs = set(json.load(f))
except:
    sent_jobs = set()

def send_telegram(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })

def scan_jobs():

    headers = {"User-Agent": "Mozilla/5.0"}

    for site, url in search_urls.items():

        r = requests.get(url, headers=headers)

        soup = BeautifulSoup(r.text, "html.parser")

        jobs = soup.select("a.base-card__full-link")

        for job in jobs:

            title = job.text.strip()
            href = job["href"]
            job_id = href.split("/")[-1].split("?")[0]

            title_lower = title.lower()

            if any(k in title_lower for k in keywords) and not any(x in title_lower for x in exclude_keywords):

                if job_id not in sent_jobs:

                    sent_jobs.add(job_id)
                    save_sent_jobs(sent_jobs)

                    with open("sent_jobs.json", "w") as f:
                        json.dump(list(sent_jobs), f)

                    message = f"{site} job\n\n{title}\n{href}"

                    send_telegram(message)

while True:

    scan_jobs()


    time.sleep(900)




