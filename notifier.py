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
    
    # --- LOGIC: PLURALIZATION & URGENCY ---
    
    # Helper for English Grammar (1 day vs 2 days)
    day_word_en = "day" if abs(days_left) == 1 else "days"
    
    if days_left < 0:
        # OVERDUE
        color = "#D93025" # Red
        bg_color = "#FCE8E6"
        icon = "🚨"
        
        status_tr = f"{abs(days_left)} gün geçti"
        status_en = f"{abs(days_left)} {day_word_en} overdue"
        
        intro_tr = "Bu aşı tarihi geçmiş durumda."
        intro_en = "This vaccination is past due."
        
    elif days_left == 0:
        # TODAY
        color = "#F9AB00" # Orange
        bg_color = "#FEF7E0"
        icon = "⭐"
        
        status_tr = "Bugün"
        status_en = "Today"
        
        intro_tr = "Aşı günü geldi çattı!"
        intro_en = "Vaccination day is here!"
        
    elif days_left <= 3:
        # URGENT UPCOMING
        color = "#E37400" # Deep Orange
        bg_color = "#FFF3E0"
        icon = "⚠️"
        
        status_tr = f"{days_left} gün kaldı"
        status_en = f"{days_left} {day_word_en} left"
        
        intro_tr = "Veteriner zamanı yaklaşıyor."
        intro_en = "Vet time is approaching."
        
    else:
        # STANDARD REMINDER
        color = "#188038" # Green
        bg_color = "#E6F4EA"
        icon = "📅"
        
        status_tr = f"{days_left} gün kaldı"
        status_en = f"{days_left} {day_word_en} left"
        
        intro_tr = "Hatırlatma."
        intro_en = "Reminder."

    # Email Header
    msg = MIMEMultipart()
    # Simplified Subject as requested
    msg['Subject'] = f"{icon} PatiCheck: Hatırlatma / Reminder"
    msg['From'] = f"PatiCheck <{SMTP_USER}>"
    msg['To'] = to_email
    
    # HTML DESIGN (Optimized Typography)
    html = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 500px; margin: 0 auto; color: #333; line-height: 1.4;">
        
        <div style="text-align: center; margin-bottom: 20px; padding-top: 10px;">
            <h2 style="margin: 0; color: #1A202C; font-weight: 800; font-size: 24px;">
                Pati<span style="color: #FF6B6B;">*</span>Check
            </h2>
        </div>

        <div style="border: 1px solid #e0e0e0; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            
            <div style="background-color: {color}; height: 8px; width: 100%;"></div>

            <div style="padding: 30px 25px; background-color: #ffffff; text-align: center;">
                
                <div style="color: #718096; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">
                    {pet_clean}
                </div>

                <div style="font-size: 28px; font-weight: 800; color: {color}; margin-bottom: 20px; line-height: 1.2;">
                    {vaccine_clean}
                </div>

                <div style="background-color: {bg_color}; border-radius: 12px; padding: 15px; margin-bottom: 25px; display: inline-block; width: 100%;">
                    <div style="font-size: 16px; font-weight: 600; color: #333; margin-bottom: 4px;">
                        {due_date}
                    </div>
                    <div style="font-size: 14px; font-weight: 500; color: {color};">
                        {status_tr} <span style="opacity: 0.7;">/ {status_en}</span>
                    </div>
                </div>

                <p style="font-size: 14px; color: #4A5568; margin-bottom: 25px;">
                    {intro_tr}<br>
                    <span style="color: #A0AEC0; font-style: italic;">{intro_en}</span>
                </p>

                <a href="{gcal_link}" style="background-color: {color}; color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px; display: inline-block;">
                    Takvime Ekle / Add to Calendar
                </a>

            </div>
        </div>
        
        <p style="text-align: center; font-size: 11px; color: #CBD5E0; margin-top: 20px;">
            <a href="{APP_URL}" style="color: #A0AEC0; text-decoration: none;">PatiCheck.app</a>
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

# SMART SCHEDULE
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

# --- WAKE UP CALL ---
try:
    if APP_URL:
        requests.get(APP_URL, timeout=10)
        print("Ping success.")
except:
    pass
