import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from supabase import create_client
import time
from streamlit_option_menu import option_menu

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
    # Auth & General
    "app_slogan": {"TR": "Evcil hayvanlarınızın sağlığı, kontrol altında.", "EN": "Your pets' health, under control."},
    "login_tab": {"TR": "Giriş Yap", "EN": "Login"},
    "code_tab": {"TR": "Kod ile Gir", "EN": "Enter w/ Code"},
    "welcome_header": {"TR": "Hoşgeldiniz", "EN": "Welcome"},
    "email_label": {"TR": "Email", "EN": "Email"},
    "password_label": {"TR": "Şifre", "EN": "Password"},
    "login_btn": {"TR": "Giriş Yap", "EN": "Login"},
    "no_account": {"TR": "Hesabınız yoksa 'Kod ile Gir' sekmesinden kayıt olun.", "EN": "No account? Sign up via 'Enter w/ Code' tab."},
    "quick_login": {"TR": "Hızlı Giriş", "EN": "Quick Login"},
    "send_code": {"TR": "Kod Gönder", "EN": "Send Code"},
    "verify_btn": {"TR": "Doğrula", "EN": "Verify"},
    "code_sent": {"TR": "Kod gönderildi:", "EN": "Code sent to:"},
    "enter_code": {"TR": "6 Haneli Kod", "EN": "6 Digit Code"},
    "error_login": {"TR": "Email veya şifre hatalı.", "EN": "Invalid email or password."},
    "error_code": {"TR": "Hatalı Kod", "EN": "Invalid Code"},
    "email_confirm_error": {"TR": "Lütfen email onaylayın.", "EN": "Please confirm your email."},
    
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
    "days_left": {"TR": "GÜN KALDI", "EN": "DAYS LEFT"},
    "days_ok": {"TR": "GÜN VAR", "EN": "DAYS LEFT"},
    "no_urgent": {"TR": "Harika! Önümüzdeki 7 gün içinde acil bir durum yok.", "EN": "Great! No urgent items in the next 7 days."},
    
    # Profiles (Pets)
    "add_vac_btn": {"TR": "Aşı Ekle", "EN": "Add Vax"},
    "details_expander": {"TR": "Detayları Göster", "EN": "Show Details"},
    "tab_general": {"TR": "Genel", "EN": "General"},
    "tab_history": {"TR": "Geçmiş", "EN": "History"},
    "tab_chart": {"TR": "Grafik", "EN": "Chart"},
    "metric_weight": {"TR": "Kilo", "EN": "Weight"},
    "metric_next": {"TR": "Sıradaki", "EN": "Next"},
    "save_changes": {"TR": "Değişiklikleri Kaydet", "EN": "Save Changes"},
    "success_update": {"TR": "Güncellendi!", "EN": "Updated!"},
    
    # Settings
    "settings_title": {"TR": "Ayarlar", "EN": "Settings"},
    "logged_in_as": {"TR": "Giriş:", "EN": "Logged in as:"},
    "logout_btn": {"TR": "Çıkış Yap", "EN": "Log Out"},
    "change_pass_exp": {"TR": "Şifre Değiştir", "EN": "Change Password"},
    "new_pass_label": {"TR": "Yeni Şifre", "EN": "New Password"},
    "update_btn": {"TR": "Güncelle", "EN": "Update"},
    "success_pass": {"TR": "Başarılı!", "EN": "Success!"},
    
    # Dialog / Form
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
    
    # Table Columns
    "col_vac": {"TR": "Aşı", "EN": "Vaccine"},
    "col_applied": {"TR": "Yapıldı", "EN": "Applied"},
    "col_due": {"TR": "Bitiş", "EN": "Due"},
    "col_weight": {"TR": "Kg", "EN": "Kg"},
    "col_note": {"TR": "Not", "EN": "Note"},
}

