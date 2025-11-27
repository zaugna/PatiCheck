import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
from datetime import date, datetime
import urllib.parse

# --- SETUP ---
SUPA_URL = os.environ["SUPABASE_URL"]
SUPA_KEY = os.environ["SUPABASE_SERVICE_KEY"] 
supabase = create_client(SUPA_URL, SUPA_KEY)

SMTP_USER = os.environ["EMAIL_USER"]
SMTP_PASS = os.environ["EMAIL_PASS"]

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
    gcal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={pet_clean}-{vaccine_clean}&dates={start}/{end}&details=PatiCheck Hatırlatması&sf=true&output=xml"
    
    # Humanized Subject & Logic
    if days_left <= 3:
        subject = f"🔔 {pet_clean} için {vaccine_clean} zamanı geldi!"
        color = "#e63946" # Urgent Red-ish
        intro = "Veteriner zamanı yaklaşıyor."
    else:
        subject = f"📅 {pet_clean}: {vaccine_clean} hatırlatması"
        color = "#2a9d8f" # Soft Teal
        intro = "Önümüzdeki hafta için küçük bir hatırlatma."
    
    # Humanized HTML Body
    html = f"""
    <div style="font-family: 'Helvetica', sans-serif; padding: 20px; color: #333; max-width: 500px;">
        <h2 style="color: {color};">Merhaba Pati Dostu! 👋</h2>
        <p style="font-size: 16px;">{intro}</p>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-left: 5px solid {color}; margin: 20px 0;">
            <p style="margin: 5px 0; font-size: 18px;"><strong>🐾 {pet_clean}</strong></p>
            <p style="margin: 5px 0;">💉 <strong>İşlem:</strong> {vaccine_clean}</p>
            <p style="margin: 5px 0;">📅 <strong>Tarih:</strong> {due_date}</p>
            <p style="margin: 5px 0;">⏳ <strong>Kalan Süre:</strong> {days_left} gün</p>
        </div>
        
        <p>Randevunuzu almayı unutmayın. Sağlıklı ve mutlu günler dileriz!</p>
        
        <a href="{gcal_link}" style="background-color:{color};color:white;padding:12px 24px;text-decoration:none;border-radius:50px;font-weight:bold;display:inline-block;margin-top:10px;">
            📅 Takvime Ekle
        </a>
        
        <hr style="margin-top: 30px; border: 0; border-top: 1px solid #eee;">
        <p style="font-size: 11px; color: #999;">Bu mesaj PatiCheck asistanı tarafından otomatik gönderilmiştir.</p>
    </div>
    """
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = f"PatiCheck Asistanı <{SMTP_USER}>" # Friendly Name
    msg['To'] = to_email
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, to_email, msg.as_string())
            print("Sent!")
    except Exception as e:
        print(f"Error: {e}")

# --- MAIN LOGIC ---
today = date.today()
print(f"Checking vaccines for {today}...")

response = supabase.table("vaccinations").select("*, profiles(email)").execute()
rows = response.data

for row in rows:
    try:
        due_str = row['next_due_date']
        due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        days_left = (due_date - today).days
        
        if 0 <= days_left <= 7:
            email = row['profiles']['email'] 
            send_alert(email, row['pet_name'], row['vaccine_type'], due_str, days_left)
    except Exception as e:
        print(f"Skipping row: {e}")
