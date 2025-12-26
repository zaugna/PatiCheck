import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
from datetime import date, datetime
import urllib.parse
import requests
import time

# --- 1. WAKE UP CALL (PRIORITY) ---
# We do this FIRST so the app wakes up immediately, 
# even if the database logic below hits a snag.
APP_URL = os.environ.get("APP_URL", "https://paticheck.streamlit.app")
print(f"Pinging {APP_URL}...")
try:
    requests.get(APP_URL, timeout=10)
    print("✅ Ping success. App is awake.")
except Exception as e:
    print(f"⚠️ Ping failed: {e}")

# --- 2. SETUP ---
try:
    SUPA_URL = os.environ["SUPABASE_URL"]
    # This must be the SERVICE_ROLE key to bypass RLS
    SUPA_KEY = os.environ["SUPABASE_SERVICE_KEY"] 
    supabase = create_client(SUPA_URL, SUPA_KEY)

    SMTP_USER = os.environ["EMAIL_USER"]
    SMTP_PASS = os.environ["EMAIL_PASS"]
except KeyError as e:
    print(f"❌ Missing Secret: {e}")
    exit(1)

def clean_text(text):
    if not text: return ""
    return str(text).strip()

def send_alert(to_email, name, pet, vaccine, due_date, days_left):
    print(f"🚀 Sending to {to_email}...")
    
    pet_clean = clean_text(pet)
    vaccine_clean = clean_text(vaccine)
    greeting = f"Merhaba {name}," if name else "Merhaba / Hello,"
    
    # Calendar Link
    start = due_date.replace("-","") + "T090000"
    end = due_date.replace("-","") + "T091500"
    gcal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={pet_clean}-{vaccine_clean}&dates={start}/{end}&details=PatiCheck&sf=true&output=xml"
    
    # Logic
    if days_