def T(key):
    """Translation Helper"""
    lang = st.session_state.lang
    return TRANS.get(key, {}).get(lang, key)

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    :root { color-scheme: light !important; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8F9FA; color: #1A202C; }
    .stApp { background-color: #F8F9FA !important; }
    
    /* Typography */
    h1, h2, h3 { color: #1A202C !important; font-weight: 800; letter-spacing: -0.5px; }
    p, label, span, li, div { color: #4A5568 !important; }
    
    /* Cards */
    div.css-card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    
    /* Buttons */
    div.stButton > button { width: 100%; border-radius: 12px; height: 48px; background-color: #FF6B6B; color: white !important; border: none; font-weight: 700; box-shadow: 0 4px 6px rgba(255, 107, 107, 0.25); transition: transform 0.1s; }
    div.stButton > button:hover { background-color: #FA5252; transform: scale(1.01); }
    button[kind="secondary"] { background-color: #FFFFFF !important; color: #2D3748 !important; border: 2px solid #E2E8F0 !important; box-shadow: none !important; }
    button[kind="secondary"]:hover { border-color: #FF6B6B !important; color: #FF6B6B !important; background-color: #FFF5F5 !important; }

    /* Modal Fixes */
    div[role="dialog"] { background-color: #FFFFFF !important; color: #1A202C !important; }
    button[aria-label="Close"] { color: #1A202C !important; background-color: transparent !important; border: none !important; }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { background-color: #FFFFFF !important; color: #1A202C !important; border: 2px solid #E2E8F0 !important; border-radius: 10px; }
    input[type="password"] { background-color: #FFFFFF !important; color: #1A202C !important; -webkit-text-fill-color: #1A202C !important; }

    /* Pills */
    div[data-baseweb="tag"] { background-color: #F1F3F5 !important; border: 1px solid #E2E8F0 !important; cursor: pointer; }
    div[data-baseweb="tag"] span, div[data-baseweb="tag"] div { color: #4A5568 !important; }
    div[data-baseweb="tag"][aria-selected="true"] { background-color: #FF6B6B !important; border-color: #FF6B6B !important; }
    div[data-baseweb="tag"][aria-selected="true"] span, div[data-baseweb="tag"][aria-selected="true"] div { color: #FFFFFF !important; }

    /* Dropdowns */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] { background-color: #FFFFFF !important; border: 1px solid #E2E8F0; }
    li[role="option"] { color: #2D3748 !important; background-color: #FFFFFF !important; }
    li[role="option"]:hover { background-color: #FFF5F5 !important; color: #FF6B6B !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: none; padding-bottom: 15px; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { height: 40px; background-color: #FFFFFF; border-radius: 20px; color: #718096; border: 1px solid #E2E8F0; font-weight: 600; flex: 1 1 auto; }
    .stTabs [aria-selected="true"] { background-color: #FF6B6B; color: white !important; border: none; box-shadow: 0 4px 6px rgba(255, 107, 107, 0.3); }
    
    /* Expander */
    .streamlit-expanderHeader { background-color: #FFFFFF !important; border: 2px solid #E2E8F0 !important; border-radius: 12px !important; color: #1A202C !important; font-weight: 600 !important; }
    .streamlit-expanderHeader:hover { border-color: #FF6B6B !important; color: #FF6B6B !important; }
    .streamlit-expanderHeader p { color: inherit !important; }
    div[data-testid="stExpander"] { border: none; box-shadow: none; }
    .streamlit-expanderContent { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-top: none; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; padding: 20px; margin-top: -8px; }

    /* Metrics & Utils */
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #1A202C !important; font-weight: 800; }
    [data-testid="stMetricLabel"] { font-size: 12px !important; color: #718096 !important; font-weight: 700; text-transform: uppercase; }
    [data-testid="stSidebar"] { display: none; }
    #MainMenu { display: none; }
    footer { display: none; }
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

# --- STATE INITIALIZATION (RESTORED) ---
if "user" not in st.session_state: st.session_state["user"] = None
if "otp_sent" not in st.session_state: st.session_state["otp_sent"] = False
if "otp_email_cache" not in st.session_state: st.session_state["otp_email_cache"] = ""

if not supabase:
    st.error("Sistem Hatası: Veritabanı bağlantısı kurulamadı.")
    st.stop()

# --- DIALOGS ---
@st.dialog("Dialog") # Title placeholder, we override inside
def add_vaccine_dialog(existing_pets, default_pet=None):
    st.markdown(f"### {T('dialog_title')}") # Manual Header since dialog title is static
    
    index = 0
    if default_pet and default_pet in existing_pets:
        index = existing_pets.index(default_pet) + 1 
    
    options = [T("opt_new_pet")] + existing_pets
    sel = st.selectbox(T("label_pet"), options, index=index)
    
    final_pet_name = ""
    if sel == T("opt_new_pet"):
        final_pet_name = st.text_input(T("label_pet_name"), placeholder=T("ph_pet_name"))
    else:
        final_pet_name = sel

    c1, c2 = st.columns(2)
    with c1:
        vac = st.selectbox(T("label_vac"), ["Karma", "Kuduz", "Lösemi", "İç Parazit", "Dış Parazit", "Bronşin", "Lyme", "Check-up"])
    with c2:
        w = st.number_input(T("label_weight"), step=0.1, value=0.0)

    d1 = st.date_input(T("label_date"))
    mode = st.radio(T("label_mode"), [T("opt_auto"), T("opt_manual")], horizontal=True, label_visibility="collapsed")
    
    d2 = None
    if mode == T("opt_auto"):
        # Pills options must match the translation dictionary keys logic or values
        # Simplified: We use values directly
        pills_opts = [T("pill_1m"), T("pill_2m"), T("pill_3m"), T("pill_1y")]
        dur = st.pills(T("label_validity"), pills_opts, default=T("pill_1y"))
        
        if dur:
            # Simple parsing logic
            val = int(dur.split()[0])
            days = val * 30 if "Ay" in dur or "Mo" in dur else val * 365
            d2 = d1 + timedelta(days=days)
            st.caption(f"{T('caption_next')} {d2.strftime('%d.%m.%Y')}")
        else:
            st.info(T("warn_date"))
    else:
        d2 = st.date_input(T("label_due_date"), value=d1 + timedelta(days=30))
    
    notes = st.text_area(T("label_notes"), height=80, placeholder=T("ph_notes"))

    if st.button(T("save_btn"), type="primary"):
        if not final_pet_name:
            st.warning(T("warn_name"))
        elif d2 is None:
            st.error(T("warn_date"))
        else:
            try:
                data = {
                    "user_id": st.session_state["user"].id,
                    "pet_name": final_pet_name,
                    "vaccine_type": vac,
                    "date_applied": str(d1),
                    "next_due_date": str(d2),
                    "weight": w,
                    "notes": notes
                }
                supabase.table("vaccinations").insert(data).execute()
                st.success(T("success_save"))
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Hata: {e}")

# --- AUTH ---
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"] = res.user
        st.rerun()
    except Exception as e:
        msg = str(e)
        if "Email not confirmed" in msg: st.error("Email not confirmed")
        else: st.error(T("error_login"))

def logout():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

# --- ENTRY ---
if st.session_state["user"] is None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #1A202C !important; font-size: 3.5rem; letter-spacing: -2px;'>🐾 PatiCheck</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #718096 !important; font-size: 1.2rem; margin-top: -10px;'>{T('app_slogan')}</p>", unsafe_allow_html=True)
    st.write("")
    
    with st.container():
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        
        # LANGUAGE TOGGLE (LOGIN SCREEN)
        lang_c1, lang_c2 = st.columns([4, 1])
        with lang_c2:
            l_sel = st.selectbox("Dil / Lang", ["TR", "EN"], label_visibility="collapsed")
            if l_sel != st.session_state.lang:
                st.session_state.lang = l_sel
                st.rerun()

        tab1, tab2 = st.tabs([T("login_tab"), T("code_tab")])
        
        with tab1:
            with st.form("login_form"):
                st.markdown(f"### {T('welcome_header')}")
                email = st.text_input(T("email_label"))
                password = st.text_input(T("password_label"), type="password")
                st.write("")
                if st.form_submit_button(T("login_btn"), type="primary"):
                    login(email, password)
            st.markdown(f"<p style='text-align:center; font-size:12px; margin-top:10px;'>{T('no_account')}</p>", unsafe_allow_html=True)

        with tab2:
            st.markdown(f"### {T('quick_login')}")
            otp_e = st.text_input(T("email_label"), key="otp_e")
            
            if not st.session_state["otp_sent"]:
                if st.button(T("send_code")):
                    try:
                        supabase.auth.sign_in_with_otp({"email": otp_e})
                        st.session_state["otp_sent"] = True
                        st.session_state["otp_email_cache"] = otp_e
                        st.rerun()
                    except Exception as e: st.error(str(e))
            else:
                st.success(f"{T('code_sent')} {st.session_state['otp_email_cache']}")
                code = st.text_input(T("enter_code"))
                if st.button(T("verify_btn")):
                    try:
                        clean_code = code.strip()
                        res = supabase.auth.verify_otp({"email": st.session_state["otp_email_cache"], "token": clean_code, "type": "magiclink"})
                        st.session_state["user"] = res.user
                        st.session_state["otp_sent"] = False
                        st.rerun()
                    except: st.error(T("error_code"))
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- HEADER & NAVIGATION ---
    st.markdown("<h3 style='text-align: center; margin-bottom: 5px;'>🐾 PatiCheck</h3>", unsafe_allow_html=True)
    
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

    # --- HOME ---
    if selected == T("nav_home"):
        c1, c2 = st.columns([2.5, 1.2])
        c1.subheader(T("hello"))
        
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
                        msg = f"{abs(days)} {T('days_passed')}"
                    elif days <= 3:
                        colors = ("#FFFAF0", "#C05621")
                        msg = f"{days} {T('days_left')}"
                    else:
                        colors = ("#F0FFF4", "#2F855A")
                        msg = f"{days} {T('days_ok')}"
                    
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

    # --- PETS ---
    elif selected == T("nav_profiles"):
        if df.empty:
            st.warning(T("empty_home"))
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            df["date_applied"] = pd.to_datetime(df["date_applied"]).dt.date
            pets = df["pet_name"].unique()

            for pet in pets:
                p_df = df[df["pet_name"] == pet].sort_values("date_applied")
                
                with st.container():
                    c_head1, c_head2 = st.columns([2.5, 1.2])
                    c_head1.subheader(f"🐾 {pet}")
                    if c_head2.button(T("add_vac_btn"), key=f"btn_{pet}", type="secondary"):
                        add_vaccine_dialog(list(pets), default_pet=pet)
                    
                    with st.expander(T("details_expander"), expanded=False):
                        t1, t2, t3 = st.tabs([T("tab_general"), T("tab_history"), T("tab_chart")])
                        
                        with t1:
                            future = p_df[p_df["next_due_date"] >= date.today()].sort_values("next_due_date")
                            col_a, col_b = st.columns(2)
                            
                            last_w = p_df.iloc[-1]['weight'] if 'weight' in p_df.columns else 0.0
                            col_a.metric(T("metric_weight"), f"{last_w} kg")
                            
                            if not future.empty:
                                nxt = future.iloc[0]
                                col_b.metric(T("metric_next"), nxt['vaccine_type'], nxt['next_due_date'].strftime('%d.%m'))
                            else:
                                col_b.metric(T("metric_next"), "-")
                                
                            valid_notes = [n for n in p_df["notes"].unique() if n and str(n).strip() != "None" and str(n).strip() != ""]
                            if valid_notes:
                                st.info(f"📝 {valid_notes[-1]}")

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
                st.write("---")

    # --- SETTINGS ---
    elif selected == T("nav_settings"):
        st.title(T("settings_title"))
        
        # LANGUAGE TOGGLE (Inside Settings)
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
