import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from supabase import create_client
import time
from streamlit_option_menu import option_menu
import os
from PIL import Image
import io

# --- CONFIG ---
st.set_page_config(page_title="PatiCheck", page_icon="🐾", layout="centered")

# --- CONNECT TO DB ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

supabase = init_supabase()

# --- TRANSLATION ENGINE ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'TR'

TRANS = {
    # Auth
    "app_slogan": {"TR": "Evcil hayvanlarınızın sağlığı, kontrol altında.", "EN": "Your pets' health, under control."},
    "login_tab": {"TR": "Giriş Yap", "EN": "Login"},
    "otp_tab": {"TR": "Kayıt / Şifremi Unuttum", "EN": "Register / Forgot Password"},
    
    "welcome_header": {"TR": "Hoşgeldiniz", "EN": "Welcome"},
    "otp_header": {"TR": "Tek Kullanımlık Kod ile Giriş", "EN": "Login with One-Time Code"},
    
    "email_label": {"TR": "Email", "EN": "Email"},
    "password_label": {"TR": "Şifre", "EN": "Password"},
    "login_btn": {"TR": "Giriş Yap", "EN": "Login"},
    "send_code": {"TR": "Kod Gönder", "EN": "Send Code"},
    "verify_btn": {"TR": "Doğrula", "EN": "Verify"},
    "code_sent": {"TR": "Kod gönderildi:", "EN": "Code sent to:"},
    "enter_code": {"TR": "6 Haneli Kod", "EN": "6 Digit Code"},
    
    # Onboarding
    "setup_title": {"TR": "Hesap Kurulumu", "EN": "Account Setup"},
    "setup_intro": {"TR": "Giriş başarılı! Lütfen isminizi ve kalıcı şifrenizi belirleyin.", "EN": "Login successful! Please set your name and permanent password."},
    "label_name": {"TR": "İsim", "EN": "Name"},
    "label_new_pass": {"TR": "Yeni Şifre", "EN": "New Password"},
    "save_setup": {"TR": "Kaydet ve Başla", "EN": "Save & Start"},
    
    # Errors/Success
    "error_login": {"TR": "Email veya şifre hatalı.", "EN": "Invalid email or password."},
    "error_code": {"TR": "Hatalı Kod.", "EN": "Invalid Code."},
    "email_confirm_error": {"TR": "Lütfen email onaylayın.", "EN": "Please confirm your email."},
    "success_setup": {"TR": "Hesap oluşturuldu!", "EN": "Account setup complete!"},
    "fill_all": {"TR": "Lütfen tüm alanları doldurun.", "EN": "Please fill all fields."},
    
    # Navigation
    "nav_home": {"TR": "Ana Sayfa", "EN": "Home"},
    "nav_profiles": {"TR": "Profiller", "EN": "Profiles"},
    "nav_settings": {"TR": "Ayarlar", "EN": "Settings"},
    
    # Home
    "hello": {"TR": "👋 Merhaba", "EN": "👋 Hello"},
    "add_main_btn": {"TR": "➕ Pet / Aşı Ekle", "EN": "➕ Add Pet / Vaccine"},
    "empty_home": {"TR": "Hoşgeldiniz! Henüz bir kayıt yok.", "EN": "Welcome! No records found yet."},
    "metric_total": {"TR": "Toplam Pet", "EN": "Total Pets"},
    "metric_upcoming": {"TR": "Yaklaşan", "EN": "Upcoming"},
    "metric_overdue": {"TR": "Gecikmiş", "EN": "Overdue"},
    "urgent_header": {"TR": "🚨 ACİL DURUMLAR", "EN": "🚨 URGENT ALERTS"},
    "days_passed": {"TR": "GÜN GEÇTİ", "EN": "DAYS AGO"},
    "day_passed": {"TR": "GÜN GEÇTİ", "EN": "DAY AGO"},
    "days_left": {"TR": "GÜN KALDI", "EN": "DAYS LEFT"},
    "day_left": {"TR": "GÜN KALDI", "EN": "DAY LEFT"},
    "days_ok": {"TR": "GÜN VAR", "EN": "DAYS LEFT"},
    "no_urgent": {"TR": "Harika! Önümüzdeki 7 gün içinde acil bir durum yok.", "EN": "Great! No urgent items in the next 7 days."},
    
    # Profiles
    "add_vac_btn": {"TR": "Aşı Ekle", "EN": "Add Vax"},
    "details_expander": {"TR": "Detayları Göster", "EN": "Show Details"},
    "tab_general": {"TR": "Genel", "EN": "General"},
    "tab_history": {"TR": "Geçmiş", "EN": "History"},
    "tab_chart": {"TR": "Grafik", "EN": "Chart"},
    "tab_photos": {"TR": "Fotoğraflar", "EN": "Photos"},
    "metric_weight": {"TR": "Kilo", "EN": "Weight"},
    "metric_next": {"TR": "Sıradaki", "EN": "Next"},
    "save_changes": {"TR": "Değişiklikleri Kaydet", "EN": "Save Changes"},
    "success_update": {"TR": "Güncellendi!", "EN": "Updated!"},
    "upload_label": {"TR": "Fotoğraf Yükle (Max 3)", "EN": "Upload Photo (Max 3)"},
    "delete_photo": {"TR": "Sil", "EN": "Delete"},
    "upload_optional": {"TR": "Fotoğraf Ekle (Opsiyonel)", "EN": "Add Photo (Optional)"},
    "gallery_header": {"TR": "Fotoğraflar", "EN": "Photos"},
    
    # Settings
    "settings_title": {"TR": "Ayarlar", "EN": "Settings"},
    "logged_in_as": {"TR": "Giriş:", "EN": "Logged in as:"},
    "logout_btn": {"TR": "Çıkış Yap", "EN": "Log Out"},
    "change_pass_exp": {"TR": "Şifre Değiştir", "EN": "Change Password"},
    "update_btn": {"TR": "Güncelle", "EN": "Update"},
    "success_pass": {"TR": "Başarılı!", "EN": "Success!"},
    
    # Dialog
    "dialog_title": {"TR": "💉 Yeni Aşı Kaydı", "EN": "💉 New Vaccine Record"},
    "label_pet": {"TR": "Evcil Hayvan", "EN": "Pet"},
    "opt_new_pet": {"TR": "➕ Yeni Pet Ekle...", "EN": "➕ Add New Pet..."},
    "label_pet_name": {"TR": "Pet İsmi", "EN": "Pet Name"},
    "ph_pet_name": {"TR": "Örn: Pamuk", "EN": "e.g. Luna"},
    "label_vac": {"TR": "Aşı / İşlem", "EN": "Vaccine / Treatment"},
    "label_weight": {"TR": "Kilo (kg)", "EN": "Weight (kg)"},
    "label_date": {"TR": "Yapılan Tarih", "EN": "Date Applied"},
    "label_mode": {"TR": "Hesaplama", "EN": "Calculation"},
    "opt_auto": {"TR": "Otomatik", "EN": "Automatic"},
    "opt_manual": {"TR": "Manuel", "EN": "Manual"},
    "label_validity": {"TR": "Geçerlilik", "EN": "Validity"},
    "pill_1m": {"TR": "1 Ay", "EN": "1 Mo"},
    "pill_2m": {"TR": "2 Ay", "EN": "2 Mo"},
    "pill_3m": {"TR": "3 Ay", "EN": "3 Mo"},
    "pill_1y": {"TR": "1 Yıl", "EN": "1 Yr"},
    "label_due_date": {"TR": "Bitiş Tarihi", "EN": "Due Date"},
    "caption_next": {"TR": "📅 Bir Sonraki Tarih:", "EN": "📅 Next Due Date:"},
    "label_notes": {"TR": "Notlar", "EN": "Notes"},
    "ph_notes": {"TR": "Veteriner adı...", "EN": "Vet name..."},
    "save_btn": {"TR": "Kaydet", "EN": "Save"},
    "warn_name": {"TR": "Lütfen bir isim girin.", "EN": "Please enter a name."},
    "warn_date": {"TR": "Lütfen geçerlilik süresini (veya tarihini) seçin.", "EN": "Please select validity or due date."},
    "success_save": {"TR": "Kaydedildi!", "EN": "Saved!"},
    
    # Vaccines
    "vac_karma": {"TR": "Karma", "EN": "Mixed (Karma)"},
    "vac_rabies": {"TR": "Kuduz", "EN": "Rabies"},
    "vac_leukemia": {"TR": "Lösemi", "EN": "Leukemia"},
    "vac_internal": {"TR": "İç Parazit", "EN": "Internal Parasite"},
    "vac_external": {"TR": "Dış Parazit", "EN": "External Parasite"},
    "vac_kc": {"TR": "Bronşin (KC)", "EN": "Kennel Cough"},
    "vac_lyme": {"TR": "Lyme", "EN": "Lyme"},
    "vac_checkup": {"TR": "Check-up", "EN": "Check-up"},
    
    # Columns
    "col_vac": {"TR": "Aşı", "EN": "Vaccine"},
    "col_applied": {"TR": "Yapıldı", "EN": "Applied"},
    "col_due": {"TR": "Bitiş", "EN": "Due"},
    "col_weight": {"TR": "Kg", "EN": "Kg"},
    "col_note": {"TR": "Not", "EN": "Note"},
}

