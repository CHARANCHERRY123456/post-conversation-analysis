import schedule, time, django, os
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'post_analysis_main.settings')
django.setup()

from analysis_app.cron import run_daily_analysis 

def job():
    print(f"Running analysis at {datetime.now()}")
    run_daily_analysis()

schedule.every().day.at("00:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
