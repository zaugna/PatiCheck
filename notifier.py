import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
from datetime import date, datetime
import urllib.parse
import requests # <--- NEW: To wake up the app
import time

# --- SETUP ---
SUPA_URL = os.environ["SUPABASE_URL"]
SUPA_KEY = os.environ["SUPABASE_SERVICE_KEY"] 
supabase = create_client(SUPA_URL, SUPA_KEY)

SMTP_USER = os.environ["EMAIL_USER"]
SMTP_PASS = os.environ["EMAIL_PASS"]
# You must add this Secret to GitHub Actions for the Wake Up to work
APP_URL = os.environ.get("APP_URL", "https://paticheck.streamlit.app") 

def clean_text(text):
    if not text: return ""
    return str(text).strip()

def send_alert(to_email, pet, vaccine, due_date, days_left):
    print(f"Sending to {to_email}...")
    
    pet_clean = clean_text(pet)
    vaccine_clean = clean_text(vaccine)
    
    # Google Calendar Link
    start = due_date.replace("-","") + "T090000"
    end = due_date.replace("-","") + "T091500"
    gcal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={pet_clean}-{vaccine_clean}&dates={start}/{end}&details=PatiCheck&sf=true&output=xml"
    
    urgency = "⚠️" if days_left > 3 else "🚨"
    
    msg = MIMEMultipart()
    msg['Subject'] = f"{urgency} PatiCheck: {pet_clean} - {vaccine_clean}"
    msg['From'] = f"PatiCheck <{SMTP_USER}>"
    msg['To'] = to_email
    
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h3 style="color: #d32f2f;">{urgency} Hatırlatma: {pet_clean}</h3>
        <p><strong>{vaccine_clean}</strong> zamanı geldi.</p>
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p>📅 <strong>Tarih:</strong> {due_date}</p>
            <p>⏳ <strong>Kalan:</strong> {days_left} gün</p>
        </div>
        
        <a href="{gcal_link}" style="background-color:#4285F4;color:white;padding:12px 24px;text-decoration:none;border-radius:5px;font-weight:bold;display:inline-block;">Google Takvime Ekle</a>
        
        <p style="margin-top: 15px; font-size: 12px; color: #666;">
            Buton çalışmıyorsa aşağıdaki linke tıklayın:<br>
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
    except Exception as e:
        print(f"Error sending to {to_email}: {e}")

# --- MAIN LOGIC ---
today = date.today()
print(f"Checking vaccines for {today}...")

response = supabase.table("vaccinations").select("*, profiles(email)").execute()
rows = response.data

for row in rows:
    try:
        due_str = row['next_due_date']
        due_date_obj = datetime.strptime(due_str, "%Y-%m-%d").date()
        days_left = (due_date_obj - today).days
        
        if 0 <= days_left <= 7:
            email = row['profiles']['email'] 
            send_alert(email, row['pet_name'], row['vaccine_type'], due_str, days_left)
    except Exception as e:
        print(f"Skipping row: {e}")

# --- WAKE UP CALL (Prevent Sleeping) ---
try:
    print(f"Pinging {APP_URL} to wake it up...")
    requests.get(APP_URL)
    print("Ping successful.")
except Exception as e:
    print(f"Ping failed: {e}")
