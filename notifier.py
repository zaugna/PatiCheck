import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
from datetime import date, datetime
import requests
import time

# --- 1. WAKE UP CALL (PRIORITY) ---
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
    if days_left < 0:
        color = "#D93025" 
        bg_color = "#FCE8E6"
        header_tr, header_en = "GECİKTİ", "OVERDUE"
        status_tr = f"{abs(days_left)} gün geçti"
        status_en = f"{abs(days_left)} days overdue"
        intro_tr = "Bu aşı tarihi geçmiş durumda."
        intro_en = "This vaccination is past due."
    elif days_left == 0:
        color = "#F9AB00"
        bg_color = "#FEF7E0"
        header_tr, header_en = "BUGÜN", "TODAY"
        status_tr, status_en = "Bugün Yapılmalı", "Due Today"
        intro_tr = "Aşı günü geldi çattı!"
        intro_en = "Vaccination day is here!"
    elif days_left <= 3:
        color = "#E37400"
        bg_color = "#FFF3E0"
        header_tr, header_en = "AZ KALDI", "SOON"
        status_tr = f"{days_left} gün kaldı"
        status_en = f"{days_left} days left"
        intro_tr = "Veteriner zamanı yaklaşıyor."
        intro_en = "Vet time is approaching."
    else:
        color = "#188038"
        bg_color = "#E6F4EA"
        header_tr, header_en = "HATIRLATMA", "REMINDER"
        status_tr = f"{days_left} gün kaldı"
        status_en = f"{days_left} days left"
        intro_tr = "Önümüzdeki hafta için hatırlatma."
        intro_en = "Reminder for the upcoming week."

    msg = MIMEMultipart()
    msg['Subject'] = f"PatiCheck: {pet_clean} - {vaccine_clean}"
    msg['From'] = f"PatiCheck <{SMTP_USER}>"
    msg['To'] = to_email
    
    html = f"""
    <div style="font-family: Helvetica, Arial, sans-serif; max-width: 500px; margin: 0 auto; color: #333;">
        <div style="border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden;">
            <div style="background-color: {color}; padding: 15px; text-align: center; color: white;">
                <h3 style="margin:0;">{header_tr} | {header_en}</h3>
            </div>
            <div style="padding: 25px; background-color: #ffffff;">
                <p>{greeting}</p>
                <div style="text-align: center; margin: 25px 0;">
                    <div style="font-size: 28px; font-weight: 900;">{pet_clean}</div>
                    <div style="font-size: 20px; color: #555;">{vaccine_clean}</div>
                </div>
                <div style="background-color: {bg_color}; border-radius: 8px; padding: 15px; text-align: center;">
                    <div style="font-weight: bold; color: {color};">{status_tr}</div>
                    <div style="font-size: 12px; color: #666;">{status_en}</div>
                    <div style="margin-top:5px; font-weight:bold; color:#333;">{due_date}</div>
                </div>
                <div style="text-align: center; margin-top: 25px;">
                    <a href="{gcal_link}" style="background-color: {color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px;">📅 Takvime Ekle / Add to Calendar</a>
                </div>
            </div>
        </div>
        <p style="text-align: center; font-size: 11px; color: #aaa; margin-top: 20px;"><a href="{APP_URL}" style="color: #aaa;">PatiCheck App</a></p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, to_email, msg.as_string())
            print(f"✅ Sent email to {to_email}")
        time.sleep(1)
    except Exception as e:
        print(f"❌ Error sending to {to_email}: {e}")

# --- 3. MAIN LOOP ---
today = date.today()
print(f"Checking vaccines for {today}...")

try:
    response = supabase.table("vaccinations").select("*, profiles(email, full_name, secondary_email)").execute()
    rows = response.data
except Exception as e:
    print(f"❌ Database Error: {e}")
    rows = []

NOTIFY_DAYS = [7, 3, 1, 0, -3, -7]

sent_count = 0

for row in rows:
    try:
        due_str = row['next_due_date']
        due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        days_left = (due_date - today).days
        
        if days_left in NOTIFY_DAYS:
            if row.get('profiles') and row['profiles'].get('email'):
                email = row['profiles']['email']
                name = row['profiles'].get('full_name', '')
                sec_email = row['profiles'].get('secondary_email', '')
                
                # Send Primary
                send_alert(email, name, row['pet_name'], row['vaccine_type'], due_str, days_left)
                sent_count += 1
                
                # Send Secondary
                if sec_email and "@" in sec_email:
                    send_alert(sec_email, name, row['pet_name'], row['vaccine_type'], due_str, days_left)
                    sent_count += 1
    except Exception as e:
        print(f"⚠️ Skipping row due to error: {e}")

print(f"🏁 Done. Total emails sent: {sent_count}")
