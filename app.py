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

# --- CSS: THE "APP EXPERIENCE" (Glassmorphism & Clean Typography) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* 1. Global Reset */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* 2. App Background */
    .stApp { background-color: #0F1116; }
    
    /* 3. Hide Sidebar & Footer */
    [data-testid="stSidebar"] { display: none; }
    #MainMenu { display: none; }
    footer { display: none; }
    
    /* 4. Typography */
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 800; letter-spacing: -0.5px; }
    p, label, span { color: #A0A4AB !important; }
    
    /* 5. GLASS CARDS */
    div.css-card {
        background-color: #1E212B;
        border: 1px solid #2E323E;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }
    
    /* 6. BUTTONS */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 45px;
        background-color: #FF6B6B;
        color: white;
        border: none;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(255, 107, 107, 0.2);
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #FF5252;
        transform: translateY(-2px);
    }
    button[kind="secondary"] {
        background-color: #2E323E !important;
        border: 1px solid #444 !important;
    }

    /* 7. INPUTS */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #15171E !important;
        color: white !important;
        border: 1px solid #2E323E !important;
        border-radius: 10px;
    }
    /* Dropdown Popups */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] { background-color: #1E212B !important; }
    li[role="option"] { background-color: #1E212B !important; color: white !important; }
    li[role="option"]:hover { background-color: #FF6B6B !important; color: white !important; }
    
    /* 8. TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #1E212B;
        border-radius: 8px;
        color: white;
        border: 1px solid #2E323E;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF6B6B;
        color: white;
    }
    
    /* 9. METRICS */
    [data-testid="stMetricValue"] { font-size: 24px !important; color: white !important; }
    [data-testid="stMetricLabel"] { font-size: 13px !important; color: #888 !important; }
    
    /* 10. PLOTLY FIX */
    .js-plotly-plot .plotly .main-svg { background-color: transparent !important; }
    
    /* 11. HIDE HINTS */
    div[data-testid="InputInstructions"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

if not supabase:
    st.error("Sistem Hatası: Veritabanı bağlantısı kurulamadı.")
    st.stop()

# --- STATE MANAGEMENT ---
if "user" not in st.session_state: st.session_state["user"] = None
if "otp_sent" not in st.session_state: st.session_state["otp_sent"] = False
if "otp_email_cache" not in st.session_state: st.session_state["otp_email_cache"] = ""

# --- MODERN DIALOGS (The "App" Feel) ---
@st.dialog("💉 Yeni Aşı Kaydı")
def add_vaccine_dialog(existing_pets, default_pet=None):
    # Determine Pet Selection
    index = 0
    if default_pet and default_pet in existing_pets:
        index = existing_pets.index(default_pet) + 1 # +1 because of "New..." option
    
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
    
    # RESTORED FEATURE: Manual Date Logic
    mode = st.radio("Hesaplama", ["Otomatik (Süre)", "Manuel Tarih"], horizontal=True, label_visibility="collapsed")
    
    if mode == "Otomatik (Süre)":
        dur = st.pills("Geçerlilik", ["1 Ay", "2 Ay", "3 Ay", "1 Yıl"], default="1 Yıl")
        m = 12 if "Yıl" in dur else int(dur.split()[0])
        d2 = d1 + timedelta(days=m*30)
    else:
        d2 = st.date_input("Bitiş Tarihi", value=d1 + timedelta(days=30))
    
    st.caption(f"📅 Bir Sonraki Tarih: {d2.strftime('%d.%m.%Y')}")
    
    notes = st.text_area("Notlar", height=80, placeholder="Veteriner adı, aşı markası vb...")

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
        else: st.error("Giriş Hatalı.")

def logout():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

# --- ENTRY POINT ---
if st.session_state["user"] is None:
    # LANDING PAGE DESIGN
    st.markdown("<h1 style='text-align: center; color: #FF6B6B !important;'>🐾 PatiCheck</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Evcil hayvanlarınızın sağlığı, kontrol altında.</p>", unsafe_allow_html=True)
    st.write("")
    
    tab1, tab2 = st.tabs(["Giriş Yap", "Kod ile Gir"])
    
    with tab1:
        email = st.text_input("Email", key="l_e")
        password = st.text_input("Şifre", type="password", key="l_p")
        if st.button("Giriş Yap"): login(email, password)
        st.markdown("<br><p style='text-align:center; font-size:12px'>Hesabınız yoksa kod ile giriş yapın, otomatik oluşsun.</p>", unsafe_allow_html=True)

    with tab2:
        st.caption("Şifresiz hızlı giriş (veya kayıt)")
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
            st.success("Kod gönderildi!")
            code = st.text_input("Gelen Kodu Girin")
            if st.button("Doğrula"):
                try:
                    res = supabase.auth.verify_otp({"email": st.session_state["otp_email_cache"], "token": code, "type": "magiclink"})
                    st.session_state["user"] = res.user
                    st.session_state["otp_sent"] = False
                    st.rerun()
                except: st.error("Hatalı Kod")

else:
    # --- APP NAVIGATION ---
    selected = option_menu(
        menu_title=None,
        options=["Ana Sayfa", "Profiller", "Ayarlar"],
        icons=["house-fill", "grid-fill", "gear-fill"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#1E212B", "border-radius": "12px"},
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "color": "#A0A4AB"},
            "nav-link-selected": {"background-color": "#FF6B6B", "color": "white", "font-weight": "600"},
        }
    )

    rows = supabase.table("vaccinations").select("*").execute().data
    df = pd.DataFrame(rows)

    # --- VIEW 1: HOME ---
    if selected == "Ana Sayfa":
        c1, c2 = st.columns([3, 1])
        c1.subheader(f"👋 Merhaba")
        if c2.button("➕ Ekle", type="primary"):
            existing = list(df["pet_name"].unique()) if not df.empty else []
            add_vaccine_dialog(existing)

        if df.empty:
            st.info("Hoşgeldiniz! Henüz bir kayıt yok. 'Ekle' butonuna basarak başlayın.")
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            today = date.today()
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Toplam Pet", df['pet_name'].nunique())
            upcoming = df[df["next_due_date"] > today]
            k2.metric("Yaklaşan", len(upcoming))
            overdue = df[df["next_due_date"] < today]
            k3.metric("Gecikmiş", len(overdue), delta_color="inverse")
            
            st.write("---")
            
            urgent = df[df["next_due_date"] <= (today + timedelta(days=7))].sort_values("next_due_date")
            
            if not urgent.empty:
                st.caption("🚨 ACİL DURUMLAR & YAKLAŞANLAR")
                for _, row in urgent.iterrows():
                    days = (row['next_due_date'] - today).days
                    
                    bg_color = "rgba(255, 75, 75, 0.1)"
                    border_color = "#FF4B4B"
                    msg = f"{abs(days)} GÜN GEÇTİ" if days < 0 else f"{days} GÜN KALDI"
                    
                    st.markdown(f"""
                    <div class="css-card" style="border-left: 4px solid {border_color};">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <h3 style="margin:0; font-size:18px; color:white;">{row['pet_name']} - {row['vaccine_type']}</h3>
                                <p style="margin:0;">{row['next_due_date'].strftime('%d.%m.%Y')}</p>
                            </div>
                            <div style="background:{color}; padding:5px 10px; border-radius:15px; color:white; font-weight:bold; font-size:12px;">
                                {msg}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("Harika! Önümüzdeki 7 gün içinde acil bir durum yok.")

    # --- VIEW 2: PROFILES ---
    elif selected == "Profiller":
        if df.empty:
            st.warning("Profil bulunamadı.")
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            df["date_applied"] = pd.to_datetime(df["date_applied"]).dt.date
            pets = df["pet_name"].unique()

            for pet in pets:
                p_df = df[df["pet_name"] == pet].sort_values("date_applied")
                
                with st.container():
                    c_head1, c_head2 = st.columns([3, 1])
                    c_head1.subheader(f"🐾 {pet}")
                    if c_head2.button("İşlem Ekle", key=f"btn_{pet}"):
                        add_vaccine_dialog(list(pets), default_pet=pet)
                    
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
                                mode='lines+markers', line=dict(color='#FF6B6B', width=3, shape='spline'),
                                fill='tozeroy',
                                hovertemplate='<b>Tarih:</b> %{x|%d.%m.%Y}<br><b>Kilo:</b> %{y} kg<extra></extra>'
                            ))
                            fig.update_layout(height=250, margin=dict(t=10,b=0,l=0,r=0), 
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'))
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                st.write("---")

    # --- VIEW 3: SETTINGS ---
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
