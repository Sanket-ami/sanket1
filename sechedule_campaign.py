import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import time, os
from dotenv import load_dotenv

load_dotenv('/home/deep/django-monogodb/callbotics_revamp/zono/.env')
connection_params = {
    "host": "localhost",       # or your database host
    "port": 5432,              # default port for PostgreSQL
    "dbname": os.getenv('DB_NAME'),  # replace with your database name
    "user": os.getenv('DB_USER'),    # replace with your username
    "password": os.getenv('DB_PASSWORD') # replace with your password
}
conn = psycopg2.connect(**connection_params, cursor_factory=RealDictCursor)
cursor = conn.cursor()
sehedule_query = """  SELECT * FROM campaign_schedulecampaign WHERE is_ongoing = False AND is_finished = False AND schedule_date <= now()  """

while True:
    cursor.execute(sehedule_query)
    sehedule_data = cursor.fetchall()
    for campaign in sehedule_data:
        campaign_query = f""" SELECT * FROM  campaign_campaign WHERE id = {campaign['campaign_id']} """
        cursor.execute(campaign_query)
        campaign_data = cursor.fetchone()
        url = f"http://127.0.0.1:8000/content/start_campaign_secheduler?token={os.getenv('SECHEDULE_CAMPAIGN_TOKEN')}&campaign_id={campaign['campaign_id']}"
        response = requests.request("GET", url)
        time.sleep(10)
        print(response.text)