def T(key):
    lang = st.session_state.lang
    return TRANS.get(key, {}).get(lang, key)

# --- CSS: THE "DIAMOND-GRADE" FIX ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    
    /* 1. FORCE LIGHT MODE */
    :root { color-scheme: light !important; }
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8F9FA !important;
        color: #1A202C !important;
    }
    .stApp { background-color: #F8F9FA !important; }
    
    /* 2. THE COMPONENT RESCUE */
    div[data-testid="stDialog"] > div { background-color: #FFFFFF !important; color: #1A202C !important; }
    button[aria-label="Close"] { color: #1A202C !important; background-color: transparent !important; border: none !important; }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #FFFFFF !important; color: #1A202C !important; border: 1px solid #E2E8F0 !important;
    }
    input[type="password"] { 
        background-color: #FFFFFF !important; color: #1A202C !important; -webkit-text-fill-color: #1A202C !important;
    }
    
    /* Selectboxes */
    div[data-baseweb="select"] { background-color: #FFFFFF !important; }
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #1A202C !important; border-color: #E2E8F0 !important; }
    div[data-baseweb="select"] span { color: #1A202C !important; }
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] { background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important; }
    li[role="option"] { color: #2D3748 !important; background-color: #FFFFFF !important; }
    li[role="option"]:hover { background-color: #FFF5F5 !important; color: #FF6B6B !important; }
    
    /* Pills */
    div[data-baseweb="tag"] { background-color: #F1F3F5 !important; border: 1px solid #E2E8F0 !important; }
    div[data-baseweb="tag"] span { color: #4A5568 !important; }
    div[data-baseweb="tag"][aria-selected="true"] { background-color: #FF6B6B !important; }
    div[data-baseweb="tag"][aria-selected="true"] span { color: #FFFFFF !important; }
    
    input[type="date"] { color-scheme: light !important; }

    /* 3. STANDARD UI ELEMENTS */
    div.css-card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    
    div.stButton > button { width: 100%; border-radius: 12px; height: 48px; background-color: #FFFFFF !important; color: #2D3748 !important; border: 2px solid #E2E8F0 !important; font-weight: 700; box-shadow: none !important; }
    div.stButton > button:hover { border-color: #FF6B6B !important; color: #FF6B6B !important; background-color: #FFF5F5 !important; }
    
    div.stButton > button[kind="primary"] { background-color: #FF6B6B !important; color: white !important; border: none !important; box-shadow: 0 4px 6px rgba(255,107,107,0.25) !important; }
    div.stButton > button[kind="primary"]:hover { background-color: #FA5252 !important; transform: scale(1.01); color: white !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: none; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { height: 40px; background-color: #FFFFFF; border-radius: 20px; color: #718096; border: 1px solid #E2E8F0; font-weight: 600; flex: 1 1 auto; }
    .stTabs [aria-selected="true"] { background-color: #FF6B6B; color: white !important; border: none; }
    
    .streamlit-expanderHeader { background-color: #FFFFFF !important; border: 2px solid #E2E8F0 !important; border-radius: 12px !important; color: #1A202C !important; }
    div[data-testid="stExpander"] { border: none; box-shadow: none; }
    
    [data-testid="stMetricValue"] { color: #1A202C !important; }
    [data-testid="stMetricLabel"] { color: #718096 !important; }
    [data-testid="stSidebar"], footer, #MainMenu { display: none; }
    div[data-testid="InputInstructions"] { display: none !important; }
    .js-plotly-plot .plotly .main-svg { background-color: transparent !important; }
    [data-testid="stDataFrame"] { background-color: white !important; border: 1px solid #E2E8F0; }

    /* Mobile */
    @media only screen and (max-width: 600px) {
        .nav-link { font-size: 12px !important; padding: 5px 2px !important; white-space: nowrap !important; }
        div[data-testid="column"] button { width: 100% !important; margin-top: 10px !important; }
        div[role="dialog"] { width: 95vw !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if "user" not in st.session_state: st.session_state["user"] = None
if "otp_sent" not in st.session_state: st.session_state["otp_sent"] = False
if "otp_email_cache" not in st.session_state: st.session_state["otp_email_cache"] = ""
if "show_onboarding" not in st.session_state: st.session_state["show_onboarding"] = False

if not supabase:
    st.error("Sistem Hatası: Veritabanı bağlantısı kurulamadı.")
    st.stop()

# --- HEADER ---
def render_header():
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image("logo.png", use_container_width=True)
    st.markdown("""
        <h1 style='text-align: center; color: #1A202C !important; font-size: 3.5rem; letter-spacing: -2px; margin-bottom: 0;'>
            Pati<span style='color:#FF6B6B'>*</span>Check
        </h1>
        <p style='text-align: center; font-size: 0.9rem; color: #A0AEC0 !important; font-style: italic; margin-top: -10px; margin-bottom: 20px;'>
            * Pati means 'Paw' in Turkish
        </p>
    """, unsafe_allow_html=True)

# --- HELPER: NAME ---
def get_user_name():
    if st.session_state["user"]:
        meta = st.session_state["user"].user_metadata
        if meta and "full_name" in meta: return meta["full_name"]
        try:
            res = supabase.table("profiles").select("full_name").eq("id", st.session_state["user"].id).execute()
            if res.data and res.data[0]['full_name']: return res.data[0]['full_name']
        except: pass
        return st.session_state["user"].email.split("@")[0]
    return ""

# --- HELPER: IMAGE PROCESSING ---
def crop_to_square(image):
    width, height = image.size
    new_size = min(width, height)
    left = (width - new_size)/2
    top = (height - new_size)/2
    right = (width + new_size)/2
    bottom = (height + new_size)/2
    return image.crop((left, top, right, bottom))

# --- DIALOGS ---
@st.dialog("Dialog") 
def add_vaccine_dialog(existing_pets, default_pet=None):
    st.markdown(f"### {T('dialog_title')}")
    index = existing_pets.index(default_pet) + 1 if default_pet and default_pet in existing_pets else 0
    options = [T("opt_new_pet")] + existing_pets
    sel = st.selectbox(T("label_pet"), options, index=index)
    
    final_pet_name = st.text_input(T("label_pet_name"), placeholder=T("ph_pet_name")) if sel == T("opt_new_pet") else sel

    # PHOTO UPLOAD (Only if new pet)
    photo_file = None
    if sel == T("opt_new_pet"):
        photo_file = st.file_uploader(T("upload_optional"), type=['png', 'jpg', 'jpeg'])

    c1, c2 = st.columns(2)
    with c1:
        vac_opts = [
            T("vac_karma"), T("vac_rabies"), T("vac_leukemia"), 
            T("vac_internal"), T("vac_external"), T("vac_kc"), 
            T("vac_lyme"), T("vac_checkup")
        ]
        vac = st.selectbox(T("label_vac"), vac_opts)
    with c2:
        w = st.number_input(T("label_weight"), step=0.1, value=0.0)

    d1 = st.date_input(T("label_date"))
    mode = st.radio(T("label_mode"), [T("opt_auto"), T("opt_manual")], horizontal=True, label_visibility="collapsed")
    
    d2 = None
    if mode == T("opt_auto"):
        dur = st.pills(T("label_validity"), [T("pill_1m"), T("pill_2m"), T("pill_3m"), T("pill_1y")], default=T("pill_1y"))
        if dur:
            val = int(dur.split()[0])
            days = val * 30 if "Ay" in dur or "Mo" in dur else val * 365
            d2 = d1 + timedelta(days=days)
            st.caption(f"{T('caption_next')} {d2.strftime('%d.%m.%Y')}")
        else:
            st.info(T("warn_date"))
            d2 = None
    else:
        d2 = st.date_input(T("label_due_date"), value=d1 + timedelta(days=30))
    
    notes = st.text_area(T("label_notes"), height=80, placeholder=T("ph_notes"))

    if st.button(T("save_btn"), type="primary"):
        if not final_pet_name: st.warning(T("warn_name"))
        elif d2 is None: st.error(T("warn_date"))
        else:
            try:
                # 1. Photo Upload
                if photo_file:
                    try:
                        img = crop_to_square(Image.open(photo_file))
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=80)
                        byte_data = buf.getvalue()
                        path = f"{st.session_state['user'].id}/{final_pet_name}/{int(time.time())}.jpg"
                        supabase.storage.from_("pet-photos").upload(path, byte_data, {"content-type": "image/jpeg"})
                        public_url = supabase.storage.from_("pet-photos").get_public_url(path)
                        supabase.table("pet_photos").insert({
                            "user_id": st.session_state['user'].id,
                            "pet_name": final_pet_name,
                            "photo_url": public_url
                        }).execute()
                    except Exception as e:
                        st.error(f"Foto Hatası: {e}")

                # 2. Save Vaccine
                supabase.table("vaccinations").insert({
                    "user_id": st.session_state["user"].id,
                    "pet_name": final_pet_name,
                    "vaccine_type": vac,
                    "date_applied": str(d1),
                    "next_due_date": str(d2),
                    "weight": w,
                    "notes": notes
                }).execute()
                st.success(T("success_save"))
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Kayıt Hatası: {e}")

@st.dialog("Dialog2")
def onboarding_dialog():
    st.markdown(f"### {T('setup_title')}")
    st.write(T('setup_intro'))
    
    name = st.text_input(T('label_name'))
    new_pass = st.text_input(T('label_new_pass'), type="password")
    
    if st.button(T('save_setup'), type="primary"):
        if name and new_pass:
            try:
                supabase.auth.update_user({"password": new_pass})
            except Exception as e:
                if "same" not in str(e).lower():
                    st.error(f"Password Error: {e}")
                    return
            try:
                uid = st.session_state["user"].id
                email = st.session_state["user"].email
                supabase.table("profiles").upsert({
                    "id": uid,
                    "email": email,
                    "full_name": name
                }).execute()
                
                st.success(T('success_setup'))
                st.session_state["show_onboarding"] = False
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(str(e))
        else:
            st.warning(T('fill_all'))

# --- AUTH LOGIC ---
def verify_otp_callback():
    code_input = st.session_state.get("otp_code_input", "").strip()
    if code_input:
        try:
            res = supabase.auth.verify_otp({
                "email": st.session_state["otp_email_cache"], 
                "token": code_input, 
                "type": "magiclink"
            })
            st.session_state["user"] = res.user
            st.session_state["otp_sent"] = False
            st.session_state["show_onboarding"] = True
        except:
            st.error(T("error_code"))

def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"] = res.user
        st.rerun()
    except Exception as e:
        msg = str(e)
        if "Email not confirmed" in msg: st.error(T("email_confirm_error"))
        else: st.error(T("error_login"))

def logout():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

# --- ENTRY ---
if st.session_state["user"] is None:
    st.markdown("<br>", unsafe_allow_html=True)
    render_header()
    
    st.markdown(f"<p style='text-align: center; color: #718096 !important; font-size: 1.2rem; margin-top: -10px;'>{T('app_slogan')}</p>", unsafe_allow_html=True)
    st.write("")
    
    with st.container():
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        
        lang_c1, lang_c2 = st.columns([4, 1])
        with lang_c2:
            l_sel = st.selectbox("Dil / Lang", ["TR", "EN"], label_visibility="collapsed")
            if l_sel != st.session_state.lang:
                st.session_state.lang = l_sel
                st.rerun()

        tab1, tab2 = st.tabs([T("login_tab"), T("otp_tab")])
        
        with tab1:
            with st.form("login_form"):
                st.markdown(f"### {T('welcome_header')}")
                email = st.text_input(T("email_label"))
                password = st.text_input(T("password_label"), type="password")
                st.write("")
                if st.form_submit_button(T("login_btn"), type="primary"):
                    login(email, password)

        with tab2:
            st.markdown(f"### {T('otp_header')}")
            
            if not st.session_state["otp_sent"]:
                with st.form("otp_send"):
                    otp_e = st.text_input(T("email_label"))
                    if st.form_submit_button(T("send_code")):
                        try:
                            supabase.auth.sign_in_with_otp({"email": otp_e})
                            st.session_state["otp_sent"] = True
                            st.session_state["otp_email_cache"] = otp_e
                            st.rerun()
                        except Exception as e: st.error(str(e))
            else:
                st.success(f"{T('code_sent')} {st.session_state['otp_email_cache']}")
                st.text_input(T("enter_code"), key="otp_code_input")
                st.button(T("verify_btn"), type="primary", on_click=verify_otp_callback)
                
                if st.button("Geri / Back", type="secondary"):
                    st.session_state["otp_sent"] = False
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

else:
    if st.session_state.get("show_onboarding"):
        onboarding_dialog()

    render_header()
    
    selected = option_menu(
        menu_title=None,
        options=[T("nav_home"), T("nav_profiles"), T("nav_settings")],
        icons=["house-fill", "heart-fill", "gear-fill"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#FFFFFF", "border-radius": "12px", "border": "1px solid #E2E8F0", "box-shadow": "0 2px 4px rgba(0,0,0,0.02)"},
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "color": "#718096"},
            "nav-link-selected": {"background-color": "#FF6B6B", "color": "white", "font-weight": "600"},
        }
    )

    rows = supabase.table("vaccinations").select("*").execute().data
    df = pd.DataFrame(rows)

    if selected == T("nav_home"):
        c1, c2 = st.columns([2.5, 1.2])
        user_name = get_user_name()
        c1.subheader(f"{T('hello')} {user_name}")
        
        if c2.button(T("add_main_btn"), type="primary"):
            existing = list(df["pet_name"].unique()) if not df.empty else []
            add_vaccine_dialog(existing)

        if df.empty:
            st.info(T("empty_home"))
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            today = date.today()
            
            k1, k2, k3 = st.columns(3)
            def styled_metric(label, value, color="#1A202C"):
                st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:12px; border:1px solid #E2E8F0; text-align:center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="color:#718096; font-size:12px; font-weight:700; margin-bottom:5px; text-transform:uppercase;">{label}</div>
                    <div style="color:{color}; font-size:26px; font-weight:800;">{value}</div>
                </div>
                """, unsafe_allow_html=True)

            with k1: styled_metric(T("metric_total"), df['pet_name'].nunique())
            upcoming = df[df["next_due_date"] > today]
            with k2: styled_metric(T("metric_upcoming"), len(upcoming))
            overdue = df[df["next_due_date"] < today]
            with k3: styled_metric(T("metric_overdue"), len(overdue), "#FF4B4B")
            
            st.write("")
            st.write("")
            
            urgent = df[df["next_due_date"] <= (today + timedelta(days=7))].sort_values("next_due_date")
            
            if not urgent.empty:
                st.caption(T("urgent_header"))
                for _, row in urgent.iterrows():
                    days = (row['next_due_date'] - today).days
                    if days < 0:
                        colors = ("#FFF5F5", "#C53030")
                        suffix = T("day_passed") if abs(days) == 1 else T("days_passed")
                        msg = f"{abs(days)} {suffix}"
                    elif days <= 3:
                        colors = ("#FFFAF0", "#C05621")
                        suffix = T("day_left") if days == 1 else T("days_left")
                        msg = f"{days} {suffix}"
                    else:
                        colors = ("#F0FFF4", "#2F855A")
                        suffix = T("day_left") if days == 1 else T("days_ok")
                        msg = f"{days} {suffix}"
                    
                    st.markdown(f"""
                    <div style="background-color: {colors[0]}; border: 1px solid {colors[1]}30; padding: 15px; border-radius: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #1A202C; font-weight: bold; font-size: 16px;">{row['pet_name']}</div>
                            <div style="color: #4A5568; font-size: 14px;">{row['vaccine_type']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: {colors[1]}; font-weight: 800; font-size: 13px;">{msg}</div>
                            <div style="color: #718096; font-size: 12px;">{row['next_due_date'].strftime('%d.%m.%Y')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success(T("no_urgent"))

    elif selected == T("nav_profiles"):
        if df.empty:
            st.warning(T("empty_home"))
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            df["date_applied"] = pd.to_datetime(df["date_applied"]).dt.date
            pets = df["pet_name"].unique()
            
            # Fetch Photos
            try:
                photos_res = supabase.table("pet_photos").select("*").eq("user_id", st.session_state["user"].id).execute()
                photos_df = pd.DataFrame(photos_res.data)
            except:
                photos_df = pd.DataFrame()

            for pet in pets:
                p_df = df[df["pet_name"] == pet].sort_values("date_applied")
                p_photos = photos_df[photos_df["pet_name"] == pet].sort_values("created_at", ascending=False) if not photos_df.empty else pd.DataFrame()
                
                with st.container():
                    c1, c2 = st.columns([2.5, 1.2])
                    with c1:
                        if not p_photos.empty:
                            av_url = p_photos.iloc[0]["photo_url"]
                            a1, a2 = st.columns([1, 4])
                            with a1: st.image(av_url, use_container_width=True)
                            with a2: st.subheader(pet)
                        else:
                            st.subheader(f"🐾 {pet}")
                    
                    if c2.button(T("add_vac_btn"), key=f"btn_{pet}", type="secondary"):
                        add_vaccine_dialog(list(pets), default_pet=pet)
                    
                    with st.expander(T("details_expander"), expanded=False):
                        t1, t2, t3, t4 = st.tabs([T("tab_general"), T("tab_history"), T("tab_chart"), T("tab_photos")])
                        
                        with t1:
                            col_a, col_b = st.columns(2)
                            last_w = p_df.iloc[-1]['weight'] if 'weight' in p_df.columns else 0.0
                            col_a.metric(T("metric_weight"), f"{last_w} kg")
                            
                            if not p_df[p_df["next_due_date"] >= date.today()].empty:
                                nxt = p_df[p_df["next_due_date"] >= date.today()].sort_values("next_due_date").iloc[0]
                                col_b.metric(T("metric_next"), nxt['vaccine_type'], nxt['next_due_date'].strftime('%d.%m'))
                            else:
                                col_b.metric(T("metric_next"), "-")
                                
                            valid_notes = [n for n in p_df["notes"].unique() if n and str(n).strip() != "None" and str(n).strip() != ""]
                            if valid_notes:
                                st.info(f"📝 {valid_notes[-1]}")
                            
                            st.write("---")
                            st.markdown(f"**{T('gallery_header')}**")
                            
                            # INSTAGRAM GRID LAYOUT
                            if not p_photos.empty:
                                cols = st.columns(3)
                                for i, (_, ph) in enumerate(p_photos.iterrows()):
                                    with cols[i % 3]:
                                        st.image(ph["photo_url"], use_container_width=True)
                                        # Simple delete button under image
                                        if st.button("🗑️", key=f"del_{ph['id']}", help=T("delete_photo"), type="secondary"):
                                            supabase.table("pet_photos").delete().eq("id", ph["id"]).execute()
                                            st.rerun()
                            
                            # Upload Button in General Tab too
                            if len(p_photos) < 3:
                                up = st.file_uploader(T("upload_label"), type=['png', 'jpg'], key=f"gal_{pet}")
                                if up:
                                    try:
                                        img = crop_to_square(Image.open(up))
                                        buf = io.BytesIO()
                                        img.save(buf, format="JPEG", quality=80)
                                        path = f"{st.session_state['user'].id}/{pet}/{int(time.time())}.jpg"
                                        supabase.storage.from_("pet-photos").upload(path, buf.getvalue(), {"content-type": "image/jpeg"})
                                        url = supabase.storage.from_("pet-photos").get_public_url(path)
                                        supabase.table("pet_photos").insert({
                                            "user_id": st.session_state['user'].id,
                                            "pet_name": pet,
                                            "photo_url": url
                                        }).execute()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))

                        with t2:
                            edit_df = p_df.copy()
                            edited = st.data_editor(
                                edit_df,
                                column_config={
                                    "id": None, "user_id": None, "created_at": None, "pet_name": None,
                                    "vaccine_type": T("col_vac"),
                                    "date_applied": st.column_config.DateColumn(T("col_applied"), format="DD.MM.YYYY"),
                                    "next_due_date": st.column_config.DateColumn(T("col_due"), format="DD.MM.YYYY"),
                                    "weight": st.column_config.NumberColumn(T("col_weight"), format="%.1f"),
                                    "notes": T("col_note")
                                },
                                hide_index=True,
                                use_container_width=True,
                                key=f"editor_{pet}"
                            )
                            if not edited.equals(edit_df):
                                if st.button(T("save_changes"), key=f"save_{pet}", type="primary"):
                                    try:
                                        recs = edited.to_dict('records')
                                        for r in recs:
                                            r['date_applied'] = str(r['date_applied'])
                                            r['next_due_date'] = str(r['next_due_date'])
                                        supabase.table("vaccinations").upsert(recs).execute()
                                        st.success(T("success_update"))
                                        time.sleep(0.5)
                                        st.rerun()
                                    except: st.error("Hata")

                        with t3:
                            if len(p_df) > 0:
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=p_df["date_applied"], y=p_df["weight"],
                                    mode='lines+markers', 
                                    line=dict(color='#FF6B6B', width=3, shape='spline'),
                                    marker=dict(size=8, color='white', line=dict(color='#FF6B6B', width=2)),
                                    fill='tozeroy', 
                                    fillcolor='rgba(255, 107, 107, 0.1)',
                                    name='Kilo'
                                ))
                                fig.update_layout(
                                    height=250, margin=dict(t=10,b=0,l=0,r=0), 
                                    paper_bgcolor='rgba(0,0,0,0)', 
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    xaxis=dict(showgrid=False, showline=False, color="#718096"),
                                    yaxis=dict(showgrid=True, gridcolor='#E2E8F0', color="#718096")
                                )
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        with t4:
                            # DUPLICATE GALLERY LOGIC FOR DEDICATED TAB
                            if not p_photos.empty:
                                cols = st.columns(3)
                                for i, (_, ph) in enumerate(p_photos.iterrows()):
                                    with cols[i % 3]:
                                        st.image(ph["photo_url"], use_container_width=True)
                                        if st.button("🗑️", key=f"del_tab_{ph['id']}", help=T("delete_photo"), type="secondary"):
                                            supabase.table("pet_photos").delete().eq("id", ph["id"]).execute()
                                            st.rerun()
                            
                            if len(p_photos) < 3:
                                up_t4 = st.file_uploader(T("upload_label"), type=['png', 'jpg'], key=f"gal_tab_{pet}")
                                if up_t4:
                                    try:
                                        img = crop_to_square(Image.open(up_t4))
                                        buf = io.BytesIO()
                                        img.save(buf, format="JPEG", quality=80)
                                        path = f"{st.session_state['user'].id}/{pet}/{int(time.time())}.jpg"
                                        supabase.storage.from_("pet-photos").upload(path, buf.getvalue(), {"content-type": "image/jpeg"})
                                        url = supabase.storage.from_("pet-photos").get_public_url(path)
                                        supabase.table("pet_photos").insert({
                                            "user_id": st.session_state['user'].id,
                                            "pet_name": pet,
                                            "photo_url": url
                                        }).execute()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                st.write("---")

    elif selected == T("nav_settings"):
        st.title(T("settings_title"))
        
        st.write("---")
        lang_sel = st.selectbox("Dil / Language", ["TR", "EN"], index=0 if st.session_state.lang == 'TR' else 1)
        if lang_sel != st.session_state.lang:
            st.session_state.lang = lang_sel
            st.rerun()
            
        st.write(f"{T('logged_in_as')} {st.session_state['user'].email}")
        
        if st.button(T("logout_btn"), type="secondary"): logout()
        
        st.write("---")
        with st.expander(T("change_pass_exp")):
            new_p = st.text_input(T("new_pass_label"), type="password")
            if st.button(T("update_btn"), type="primary"):
                try:
                    supabase.auth.update_user({"password": new_p})
                    st.success(T("success_pass"))
                except Exception as e: st.error(str(e))
