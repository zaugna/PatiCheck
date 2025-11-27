import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
from datetime import date, datetime

# --- SETUP ---
SUPA_URL = os.environ["SUPABASE_URL"]
SUPA_KEY = os.environ["SUPABASE_SERVICE_KEY"] # SERVICE KEY (SECRET)
supabase = create_client(SUPA_URL, SUPA_KEY)

SMTP_USER = os.environ["EMAIL_USER"]
SMTP_PASS = os.environ["EMAIL_PASS"]

def send_alert(to_email, pet, vaccine, due_date, days_left):
    print(f"Sending to {to_email}...")
    # Google Calendar Link
    start = due_date.replace("-","") + "T090000"
    end = due_date.replace("-","") + "T091500"
    link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={pet}-{vaccine}&dates={start}/{end}&details=PatiCheck"
    
    msg = MIMEMultipart()
    msg['Subject'] = f"🔔 PatiCheck: {pet} - {vaccine}"
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    
    html = f"""
    <h3>⚠️ Hatırlatma: {pet}</h3>
    <p><strong>{vaccine}</strong> zamanı geldi.</p>
    <ul><li>Tarih: {due_date}</li><li>Kalan: {days_left} gün</li></ul>
    <a href="{link}" style="background-color:#4285F4;color:white;padding:10px;text-decoration:none;border-radius:5px;">Google Takvime Ekle</a>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, to_email, msg.as_string())
    except Exception as e:
        print(f"Error: {e}")

# --- MAIN LOOP ---
today = date.today()
print(f"Checking {today}...")

# Fetch all vaccines + join with profiles to get emails
res = supabase.table("vaccinations").select("*, profiles(email)").execute()
for row in res.data:
    try:
        due = datetime.strptime(row['next_due_date'], "%Y-%m-%d").date()
        days = (due - today).days
        if 0 <= days <= 7:
            email = row['profiles']['email']
            send_alert(email, row['pet_name'], row['vaccine_type'], row['next_due_date'], days)
    except Exception as e:
        print(f"Skip: {e}")
