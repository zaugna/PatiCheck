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
    
    # --- DESIGN LOGIC ---
    # We separate the languages to style them differently (Hierarchy)
    
    if days_left < 0:
        # OVERDUE
        color = "#D93025" # Google Red
        bg_color = "#FCE8E6"
        icon = "🚨"
        
        # Text
        header_tr = "GECİKTİ"
        header_en = "OVERDUE"
        
        status_tr = f"{abs(days_left)} gün geçti"
        status_en = f"{abs(days_left)} days overdue"
        
        intro_tr = "Bu aşı tarihi geçmiş durumda. Lütfen kontrol ediniz."
        intro_en = "This vaccination is past due. Please check."
        
    elif days_left == 0:
        # TODAY
        color = "#F9AB00" # Google Orange
        bg_color = "#FEF7E0"
        icon = "⭐"
        
        header_tr = "BUGÜN"
        header_en = "TODAY"
        
        status_tr = "Bugün Yapılmalı"
        status_en = "Due Today"
        
        intro_tr = "Aşı günü geldi çattı!"
        intro_en = "Vaccination day is here!"
        
    elif days_left <= 3:
        # URGENT UPCOMING
        color = "#E37400" # Dark Orange
        bg_color = "#FFF3E0"
        icon = "⚠️"
        
        header_tr = "AZ KALDI"
        header_en = "SOON"
        
        status_tr = f"{days_left} gün kaldı"
        status_en = f"{days_left} days left"
        
        intro_tr = "Veteriner zamanı yaklaşıyor."
        intro_en = "Vet time is approaching."
        
    else:
        # STANDARD REMINDER
        color = "#188038" # Google Green
        bg_color = "#E6F4EA"
        icon = "📅"
        
        header_tr = "HATIRLATMA"
        header_en = "REMINDER"
        
        status_tr = f"{days_left} gün kaldı"
        status_en = f"{days_left} days left"
        
        intro_tr = "Önümüzdeki hafta için hatırlatma."
        intro_en = "Reminder for the upcoming week."

    # Email Content
    msg = MIMEMultipart()
    msg['Subject'] = f"{icon} {pet_clean}: {vaccine_clean} ({status_tr})"
    msg['From'] = f"PatiCheck <{SMTP_USER}>"
    msg['To'] = to_email
    
    # HTML DESIGN (Clean Card)
    html = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 500px; margin: 0 auto; color: #333;">
        
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #333; font-weight: 800; letter-spacing: -1px;">
                Pati<span style="color: #FF6B6B;">*</span>Check
            </h2>
        </div>

        <div style="border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            
            <div style="background-color: {color}; padding: 15px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 1px;">
                    {header_tr} <span style="font-weight: 300; opacity: 0.8;">| {header_en}</span>
                </h3>
            </div>

            <div style="padding: 25px; background-color: #ffffff;">
                
                <div style="text-align: center; margin-bottom: 25px;">
                    <div style="font-size: 28px; font-weight: 800; color: #1a1a1a; margin-bottom: 5px;">
                        {pet_clean}
                    </div>
                    <div style="font-size: 18px; color: #555; font-weight: 500;">
                        {vaccine_clean}
                    </div>
                </div>

                <div style="background-color: {bg_color}; border-radius: 8px; padding: 15px; margin-bottom: 25px;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                            <td align="center" style="padding-bottom: 10px; border-bottom: 1px solid rgba(0,0,0,0.05);">
                                <div style="font-size: 12px; color: {color}; text-transform: uppercase; font-weight: 700;">TARİH / DATE</div>
                                <div style="font-size: 18px; font-weight: 600; color: #333;">{due_date}</div>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-top: 10px;">
                                <div style="font-size: 12px; color: {color}; text-transform: uppercase; font-weight: 700;">DURUM / STATUS</div>
                                <div style="font-size: 16px; font-weight: 700; color: {color};">
                                    {status_tr} <span style="font-weight: 400; color: #666; font-size: 14px;">({status_en})</span>
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>

                <p style="text-align: center; font-size: 14px; line-height: 1.5; color: #444; margin-bottom: 25px;">
                    <strong>{intro_tr}</strong><br>
                    <span style="color: #888; font-style: italic;">{intro_en}</span>
                </p>

                <div style="text-align: center;">
                    <a href="{gcal_link}" style="background-color: {color}; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px; display: inline-block;">
                        📅 Takvime Ekle / Add to Calendar
                    </a>
                </div>

            </div>
        </div>
        
        <p style="text-align: center; font-size: 11px; color: #aaa; margin-top: 20px;">
            PatiCheck Asistan / Assistant <br>
            <a href="{APP_URL}" style="color: #aaa; text-decoration: underline;">Uygulamaya Git / Go to App</a>
        </p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, to_email, msg.as_string())
            print(f"Sent email to {to_email}")
        time.sleep(1) # Anti-spam buffer
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
