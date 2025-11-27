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

# --- CSS: DESIGN SYSTEM (Inter Font + Soft Coral) ---
st.markdown("""
<style>
    /* Import Inter Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main Background */
    .stApp { background-color: #0E1117; }
    
    /* Text Colors */
    h1, h2, h3, h4, h5, h6, p, div, span, li, label { color: #F0F2F6 !important; }
    
    /* BRAND COLOR: Soft Coral (#FF6B6B) */
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1F2026 !important; }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: #262730 !important; color: white !important; border: 1px solid #444 !important; border-radius: 8px;
    }
    
    /* Dropdowns */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #262730 !important;
    }
    li[role="option"] { background-color: #262730 !important; color: white !important; }
    li[role="option"]:hover { background-color: #FF6B6B !important; color: white !important; }
    div[data-baseweb="select"] > div {
        background-color: #262730 !important; color: white !important; border: 1px solid #444 !important;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #FF6B6B !important; color: white !important; border: none; font-weight: 600; border-radius: 8px;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover { background-color: #FF5252 !important; box-shadow: 0 4px 12px rgba(255,107,107,0.3); }

    /* Cards (Expanders) - FIXING THE GREY HEADER */
    div[data-testid="stExpander"] { background-color: transparent; border: none; }
    .streamlit-expanderHeader { 
        background-color: #262730 !important; 
        color: white !important; 
        border: 1px solid #444; 
        border-radius: 8px;
    }
    .streamlit-expanderHeader:hover {
        border-color: #FF6B6B !important; /* Glow effect on hover */
    }
    .streamlit-expanderHeader p { font-weight: 600; font-size: 16px; }

    /* Tables & Charts */
    [data-testid="stDataFrame"] { background-color: #262730; border-radius: 8px; }
    .js-plotly-plot .plotly .main-svg { background-color: transparent !important; }
    
    /* Utilities */
    div[data-testid="InputInstructions"] { display: none !important; }
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
    st.caption("Evcil hayvanlarınızın sağlığını takip etmenin en kolay yolu.")
    st.write("")
    
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        # WRAPPING IN FORM ENABLES ENTER KEY SUBMISSION
        with st.form("login_form"):
            e = st.text_input("Email")
            p = st.text_input("Şifre", type="password")
            st.write("") 
            # form_submit_button is required inside form
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
    # --- LOGGED IN DASHBOARD ---
    with st.sidebar:
        st.write(f"👤 {st.session_state['user'].email}")
        if st.button("Çıkış Yap", use_container_width=True): logout()
    
    st.sidebar.title("🐾 PatiCheck")
    menu = st.sidebar.radio("Menü", ["Genel Bakış", "Yeni Kayıt"])

    # Load Data
    rows = supabase.table("vaccinations").select("*").execute().data
    df = pd.DataFrame(rows)

    if menu == "Genel Bakış":
        st.header("🐶🐱 Evcil Hayvan Profilleri")
        
        if df.empty:
            # ONBOARDING (Empty State)
            st.container(border=True).markdown("""
            ### 👋 Hoşgeldin!
            Henüz bir kayıt bulunamadı.
            
            Sağlık takibine başlamak için sol menüden **'Yeni Kayıt'** seçeneğine tıklayın.
            """)
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"])
            df = df.sort_values("next_due_date")
            pets = df["pet_name"].unique()

            for pet in pets:
                p_df = df[df["pet_name"] == pet]
                due = p_df["next_due_date"].min()
                days = (due.date() - date.today()).days
                
                status = "✅ Durum İyi"
                if days < 7: status = f"🚨 {days} Gün Kaldı!"
                elif days < 30: status = f"⚠️ Yaklaşıyor ({days} Gün)"

                with st.expander(f"{pet} | {status}"):
                    c1, c2 = st.columns(2)
                    last_weight = p_df.iloc[-1]['weight'] if 'weight' in p_df.columns else 0
                    c1.metric("Son Kilo", f"{last_weight} kg")
                    c1.metric("Sıradaki İşlem", p_df.iloc[0]['vaccine_type'])
                    
                    st.write("---")
                    
                    # CHART WITH EXPLANATION
                    if len(p_df) > 0:
                        st.subheader("📉 Kilo Geçmişi")
                        st.caption(f"{pet} isimli dostunuzun zaman içindeki kilo değişim grafiği.")
                        
                        chart_df = p_df.copy()
                        chart_df["date_applied"] = pd.to_datetime(chart_df["date_applied"])
                        chart_df = chart_df.sort_values("date_applied")

                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=chart_df["date_applied"], 
                            y=chart_df["weight"],
                            mode='lines+markers',
                            line=dict(color='#FF6B6B', width=3, shape='spline'), # Using Brand Color
                            marker=dict(size=8, color='#0E1117', line=dict(color='#FF6B6B', width=2)),
                            fill='tozeroy',
                            fillcolor='rgba(255, 107, 107, 0.1)',
                            name='Kilo',
                            hovertemplate='<b>Tarih:</b> %{x|%d.%m.%Y}<br><b>Kilo:</b> %{y} kg<extra></extra>' # Cleaner Tooltip
                        ))
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
                    # Table
                    disp = p_df[["vaccine_type", "next_due_date"]].copy()
                    disp.columns = ["Yapılacak İşlem", "Tarih"]
                    # Format date in table
                    disp["Tarih"] = disp["Tarih"].dt.strftime('%d.%m.%Y')
                    st.dataframe(disp, hide_index=True, use_container_width=True)

    elif menu == "Yeni Kayıt":
        st.header("💉 Yeni Giriş")
        
        # New Feature: If you have images, you can uncomment this line later
        # st.image("assets/banner.png", use_column_width=True)
        
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
            m = 12 if "Yıl" in dur else int(dur.split()[0])
            d2 = d1 + timedelta(days=m*30)
            st.info(f"Sonraki Tarih: {d2.strftime('%d.%m.%Y')}")

        if st.button("Kaydet", type="primary"):
            data = {
                "user_id": st.session_state["user"].id,
                "pet_name": pet, "vaccine_type": vac,
                "date_applied": str(d1), "next_due_date": str(d2), "weight": w
            }
            supabase.table("vaccinations").insert(data).execute()
            st.success("✅ Kayıt Başarıyla Eklendi!")
            time.sleep(0.5)
            st.rerun()
