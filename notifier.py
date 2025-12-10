import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
from datetime import date, datetime
import urllib.parse
import requests
import time

# --- SETUP ---
SUPA_URL = os.environ["SUPABASE_URL"]
SUPA_KEY = os.environ["SUPABASE_SERVICE_KEY"] 
supabase = create_client(SUPA_URL, SUPA_KEY)

SMTP_USER = os.environ["EMAIL_USER"]
SMTP_PASS = os.environ["EMAIL_PASS"]
APP_URL = os.environ.get("APP_URL", "https://paticheck.streamlit.app") 

def clean_text(text):
    if not text: return ""
    return str(text).strip()

def send_alert(to_email, pet, vaccine, due_date, days_left):
    print(f"Sending to {to_email}...")
    
    pet_clean = clean_text(pet)
    vaccine_clean = clean_text(vaccine)
    
    # Calendar Link
    start = due_date.replace("-","") + "T090000"
    end = due_date.replace("-","") + "T091500"
    gcal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={pet_clean}-{vaccine_clean}&dates={start}/{end}&details=PatiCheck&sf=true&output=xml"
    
    # --- LOGIC: DYNAMIC URGENCY & TEXT ---
    if days_left < 0:
        urgency = "🚨"
        subject_prefix = "GECİKTİ"
        color = "#d32f2f" # Dark Red
        intro = f"Dikkat! {abs(days_left)} gün gecikti."
        status_label = f"{abs(days_left)} gün GEÇTİ"
        status_color = "red"
        
    elif days_left == 0:
        urgency = "⭐"
        subject_prefix = "BUGÜN"
        color = "#f57c00" # Orange
        intro = "Aşı günü geldi çattı!"
        status_label = "BUGÜN"
        status_color = "orange"
        
    elif days_left <= 3:
        urgency = "⚠️"
        subject_prefix = "AZ KALDI"
        color = "#e63946" # Soft Red
        intro = "Veteriner zamanı yaklaşıyor."
        status_label = f"{days_left} gün KALDI"
        status_color = "#e63946"
        
    else:
        urgency = "📅"
        subject_prefix = "HATIRLATMA"
        color = "#2a9d8f" # Teal
        intro = "Önümüzdeki hafta için hatırlatma."
        status_label = f"{days_left} gün KALDI"
        status_color = "#2a9d8f"

    msg = MIMEMultipart()
    msg['Subject'] = f"{urgency} {subject_prefix}: {pet_clean} - {vaccine_clean}"
    msg['From'] = f"PatiCheck <{SMTP_USER}>"
    msg['To'] = to_email
    
    html = f"""
    <div style="font-family: 'Helvetica', sans-serif; padding: 20px; color: #333; max-width: 500px; border: 1px solid #eee; border-radius: 10px;">
        <h2 style="color: {color}; margin-top: 0;">{urgency} {intro}</h2>
        <div style="background-color: #f9f9f9; padding: 15px; border-left: 5px solid {color}; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 5px 0; font-size: 18px;"><strong>🐾 {pet_clean}</strong></p>
            <p style="margin: 5px 0;">💉 <strong>İşlem:</strong> {vaccine_clean}</p>
            <p style="margin: 5px 0;">📅 <strong>Tarih:</strong> {due_date}</p>
            <p style="margin: 15px 0 5px 0; font-weight:bold; font-size: 16px; color: {status_color};">
                ⏳ Durum: {status_label}
            </p>
        </div>
        <a href="{gcal_link}" style="background-color:{color}; color:white; padding:12px 24px; text-decoration:none; border-radius:50px; font-weight:bold; display:inline-block;">
            📅 Takvime Ekle
        </a>
        <p style="margin-top: 30px; font-size: 11px; color: #999; border-top: 1px solid #eee; padding-top: 10px;">
            Bu mesaj PatiCheck asistanı tarafından otomatik gönderilmiştir.
        </p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, to_email, msg.as_string())
            print(f"Sent email to {to_email}")
        time.sleep(1)
    except Exception as e:
        print(f"Error sending to {to_email}: {e}")

# --- MAIN LOOP ---
today = date.today()
print(f"Checking vaccines for {today}...")

try:
    response = supabase.table("vaccinations").select("*, profiles(email)").execute()
    rows = response.data
except Exception as e:
    print(f"Database Error: {e}")
    rows = []

NOTIFY_DAYS = [7, 3, 1, 0, -3, -7]

for row in rows:
    try:
        due_str = row['next_due_date']
        due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        days_left = (due_date - today).days
        
        if days_left in NOTIFY_DAYS:
            if row['profiles'] and row['profiles'].get('email'):
                email = row['profiles']['email'] 
                send_alert(email, row['pet_name'], row['vaccine_type'], due_str, days_left)
            else:
                print(f"No email found for user {row['user_id']}")
    except Exception as e:
        print(f"Skipping row due to error: {e}")

# --- ROBUST WAKE UP CALL ---
# Tries 3 times with long timeouts to allow 'Cold Boot'
if APP_URL:
    print(f"Attempting to wake up {APP_URL}...")
    for i in range(3):
        try:
            # 60 second timeout gives Streamlit time to boot up
            r = requests.get(APP_URL, timeout=60)
            if r.status_code == 200:
                print(f"✅ App is awake! (Status: {r.status_code})")
                break
            else:
                print(f"⚠️ App returned status {r.status_code}. Retrying...")
        except Exception as e:
            print(f"⚠️ Wake up attempt {i+1} failed: {e}")
            time.sleep(5) # Wait 5s before retry
    else:
        print("❌ Failed to wake app after 3 attempts.")
