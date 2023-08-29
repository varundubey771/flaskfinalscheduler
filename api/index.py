# -*- coding: utf-8 -*-
import os
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import re
import datetime

load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_DATABASE")

def writer(data):
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )
    cursor = connection.cursor(dictionary=True)
    insert_query = "INSERT INTO JobCount (country, count, title, timestamp) VALUES (%s, %s, %s, %s)"
    try:
        cursor.executemany(insert_query,data)
        connection.commit()
        print(cursor.rowcount, "rows inserted.")
    except mysql.connector.Error as err:
        print("Error:", err)
        connection.rollback()
    cursor.close()
    connection.close()
    return 0

def scrape_jobs(country,jobTitle):
    url = f"https://www.linkedin.com/jobs/search/?keywords={jobTitle}&location={country}"

    headers = {
        "User-Agent": "Your User Agent String"
        # Add any other headers you might need
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        job_count_elem = soup.find("code", {"id": "totalResults"})
        if job_count_elem:
            job_count_comment = str(job_count_elem)
            job_count = re.search(r"<!--(\d+)-->", job_count_comment).group(1)
            return job_count
        else:
            return "N/A"
    else:
        return "N/A"

# Initial Flask app
app = Flask(__name__)

@app.route('/')
def home():
   return 'Hello, what did you have for breakfast?'

@app.route('/getJobData')
def getJobData():
   countries = ["Australia","India","United Kingdom","United States","Ireland"]
   jobs = ["Python", "Java"]
   lst=[]
   for country in countries:
       for job in jobs:
           job_count = scrape_jobs(country,job)
           lst.append({"country": country,"job_count":job_count,"job":job})
   return lst

@app.route('/sendJobDataCron')
def sendJobDataCron():
   countries = ["Australia"]
   jobs = ["Python", "Java"]
   lst=[]
   print(countries)
   print(jobs)
   current_datetime = datetime.datetime.now()
   str_cur_dt= current_datetime.strftime("%Y-%m-%d %H:%M:%S")
   parsed_datetime = datetime.datetime.strptime(str_cur_dt, "%Y-%m-%d %H:%M:%S")
   for country in countries:
       for job in jobs:
           job_count = int(scrape_jobs(country,job))
           lst.append((country, job_count, job,parsed_datetime))
   print(lst)
   resp = (writer(lst))
   return lst
