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

# --- CSS: THE "DIRECTOR'S CUT" DESIGN SYSTEM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* 1. TYPOGRAPHY & RESET */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1A202C;
    }
    .stApp { background-color: #F8F9FA; }
    
    /* Strict Font Sizing */
    h1 { font-size: 28px !important; font-weight: 800 !important; letter-spacing: -0.5px; color: #111 !important; }
    h2 { font-size: 22px !important; font-weight: 700 !important; color: #333 !important; }
    h3 { font-size: 18px !important; font-weight: 600 !important; color: #444 !important; }
    p, label, li, span, div { font-size: 14px !important; color: #4A5568; }
    
    /* 2. THE "BOXED" TABS (Restoring the Segmented Control Look) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px; /* Space between tabs */
        background-color: transparent;
        padding: 0px;
        margin-bottom: 10px;
        border: none;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px; /* Boxy look */
        padding: 0 20px;
        color: #718096;
        font-weight: 600;
        flex-grow: 1; /* Stretch to fill width */
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF6B6B;
        color: white !important;
        border-color: #FF6B6B;
        box-shadow: 0 4px 6px rgba(255, 107, 107, 0.3);
    }
    
    /* 3. BUTTONS (Professional & Aligned) */
    div.stButton > button {
        border-radius: 10px;
        height: 42px;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease;
        width: 100%;
    }
    /* Primary Action (Red) */
    button[kind="primary"] {
        background-color: #FF6B6B !important;
        color: white !important;
        box-shadow: 0 2px 5px rgba(255, 107, 107, 0.2);
    }
    button[kind="primary"]:hover {
        background-color: #FA5252 !important;
        transform: translateY(-1px);
    }
    /* Secondary Action (White/Grey) - Used for 'Aşı Ekle' inside cards */
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #2D3748 !important;
        border: 1px solid #CBD5E0 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    button[kind="secondary"]:hover {
        border-color: #FF6B6B !important;
        color: #FF6B6B !important;
        background-color: #FFF5F5 !important;
    }

    /* 4. EXPANDER HEADER (High Visibility) */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        color: #1A202C !important;
        padding: 12px 16px !important;
        margin-top: 10px;
    }
    /* Highlight when hovering or active */
    .streamlit-expanderHeader:hover {
        border-color: #FF6B6B !important;
        background-color: #FFFAFA !important;
    }
    /* Fix text inside header */
    .streamlit-expanderHeader p { 
        font-size: 15px !important; 
        font-weight: 600 !important; 
        color: #2D3748 !important; 
    }
    div[data-testid="stExpander"] { border: none; }
    
    /* 5. CARDS & CONTAINERS */
    /* Clean container for Pet Profile */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 24px;
    }

    /* 6. INPUTS & DROPDOWNS */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #2D3748 !important;
        border: 1px solid #CBD5E0 !important;
        border-radius: 8px;
    }
    
    /* Dropdown Menu Items */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #FFFFFF !important;
    }
    li[role="option"] {
        color: #2D3748 !important;
        background-color: #FFFFFF !important;
    }
    li[role="option"]:hover {
        background-color: #FFF5F5 !important;
        color: #FF6B6B !important;
    }

    /* 7. METRICS */
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #1A202C !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { font-size: 12px !important; color: #718096 !important; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    
    /* 8. PLOTLY CLEANUP */
    .js-plotly-plot .plotly .main-svg { background-color: transparent !important; }
    
    /* 9. UTILS */
    [data-testid="stSidebar"] { display: none; }
    #MainMenu { display: none; }
    footer { display: none; }
    div[data-testid="InputInstructions"] { display: none !important; }
    [data-testid="stDataFrame"] { border: 1px solid #E2E8F0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

if not supabase:
    st.error("Sistem Hatası: Veritabanı bağlantısı kurulamadı.")
    st.stop()

# --- STATE ---
if "user" not in st.session_state: st.session_state["user"] = None
if "otp_sent" not in st.session_state: st.session_state["otp_sent"] = False
if "otp_email_cache" not in st.session_state: st.session_state["otp_email_cache"] = ""

# --- DIALOGS ---
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

# --- ENTRY ---
if st.session_state["user"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #1A202C !important; font-size: 42px !important;'>🐾 PatiCheck</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px !important;'>Evcil hayvanlarınızın sağlığı, kontrol altında.</p>", unsafe_allow_html=True)
    st.write("")
    
    c_login = st.container()
    with c_login:
        # Applying a card style wrapper manually via markdown div is tricky in Streamlit 
        # so we rely on the clean input styles defined in CSS.
        tab1, tab2 = st.tabs(["Giriş Yap", "Kod ile Gir"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Şifre", type="password")
                st.write("")
                if st.form_submit_button("Giriş Yap", type="primary"):
                    login(email, password)
            st.markdown("<p style='text-align:center; font-size:12px !important; color:#888 !important; margin-top:10px;'>Hesabınız yoksa 'Kod ile Gir' sekmesinden kayıt olun.</p>", unsafe_allow_html=True)

        with tab2:
            st.caption("Şifresiz hızlı giriş (veya kayıt)")
            otp_e = st.text_input("Email", key="otp_e")
            
            if not st.session_state["otp_sent"]:
                if st.button("Kod Gönder", type="primary"):
                    try:
                        supabase.auth.sign_in_with_otp({"email": otp_e})
                        st.session_state["otp_sent"] = True
                        st.session_state["otp_email_cache"] = otp_e
                        st.rerun()
                    except Exception as e: st.error(str(e))
            else:
                st.success(f"Kod gönderildi: {st.session_state['otp_email_cache']}")
                code = st.text_input("6 Haneli Kod")
                if st.button("Doğrula", type="primary"):
                    try:
                        res = supabase.auth.verify_otp({"email": st.session_state["otp_email_cache"], "token": code, "type": "magiclink"})
                        st.session_state["user"] = res.user
                        st.session_state["otp_sent"] = False
                        st.rerun()
                    except: st.error("Hatalı Kod")

else:
    # --- NAVIGATION (Bold & Visible) ---
    selected = option_menu(
        menu_title=None,
        options=["Ana Sayfa", "Evcil Hayvanlarım", "Ayarlar"],
        icons=["house-fill", "heart-fill", "gear-fill"],
        default_index=0,
        orientation="horizontal",
        styles={
            # Container border and shadow
            "container": {"padding": "0!important", "background-color": "#FFFFFF", "border-radius": "12px", "border": "1px solid #E2E8F0", "box-shadow": "0 2px 8px rgba(0,0,0,0.03)"},
            # Nav items: Bold and Darker color
            "nav-link": {"font-size": "15px", "text-align": "center", "margin": "0px", "color": "#4A5568", "font-weight": "600"},
            # Selected item: Brand Red
            "nav-link-selected": {"background-color": "#FF6B6B", "color": "white", "font-weight": "700"},
        }
    )

    rows = supabase.table("vaccinations").select("*").execute().data
    df = pd.DataFrame(rows)

    # --- HOME ---
    if selected == "Ana Sayfa":
        # Header Alignment
        c1, c2 = st.columns([3, 1.2])
        with c1:
            st.subheader("👋 Merhaba")
        with c2:
            # Primary Action Button - Aligned to header
            if st.button("➕ Pet / Aşı Ekle", type="primary", use_container_width=True):
                existing = list(df["pet_name"].unique()) if not df.empty else []
                add_vaccine_dialog(existing)

        if df.empty:
            st.info("Hoşgeldiniz! Henüz bir kayıt yok.")
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
                        colors = ("#FFF5F5", "#C53030")
                        msg = f"{abs(days)} GÜN GEÇTİ"
                    elif days <= 3:
                        colors = ("#FFFAF0", "#C05621")
                        msg = f"{days} GÜN KALDI"
                    else:
                        colors = ("#F0FFF4", "#2F855A")
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

    # --- PETS ---
    elif selected == "Evcil Hayvanlarım":
        if df.empty:
            st.warning("Profil bulunamadı.")
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            df["date_applied"] = pd.to_datetime(df["date_applied"]).dt.date
            pets = df["pet_name"].unique()

            for pet in pets:
                p_df = df[df["pet_name"] == pet].sort_values("date_applied")
                
                # --- PET CARD LAYOUT ---
                # We use 'st.container' but styled with CSS to look like a card
                
                # Pet Header Row
                c_head1, c_head2 = st.columns([3, 1.2]) # Adjusted ratio
                with c_head1:
                    st.subheader(f"🐾 {pet}")
                with c_head2:
                    # Stylish Secondary Button
                    if st.button("➕ Aşı Ekle", key=f"btn_{pet}", type="secondary", use_container_width=True):
                        add_vaccine_dialog(list(pets), default_pet=pet)
                
                # The Expander
                with st.expander("Detayları Göster", expanded=True):
                    # TABS (Styled as Segmented Control)
                    t1, t2, t3 = st.tabs(["Genel Bakış", "Geçmiş Kayıtlar", "Kilo Grafiği"])
                    
                    with t1:
                        future = p_df[p_df["next_due_date"] >= date.today()].sort_values("next_due_date")
                        col_a, col_b = st.columns(2)
                        
                        last_w = p_df.iloc[-1]['weight'] if 'weight' in p_df.columns else 0
                        col_a.metric("Güncel Kilo", f"{last_w} kg")
                        
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
                        # Convert to datetime for editor
                        edit_df["date_applied"] = pd.to_datetime(edit_df["date_applied"])
                        
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
                        if not edited.equals(edit_df):
                            if st.button("Değişiklikleri Kaydet", key=f"save_{pet}", type="primary"):
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

    # --- SETTINGS ---
    elif selected == "Ayarlar":
        st.title("Ayarlar")
        st.write(f"Giriş: {st.session_state['user'].email}")
        
        if st.button("Çıkış Yap", type="secondary"): logout()
        
        st.write("---")
        with st.expander("Şifre Değiştir"):
            new_p = st.text_input("Yeni Şifre", type="password")
            if st.button("Güncelle", type="primary"):
                try:
                    supabase.auth.update_user({"password": new_p})
                    st.success("Başarılı!")
                except Exception as e: st.error(str(e))
