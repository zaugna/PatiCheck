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

# --- CSS: THE "NUKE" DARK MODE & UI FIXES ---
st.markdown("""
<style>
    /* 1. Main Background */
    .stApp { background-color: #0E1117; }
    
    /* 2. Text Colors */
    h1, h2, h3, h4, h5, h6, p, div, span, li, label { color: #E0E0E0 !important; }
    
    /* 3. Inputs (Dark Background) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div {
        background-color: #262730 !important; color: white !important; border-color: #444 !important;
    }
    
    /* 4. FIX: HIDE "PRESS ENTER TO APPLY" */
    /* This removes the overlapping text in password fields */
    div[data-testid="InputInstructions"] { display: none !important; }

    /* 5. FIX: BUTTONS */
    /* Forces primary buttons to be Red and readable */
    div.stButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #FF2B2B !important;
    }

    /* 6. Cards & Tables */
    div[data-testid="stExpander"] { background-color: transparent; border: none; }
    .streamlit-expanderHeader { background-color: #262730 !important; color: white !important; border: 1px solid #444; }
    [data-testid="stDataFrame"] { background-color: #262730; }
    
    /* 7. Plotly Chart Background Fix */
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
        st.error(f"Giriş Hatası: {e}")

def register(email, password):
    try:
        # Trigger handles profile creation automatically
        res = supabase.auth.sign_up({"email": email, "password": password})
        
        # Logic Update: If email confirmation is OFF, user is logged in immediately.
        # If ON, they need to check email. 
        # Since we turned it OFF for UX, we check if we got a user object.
        if res.user:
            st.session_state["user"] = res.user
            st.success("Kayıt Başarılı! Giriş yapılıyor...")
            time.sleep(1)
            st.rerun()
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

# --- APP FLOW ---
if st.session_state["user"] is None:
    st.title("🐾 PatiCheck: Giriş")
    
    # LOGIN / REGISTER TABS
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        e = st.text_input("Email", key="l_email")
        p = st.text_input("Şifre", type="password", key="l_pass")
        st.write("") 
        # type="primary" makes it red by default, CSS ensures it stays red
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
                        fig.add_trace(go.Scatter(x=chart_df["date_applied"], y=chart_df["weight"], 
                            mode='lines+markers', line=dict(color='#FF4B4B', shape='spline'), fill='tozeroy'))
                        fig.update_layout(height=200, margin=dict(t=0,b=0,l=0,r=0), 
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#262730'))
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    disp = p_df[["vaccine_type", "next_due_date"]].copy()
                    disp.columns = ["Aşı", "Tarih"]
                    st.dataframe(disp, hide_index=True, use_container_width=True)
        else:
            st.info("Kayıt yok.")

    elif menu == "Yeni Kayıt":
        st.header("💉 Yeni Giriş")
        c1, c2 = st.columns(2)
        opts = list(df["pet_name"].unique()) + ["➕ Yeni Ekle..."] if not df.empty else ["➕ Yeni Ekle..."]
        
        with c1:
            sel = st.selectbox("Pet", opts)
            pet = st.text_input("İsim") if sel == "➕ Yeni Ekle..." else sel
            vac = st.selectbox("İşlem", ["Karma", "Kuduz", "Lösemi", "İç Parazit", "Dış Parazit", "Check-up"])
            w = st.number_input("Kilo", step=0.1)
        with c2:
            d1 = st.date_input("Tarih")
            dur = st.selectbox("Süre", ["1 Ay", "3 Ay", "1 Yıl"])
            m = 12 if "Yıl" in dur else int(dur.split()[0])
            d2 = d1 + timedelta(days=m*30)
            st.info(f"Sonraki: {d2}")

        if st.button("Kaydet", type="primary"):
            data = {
                "user_id": st.session_state["user"].id,
                "pet_name": pet, "vaccine_type": vac,
                "date_applied": str(d1), "next_due_date": str(d2), "weight": w
            }
            supabase.table("vaccinations").insert(data).execute()
            st.success("Kaydedildi!")
            time.sleep(0.5)
            st.rerun()
