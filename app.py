import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from supabase import create_client
import time

# --- CONFIG ---
st.set_page_config(page_title="PatiCheck", page_icon="🐾", layout="wide")

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

# --- CSS: SURGICAL FIXES (Protects Icons, Fixes Colors) ---
st.markdown("""
<style>
    /* 1. IMPORT INTER FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* 2. APPLY FONT SAFELY (Exclude icons) */
    html, body, h1, h2, h3, h4, h5, h6, p, div, label, span, button, input {
        font-family: 'Inter', sans-serif !important;
    }
    /* Protect Material Icons (The arrows) from font overrides */
    i, .material-icons {
        font-family: 'Material Icons' !important;
    }

    /* 3. MAIN BACKGROUND */
    .stApp { background-color: #0E1117; }
    
    /* 4. TEXT COLORS (High Contrast) */
    h1, h2, h3, h4, h5, h6, p, label, li { color: #E0E0E0 !important; }
    
    /* 5. METRICS (Fixing the Grey-on-Grey issue) */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important; /* Bright White for numbers */
    }
    [data-testid="stMetricLabel"] {
        color: #B0B0B0 !important; /* Light Grey for labels */
    }

    /* 6. SIDEBAR */
    [data-testid="stSidebar"] { background-color: #1F2026 !important; }
    
    /* 7. INPUTS */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #262730 !important; 
        color: white !important; 
        border: 1px solid #444 !important; 
        border-radius: 8px;
    }
    
    /* 8. DROPDOWNS */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #262730 !important;
    }
    li[role="option"] { background-color: #262730 !important; color: white !important; }
    li[role="option"]:hover { background-color: #FF6B6B !important; color: white !important; }
    div[data-baseweb="select"] > div {
        background-color: #262730 !important; color: white !important; border-color: #444 !important;
    }

    /* 9. BUTTONS */
    div.stButton > button {
        background-color: #FF6B6B !important; 
        color: white !important; 
        border: none; 
        font-weight: 600; 
        border-radius: 8px;
    }
    div.stButton > button:hover { background-color: #FF5252 !important; }

    /* 10. EXPANDER HEADER FIX */
    .streamlit-expanderHeader {
        background-color: #262730 !important;
        border: 1px solid #444;
        border-radius: 8px;
        color: white !important;
    }
    /* Force text inside header to be white */
    .streamlit-expanderHeader p { color: white !important; font-size: 16px; font-weight: 600; }
    div[data-testid="stExpander"] { border: none; }

    /* 11. UTILITIES */
    [data-testid="stDataFrame"] { background-color: #262730; border-radius: 8px; }
    div[data-testid="InputInstructions"] { display: none !important; }
    .js-plotly-plot .plotly .main-svg { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

if not supabase:
    st.error("Lütfen Streamlit Secrets ayarlarını yapınız.")
    st.stop()

# --- AUTH LOGIC ---
if "user" not in st.session_state:
    st.session_state["user"] = None

def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"] = res.user
        st.success("Giriş Başarılı!")
        time.sleep(0.5)
        st.rerun()
    except Exception as e:
        msg = str(e)
        if "Email not confirmed" in msg:
            st.error("Lütfen önce email adresinize gelen onay linkine tıklayın.")
        else:
            st.error(f"Giriş Hatası: {msg}")

def register(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            st.success("Kayıt oluşturuldu! Lütfen email adresinize gelen onay linkine tıklayın.")
            st.info("Onayladıktan sonra 'Giriş Yap' sekmesinden giriş yapabilirsiniz.")
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

# --- APP FLOW ---
if st.session_state["user"] is None:
    st.title("🐾 PatiCheck")
    
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        with st.form("login_form"):
            e = st.text_input("Email")
            p = st.text_input("Şifre", type="password")
            st.write("") 
            if st.form_submit_button("Giriş Yap", type="primary", use_container_width=True): 
                login(e, p)
            
    with tab2:
        with st.form("register_form"):
            ne = st.text_input("Email")
            np = st.text_input("Şifre", type="password")
            st.write("")
            if st.form_submit_button("Kayıt Ol", type="primary", use_container_width=True): 
                register(ne, np)

else:
    with st.sidebar:
        st.write(f"👤 {st.session_state['user'].email}")
        if st.button("Çıkış Yap", use_container_width=True): logout()
    
    st.sidebar.title("🐾 PatiCheck")
    menu = st.sidebar.radio("Menü", ["Genel Bakış", "Yeni Kayıt"])

    rows = supabase.table("vaccinations").select("*").execute().data
    df = pd.DataFrame(rows)

    if menu == "Genel Bakış":
        st.header("🐶🐱 Evcil Hayvan Profilleri")
        
        if df.empty:
            st.container(border=True).markdown("### 👋 Hoşgeldin!\nHenüz bir kayıt bulunamadı. Sağlık takibine başlamak için sol menüden **'Yeni Kayıt'** seçeneğine tıklayın.")
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"])
            df = df.sort_values("next_due_date")
            pets = df["pet_name"].unique()

            for pet in pets:
                p_df = df[df["pet_name"] == pet]
                
                # --- LOGIC: MULTIPLE UPCOMING VACCINES ---
                today = date.today()
                # Find the absolute closest date
                closest_date = p_df["next_due_date"].min()
                days_until = (closest_date.date() - today).days
                
                # Determine Status Color
                status = "✅ Durum İyi"
                if days_until < 7: status = f"🚨 {days_until} Gün Kaldı!"
                elif days_until < 30: status = f"⚠️ Yaklaşıyor ({days_until} Gün)"

                # Find ALL vaccines due on that closest date (or within the next 30 days)
                future_vax = p_df[p_df["next_due_date"] >= pd.Timestamp(today)]
                if not future_vax.empty:
                    # Sort to get closest
                    future_vax = future_vax.sort_values("next_due_date")
                    # Take the top 2-3 unique vaccine names
                    next_names = future_vax["vaccine_type"].unique()[:2] 
                    next_vax_str = ", ".join(next_names)
                    if len(future_vax["vaccine_type"].unique()) > 2:
                        next_vax_str += "..."
                else:
                    next_vax_str = "Planlanan Aşı Yok"

                # --- CARD UI ---
                with st.expander(f"{pet} | {status}"):
                    c1, c2 = st.columns(2)
                    last_weight = p_df.iloc[-1]['weight'] if 'weight' in p_df.columns else 0
                    c1.metric("Son Kilo", f"{last_weight} kg")
                    # Updated Metric to show potentially multiple vaccines
                    c2.metric("Sıradaki İşlemler", next_vax_str, delta=f"{closest_date.strftime('%d.%m.%Y')}", delta_color="off")
                    
                    st.write("---")
                    
                    # SMART VET INFO
                    notes_df = p_df.sort_values("date_applied", ascending=False)
                    valid_notes = [n for n in notes_df["notes"].unique() if n and str(n).strip() != "None" and str(n).strip() != ""]
                    if valid_notes:
                        st.info(f"ℹ️ **Veteriner / Not:** {valid_notes[0]}")

                    st.write("---")
                    
                    # CHART
                    if len(p_df) > 0:
                        st.subheader("📉 Kilo Geçmişi")
                        st.caption(f"{pet} için kilo değişim grafiği.")
                        
                        chart_df = p_df.copy()
                        chart_df["date_applied"] = pd.to_datetime(chart_df["date_applied"])
                        chart_df = chart_df.sort_values("date_applied")

                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=chart_df["date_applied"], 
                            y=chart_df["weight"],
                            mode='lines+markers',
                            line=dict(color='#FF6B6B', width=3, shape='spline'),
                            marker=dict(size=8, color='#0E1117', line=dict(color='#FF6B6B', width=2)),
                            fill='tozeroy',
                            fillcolor='rgba(255, 107, 107, 0.1)',
                            name='Kilo',
                            hovertemplate='<b>Tarih:</b> %{x|%d.%m.%Y}<br><b>Kilo:</b> %{y} kg<extra></extra>'
                        ))
                        if len(chart_df) == 1:
                            val = chart_df["weight"].iloc[0]
                            fig.add_hline(y=val, line_dash="dot", line_color="#444", annotation_text="Başlangıç", annotation_position="top right")

                        fig.update_layout(
                            height=250, 
                            margin=dict(t=10,b=0,l=0,r=0), 
                            paper_bgcolor='rgba(0,0,0,0)', 
                            plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=False, showline=False, tickformat="%d.%m"),
                            yaxis=dict(showgrid=True, gridcolor='#262730', zeroline=False),
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    st.write("---")
                    
                    # TABLE
                    st.caption("📜 Geçmiş İşlemler")
                    disp = p_df[["vaccine_type", "next_due_date"]].copy()
                    disp.columns = ["Yapılan İşlem", "Tarih"]
                    disp["Tarih"] = disp["Tarih"].dt.strftime('%d.%m.%Y')
                    st.dataframe(disp, hide_index=True, use_container_width=True)

    elif menu == "Yeni Kayıt":
        st.header("💉 Yeni Giriş")
        c1, c2 = st.columns(2)
        existing_pets = list(df["pet_name"].unique()) if not df.empty else []
        opts = existing_pets + ["➕ Yeni Ekle..."]
        
        with c1:
            sel = st.selectbox("Evcil Hayvan", opts)
            pet = st.text_input("İsim") if sel == "➕ Yeni Ekle..." else sel
            
            vaccine_list = ["Karma", "Kuduz", "Lösemi", "İç Parazit", "Dış Parazit", "Bronşin", "Lyme", "Check-up"]
            vac = st.selectbox("İşlem", vaccine_list)
            w = st.number_input("Kilo (kg)", step=0.1)

        with c2:
            d1 = st.date_input("Tarih")
            dur = st.selectbox("Süre", ["1 Ay", "2 Ay", "1 Yıl"])
            
            if "Yıl" in dur: m = 12
            else: m = int(dur.split()[0])
            d2 = d1 + timedelta(days=m*30)
            
            st.info(f"Sonraki Tarih: {d2.strftime('%d.%m.%Y')}")
            
            notes = st.text_area("Notlar / Veteriner Bilgisi (Opsiyonel)", 
                                 placeholder="Daha önce girdiyseniz boş bırakabilirsiniz. Sadece yeni bilgi varsa yazın.")

        if st.button("Kaydet", type="primary"):
            data = {
                "user_id": st.session_state["user"].id,
                "pet_name": pet, "vaccine_type": vac,
                "date_applied": str(d1), "next_due_date": str(d2), "weight": w,
                "notes": notes
            }
            supabase.table("vaccinations").insert(data).execute()
            st.success("✅ Kayıt Başarıyla Eklendi!")
            time.sleep(0.5)
            st.rerun()
