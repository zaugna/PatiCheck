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

# --- DESIGN SYSTEM: "CLEAN LIGHT" ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    
    /* 1. GLOBAL RESET */
    * { font-family: 'Inter', sans-serif; }
    
    /* 2. BACKGROUND (Soft Off-White) */
    .stApp { background-color: #F7F9FC; }
    
    /* 3. TYPOGRAPHY */
    h1, h2, h3 { color: #1A202C !important; font-weight: 800; letter-spacing: -0.5px; }
    p, label, span, li, div { color: #4A5568 !important; }
    
    /* 4. CARDS (White + Soft Shadow) */
    div.css-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* 5. BUTTONS (Vibrant & Tactile) */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 48px;
        background-color: #FF6B6B;
        color: white !important;
        border: none;
        font-weight: 600;
        box-shadow: 0 4px 14px 0 rgba(255, 107, 107, 0.39);
        transition: transform 0.2s;
    }
    div.stButton > button:hover {
        background-color: #FA5252;
        transform: scale(1.02);
        color: white !important;
    }
    /* Secondary Button Override */
    button[kind="secondary"] {
        background-color: #EDF2F7 !important;
        color: #2D3748 !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 6. INPUTS (Clean White) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #2D3748 !important;
        border: 2px solid #E2E8F0 !important;
        border-radius: 10px;
        padding-left: 10px;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #FF6B6B !important;
    }
    
    /* 7. DROPDOWNS */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    li[role="option"] { color: #2D3748 !important; }
    li[role="option"]:hover { background-color: #FFF5F5 !important; color: #FF6B6B !important; }
    
    /* 8. TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: none; }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #FFFFFF;
        border-radius: 8px;
        color: #718096;
        border: 1px solid #E2E8F0;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF6B6B;
        color: white !important;
        border: none;
    }
    
    /* 9. METRICS */
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #1A202C !important; font-weight: 800; }
    [data-testid="stMetricLabel"] { font-size: 14px !important; color: #718096 !important; font-weight: 500; }
    
    /* 10. EXPANDER (Clean Card Style) */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        color: #2D3748 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .streamlit-expanderHeader:hover { border-color: #FF6B6B; color: #FF6B6B !important; }
    div[data-testid="stExpander"] { border: none; }
    .streamlit-expanderContent {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: none;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
        padding: 20px;
    }

    /* 11. HIDE UTILS */
    [data-testid="stSidebar"] { display: none; }
    #MainMenu { display: none; }
    footer { display: none; }
    .js-plotly-plot .plotly .main-svg { background-color: transparent !important; }
    div[data-testid="InputInstructions"] { display: none !important; }
    
    /* 12. TABLE FIX */
    [data-testid="stDataFrame"] { background-color: white; border: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)

if not supabase:
    st.error("Sistem Hatası: Veritabanı bağlantısı kurulamadı.")
    st.stop()

# --- STATE ---
if "user" not in st.session_state: st.session_state["user"] = None
if "otp_sent" not in st.session_state: st.session_state["otp_sent"] = False
if "otp_email_cache" not in st.session_state: st.session_state["otp_email_cache"] = ""

# --- MODERN DIALOGS ---
@st.dialog("💉 Yeni Aşı Kaydı")
def add_vaccine_dialog(existing_pets, default_pet=None):
    index = 0
    if default_pet and default_pet in existing_pets:
        index = existing_pets.index(default_pet) + 1 
    
    options = ["➕ Yeni Pet Ekle..."] + existing_pets
    sel = st.selectbox("Evcil Hayvan", options, index=index)
    
    final_pet_name = ""
    if sel == "➕ Yeni Pet Ekle...":
        final_pet_name = st.text_input("Pet İsmi", placeholder="Örn: Pamuk")
    else:
        final_pet_name = sel

    c1, c2 = st.columns(2)
    with c1:
        vac = st.selectbox("Aşı / İşlem", ["Karma", "Kuduz", "Lösemi", "İç Parazit", "Dış Parazit", "Bronşin", "Lyme", "Check-up"])
    with c2:
        w = st.number_input("Kilo (kg)", step=0.1, value=None, placeholder="0.0")

    d1 = st.date_input("Yapılan Tarih")
    
    mode = st.radio("Hesaplama", ["Otomatik", "Manuel"], horizontal=True, label_visibility="collapsed")
    
    if mode == "Otomatik":
        dur = st.pills("Geçerlilik", ["1 Ay", "2 Ay", "3 Ay", "1 Yıl"], default="1 Yıl")
        m = 12 if "Yıl" in dur else int(dur.split()[0])
        d2 = d1 + timedelta(days=m*30)
    else:
        d2 = st.date_input("Bitiş Tarihi", value=d1 + timedelta(days=30))
    
    st.caption(f"📅 Bir Sonraki Tarih: {d2.strftime('%d.%m.%Y')}")
    notes = st.text_area("Notlar", height=80, placeholder="Veteriner adı...")

    if st.button("Kaydet", type="primary"):
        if not final_pet_name:
            st.warning("Lütfen bir isim girin.")
        else:
            try:
                data = {
                    "user_id": st.session_state["user"].id,
                    "pet_name": final_pet_name,
                    "vaccine_type": vac,
                    "date_applied": str(d1),
                    "next_due_date": str(d2),
                    "weight": w if w else 0.0,
                    "notes": notes
                }
                supabase.table("vaccinations").insert(data).execute()
                st.success("Kaydedildi!")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Hata: {e}")

# --- AUTH LOGIC ---
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"] = res.user
        st.rerun()
    except Exception as e:
        msg = str(e)
        if "Email not confirmed" in msg: st.error("Lütfen email onaylayın.")
        else: st.error("Email veya şifre hatalı.")

def logout():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

# --- ENTRY POINT ---
if st.session_state["user"] is None:
    # CLEAN LIGHT LANDING PAGE
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #1A202C !important; font-size: 3.5rem; letter-spacing: -2px;'>🐾 PatiCheck</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #718096 !important; font-size: 1.2rem; margin-top: -10px;'>Akıllı, güvenli ve modern evcil hayvan takibi.</p>", unsafe_allow_html=True)
    st.write("")
    
    # White Card Container for Login
    with st.container():
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Giriş Yap", "Kod ile Gir"])
        
        with tab1:
            with st.form("login_form"):
                st.markdown("### Hoşgeldiniz")
                email = st.text_input("Email")
                password = st.text_input("Şifre", type="password")
                st.write("")
                if st.form_submit_button("Giriş Yap", type="primary"):
                    login(email, password)
            st.markdown("<p style='text-align:center; font-size:12px; margin-top:10px;'>Hesabınız yoksa 'Kod ile Gir' sekmesinden otomatik oluşturun.</p>", unsafe_allow_html=True)

        with tab2:
            st.markdown("### Hızlı Giriş")
            otp_e = st.text_input("Email", key="otp_e")
            
            if not st.session_state["otp_sent"]:
                if st.button("Kod Gönder"):
                    try:
                        supabase.auth.sign_in_with_otp({"email": otp_e})
                        st.session_state["otp_sent"] = True
                        st.session_state["otp_email_cache"] = otp_e
                        st.rerun()
                    except Exception as e: st.error(str(e))
            else:
                st.success(f"Kod gönderildi: {st.session_state['otp_email_cache']}")
                code = st.text_input("6 Haneli Kod")
                if st.button("Doğrula"):
                    try:
                        res = supabase.auth.verify_otp({"email": st.session_state["otp_email_cache"], "token": code, "type": "magiclink"})
                        st.session_state["user"] = res.user
                        st.session_state["otp_sent"] = False
                        st.rerun()
                    except: st.error("Hatalı Kod")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- MODERN NAV (Light Theme) ---
    selected = option_menu(
        menu_title=None,
        options=["Ana Sayfa", "Evcil Hayvanlarım", "Ayarlar"],
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

    # --- VIEW: HOME ---
    if selected == "Ana Sayfa":
        c1, c2 = st.columns([3, 1])
        c1.subheader(f"👋 Merhaba")
        if c2.button("➕ Ekle", type="primary"):
            existing = list(df["pet_name"].unique()) if not df.empty else []
            add_vaccine_dialog(existing)

        if df.empty:
            st.info("Hoşgeldiniz! Henüz bir kayıt yok.")
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            today = date.today()
            
            # STATS
            k1, k2, k3 = st.columns(3)
            # Custom styled metric container using HTML
            def styled_metric(label, value, color="#1A202C"):
                st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:12px; border:1px solid #E2E8F0; text-align:center;">
                    <div style="color:#718096; font-size:13px; font-weight:600; margin-bottom:5px;">{label}</div>
                    <div style="color:{color}; font-size:24px; font-weight:800;">{value}</div>
                </div>
                """, unsafe_allow_html=True)

            with k1: styled_metric("Toplam Pet", df['pet_name'].nunique())
            upcoming = df[df["next_due_date"] > today]
            with k2: styled_metric("Yaklaşan", len(upcoming))
            overdue = df[df["next_due_date"] < today]
            with k3: styled_metric("Gecikmiş", len(overdue), "#FF4B4B")
            
            st.write("")
            st.write("")
            
            urgent = df[df["next_due_date"] <= (today + timedelta(days=7))].sort_values("next_due_date")
            
            if not urgent.empty:
                st.caption("🚨 ACİL DURUMLAR")
                for _, row in urgent.iterrows():
                    days = (row['next_due_date'] - today).days
                    if days < 0:
                        colors = ("#FFF5F5", "#C53030") # Red bg, Red text
                        msg = f"{abs(days)} GÜN GEÇTİ"
                    elif days <= 3:
                        colors = ("#FFFAF0", "#C05621") # Orange
                        msg = f"{days} GÜN KALDI"
                    else:
                        colors = ("#F0FFF4", "#2F855A") # Green
                        msg = f"{days} GÜN VAR"
                    
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
                st.success("Harika! Önümüzdeki 7 gün içinde acil bir durum yok.")

    # --- VIEW: PETS ---
    elif selected == "Evcil Hayvanlarım":
        if df.empty:
            st.warning("Profil bulunamadı.")
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            df["date_applied"] = pd.to_datetime(df["date_applied"]).dt.date
            pets = df["pet_name"].unique()

            for pet in pets:
                p_df = df[df["pet_name"] == pet].sort_values("date_applied")
                
                # Card Container
                with st.container():
                    c_head1, c_head2 = st.columns([3, 1])
                    c_head1.subheader(f"🐾 {pet}")
                    if c_head2.button("İşlem Ekle", key=f"btn_{pet}"):
                        add_vaccine_dialog(list(pets), default_pet=pet)
                    
                    # Styled Expander (The Card)
                    with st.expander("Detayları Göster", expanded=True):
                        t1, t2, t3 = st.tabs(["Genel", "Geçmiş", "Grafik"])
                        
                        with t1:
                            future = p_df[p_df["next_due_date"] >= date.today()].sort_values("next_due_date")
                            col_a, col_b = st.columns(2)
                            
                            last_w = p_df.iloc[-1]['weight'] if 'weight' in p_df.columns else 0
                            col_a.metric("Kilo", f"{last_w} kg")
                            
                            if not future.empty:
                                nxt = future.iloc[0]
                                col_b.metric("Sıradaki", nxt['vaccine_type'], nxt['next_due_date'].strftime('%d.%m'))
                            else:
                                col_b.metric("Sıradaki", "-")
                                
                            valid_notes = [n for n in p_df["notes"].unique() if n and str(n).strip() != "None" and str(n).strip() != ""]
                            if valid_notes:
                                st.info(f"📝 {valid_notes[-1]}")

                        with t2:
                            edit_df = p_df.copy()
                            edited = st.data_editor(
                                edit_df,
                                column_config={
                                    "id": None, "user_id": None, "created_at": None, "pet_name": None,
                                    "vaccine_type": "Aşı",
                                    "date_applied": st.column_config.DateColumn("Yapıldı", format="DD.MM.YYYY"),
                                    "next_due_date": st.column_config.DateColumn("Bitiş", format="DD.MM.YYYY"),
                                    "weight": st.column_config.NumberColumn("Kg", format="%.1f"),
                                    "notes": "Not"
                                },
                                hide_index=True,
                                use_container_width=True,
                                key=f"editor_{pet}"
                            )
                            if not edited.equals(p_df):
                                if st.button("Değişiklikleri Kaydet", key=f"save_{pet}"):
                                    try:
                                        recs = edited.to_dict('records')
                                        for r in recs:
                                            r['date_applied'] = str(r['date_applied'])
                                            r['next_due_date'] = str(r['next_due_date'])
                                        supabase.table("vaccinations").upsert(recs).execute()
                                        st.success("Güncellendi!")
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

    # --- VIEW: SETTINGS ---
    elif selected == "Ayarlar":
        st.title("Ayarlar")
        st.write(f"Giriş: {st.session_state['user'].email}")
        
        if st.button("Çıkış Yap", type="secondary"): logout()
        
        st.write("---")
        with st.expander("Şifre Değiştir"):
            new_p = st.text_input("Yeni Şifre", type="password")
            if st.button("Güncelle"):
                try:
                    supabase.auth.update_user({"password": new_p})
                    st.success("Başarılı!")
                except Exception as e: st.error(str(e))
