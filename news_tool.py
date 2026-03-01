import requests
import smtplib
import schedule
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from openai import OpenAI

# ── Configuration ────────────────────────────────────────────────────────────
NEWS_API_KEY   = "YOUR_NEWS_API_KEY"       # from newsapi.org
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"     # from platform.openai.com
EMAIL_ADDRESS  = "yamanm17034@gmail.com"
EMAIL_PASSWORD = "YOUR_GMAIL_APP_PASSWORD" # Gmail App Password (not your login password)

TOPICS = [
    "university admissions US UK Europe",
    "bachelors masters degree higher education",
    "university rankings tuition fees",
    "student visa UK US Europe",
    "higher education policy university funding",
]

# ── Fetch News ────────────────────────────────────────────────────────────────
def fetch_news():
    articles = []
    url = "https://newsapi.org/v2/everything"
    for topic in TOPICS:
        params = {
            "q": topic,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 5,
            "apiKey": NEWS_API_KEY,
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            articles.extend(data.get("articles", []))

    # Remove duplicates by title
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    return unique[:20]  # Return top 20 articles

# ── Summarize with AI ─────────────────────────────────────────────────────────
def summarize_news(articles):
    client = OpenAI(api_key=OPENAI_API_KEY)

    headlines = "\n".join(
        [f"- {a['title']} ({a['source']['name']}): {a['description']}"
         for a in articles if a.get("title") and a.get("description")]
    )

    prompt = f"""You are an education industry analyst.
Summarize the following news articles about higher education (bachelors & masters) in the US, UK, and Europe.
Write a clear, concise daily briefing with the most important developments.
Group by theme (e.g. Admissions, Policy, Rankings, Visas, Funding).
Keep it professional but easy to read.

Articles:
{headlines}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# ── Send Email ────────────────────────────────────────────────────────────────
def send_email(summary):
    today = datetime.now().strftime("%B %d, %Y")
    subject = f"Education News Briefing — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_ADDRESS
    msg["To"]      = EMAIL_ADDRESS

    # Plain text version
    text_body = f"Education News Briefing — {today}\n\n{summary}"

    # HTML version
    html_body = f"""
    <html><body>
    <h2 style="color:#2c3e50;">Education News Briefing — {today}</h2>
    <p style="font-family:Arial; font-size:15px; line-height:1.6; color:#333;">
        {summary.replace(chr(10), '<br>')}
    </p>
    <hr>
    <p style="font-size:12px; color:#999;">
        Automated briefing covering higher education in the US, UK & Europe.
    </p>
    </body></html>
    """

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg.as_string())

    print(f"[{datetime.now()}] Email sent successfully!")

# ── Main Job ──────────────────────────────────────────────────────────────────
def run_daily_briefing():
    print(f"[{datetime.now()}] Fetching education news...")
    articles = fetch_news()
    if not articles:
        print("No articles found.")
        return
    print(f"Found {len(articles)} articles. Summarizing...")
    summary = summarize_news(articles)
    print("Sending email...")
    send_email(summary)

# ── Scheduler (10:00 AM UAE = 06:00 UTC) ─────────────────────────────────────
schedule.every().day.at("06:00").do(run_daily_briefing)

if __name__ == "__main__":
    print("Education News Tool started. Waiting for 10:00 AM UAE time...")
    print("Press Ctrl+C to stop.")
    # Run immediately on start to test
    run_daily_briefing()
    while True:
        schedule.run_pending()
        time.sleep(60)
