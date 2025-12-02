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
    
    # --- LOGIC: DYNAMIC CONTENT BASED ON TIMING ---
    if days_left < 0:
        # OVERDUE
        urgency = "🚨"
        subject_prefix = "GECİKTİ"
        color = "#d32f2f" # Dark Red
        intro = f"{abs(days_left)} gün gecikti. Lütfen en kısa zamanda tamamlayın."
    elif days_left == 0:
        # TODAY
        urgency = "⭐"
        subject_prefix = "BUGÜN"
        color = "#f57c00" # Orange
        intro = "Aşı günü geldi çattı!"
    elif days_left <= 3:
        # URGENT
        urgency = "⚠️"
        subject_prefix = "AZ KALDI"
        color = "#e63946" # Red-ish
        intro = "Veteriner zamanı yaklaşıyor."
    else:
        # UPCOMING
        urgency = "📅"
        subject_prefix = "HATIRLATMA"
        color = "#2a9d8f" # Teal
        intro = "Önümüzdeki hafta için küçük bir hatırlatma."

    # Subject
    msg = MIMEMultipart()
    msg['Subject'] = f"{urgency} {subject_prefix}: {pet_clean} - {vaccine_clean}"
    msg['From'] = f"PatiCheck <{SMTP_USER}>"
    msg['To'] = to_email
    
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h3 style="color: {color};">{urgency} {intro}</h3>
        <p><strong>{pet_clean}</strong> - <strong>{vaccine_clean}</strong></p>
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p>📅 <strong>Tarih:</strong> {due_date}</p>
            <p>⏳ <strong>Durum:</strong> {days_left} gün (kalan/geçen)</p>
        </div>
        
        <a href="{gcal_link}" style="background-color:#4285F4;color:white;padding:12px 24px;text-decoration:none;border-radius:5px;font-weight:bold;display:inline-block;">Google Takvime Ekle</a>
        
        <p style="margin-top: 15px; font-size: 12px; color: #666;">
            Buton çalışmıyorsa:<br>
            <a href="{gcal_link}" style="color: #4285F4;">{gcal_link}</a>
        </p>
        <p style="margin-top:20px;font-size:12px;color:#888;">Bu otomatik bir mesajdır. - PatiCheck</p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, to_email, msg.as_string())
            print("Sent!")
        # Anti-Spam Delay
        time.sleep(2) 
    except Exception as e:
        print(f"Error sending to {to_email}: {e}")

# --- MAIN LOGIC ---
today = date.today()
print(f"Checking vaccines for {today}...")

response = supabase.table("vaccinations").select("*, profiles(email)").execute()
rows = response.data

# LOGIC: NOTIFY ON KEY DAYS
# We notify on: 7 days before, 3 days before, 1 day before, Day 0, 3 days late, 7 days late
NOTIFY_DAYS = [7, 3, 1, 0, -3, -7]

for row in rows:
    try:
        due_str = row['next_due_date']
        due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        days_left = (due_date - today).days
        
        if days_left in NOTIFY_DAYS:
            email = row['profiles']['email'] 
            send_alert(email, row['pet_name'], row['vaccine_type'], due_str, days_left)
    except Exception as e:
        print(f"Skipping row: {e}")

# --- WAKE UP ---
try:
    if APP_URL:
        requests.get(APP_URL)
        print("Ping success.")
except:
    pass
