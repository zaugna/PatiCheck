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
        key = st.secrets["SUPABASE_KEY"] # ANON KEY
        return create_client(url, key)
    except:
        return None

supabase = init_supabase()

# --- CSS: ULTIMATE DARK MODE FIX ---
st.markdown("""
<style>
    /* 1. Main Background */
    .stApp { background-color: #0E1117; }
    
    /* 2. Text Colors (Global) */
    h1, h2, h3, h4, h5, h6, p, div, span, li, label { color: #E0E0E0 !important; }
    
    /* 3. SIDEBAR FIX */
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    [data-testid="stSidebar"] * { color: #E0E0E0 !important; }
    
    /* 4. INPUTS & DROPDOWNS (The Grey Fix) */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: #262730 !important; color: white !important; border-color: #444 !important;
    }
    
    /* 5. DROPDOWN MENU POPUP FIX */
    /* This targets the actual list that pops up */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #262730 !important;
    }
    /* The items inside the list */
    li[role="option"] {
        background-color: #262730 !important;
        color: white !important;
    }
    /* Hover effect */
    li[role="option"]:hover {
        background-color: #FF4B4B !important;
    }
    /* The box before you click it */
    div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: white !important;
        border-color: #444 !important;
    }

    /* 6. BUTTONS */
    div.stButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #FF2B2B !important;
    }

    /* 7. Cards & Tables */
    div[data-testid="stExpander"] { background-color: transparent; border: none; }
    .streamlit-expanderHeader { background-color: #262730 !important; color: white !important; border: 1px solid #444; }
    [data-testid="stDataFrame"] { background-color: #262730; }
    
    /* 8. Plotly Chart Background */
    .js-plotly-plot .plotly .main-svg { background-color: transparent !important; }
    
    /* 9. Hide Password Instructions */
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
        # Provide a clearer error message for unconfirmed emails
        msg = str(e)
        if "Email not confirmed" in msg:
            st.error("Lütfen önce email adresinize gelen onay linkine tıklayın.")
        else:
            st.error(f"Giriş Hatası: {msg}")

def register(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            # FIX: Do NOT auto-login. Force them to check email.
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
    st.title("🐾 PatiCheck: Giriş")
    
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        e = st.text_input("Email", key="l_email")
        p = st.text_input("Şifre", type="password", key="l_pass")
        st.write("") 
        if st.button("Giriş Yap", type="primary", use_container_width=True): 
            login(e, p)
            
    with tab2:
        ne = st.text_input("Email", key="r_email")
        np = st.text_input("Şifre", type="password", key="r_pass")
        st.write("")
        if st.button("Kayıt Ol", type="primary", use_container_width=True): 
            register(ne, np)

else:
    # --- LOGGED IN DASHBOARD ---
    with st.sidebar:
        st.write(f"👤 {st.session_state['user'].email}")
        if st.button("Çıkış Yap"): logout()
    
    st.sidebar.title("🐾 PatiCheck")
    menu = st.sidebar.radio("Menü", ["Genel Bakış", "Yeni Kayıt"])

    # Load Data
    rows = supabase.table("vaccinations").select("*").execute().data
    df = pd.DataFrame(rows)

    if menu == "Genel Bakış":
        st.header("Evcil Hayvan Profilleri")
        if not df.empty:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"])
            df = df.sort_values("next_due_date")
            pets = df["pet_name"].unique()

            for pet in pets:
                p_df = df[df["pet_name"] == pet]
                due = p_df["next_due_date"].min()
                days = (due.date() - date.today()).days
                
                status = "✅ İyi"
                if days < 7: status = f"🚨 {days} Gün!"
                elif days < 30: status = f"⚠️ {days} Gün"

                with st.expander(f"{pet} | {status}"):
                    c1, c2 = st.columns(2)
                    last_weight = p_df.iloc[-1]['weight'] if 'weight' in p_df.columns else 0
                    c1.metric("Son Kilo", f"{last_weight} kg")
                    c1.metric("Sıradaki", p_df.iloc[0]['vaccine_type'])
                    
                    if len(p_df) > 1:
                        # Chart Logic
                        chart_df = p_df.copy()
                        chart_df["date_applied"] = pd.to_datetime(chart_df["date_applied"])
                        chart_df = chart_df.sort_values("date_applied")

                        fig = go.Figure()
                        fig.
