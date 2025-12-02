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

# --- CSS: DESIGN SYSTEM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, h1, h2, h3, h4, h5, h6, p, a, button, input, label, li, textarea, div {
        font-family: 'Inter', sans-serif !important;
    }
    i, .material-icons { font-family: 'Material Icons' !important; }

    .stApp { background-color: #0E1117; }
    h1, h2, h3, h4, h5, h6, p, label, li { color: #E0E0E0 !important; }
    [data-testid="stMetricValue"] div { color: #FFFFFF !important; }
    [data-testid="stMetricLabel"] label { color: #FF6B6B !important; }
    [data-testid="stSidebar"] { background-color: #1F2026 !important; }
    
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #262730 !important; color: white !important; border: 1px solid #444 !important; border-radius: 8px;
    }
    
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] { background-color: #262730 !important; }
    li[role="option"] { background-color: #262730 !important; color: white !important; }
    li[role="option"]:hover { background-color: #FF6B6B !important; color: white !important; }
    div[data-baseweb="select"] > div { background-color: #262730 !important; color: white !important; border-color: #444 !important; }

    div.stButton > button {
        background-color: #FF6B6B !important; color: white !important; border: none; font-weight: 600; border-radius: 8px;
    }
    div.stButton > button:hover { background-color: #FF5252 !important; }

    .streamlit-expanderHeader {
        background-color: #1F2026 !important; border: 1px solid #333; border-radius: 8px; color: white !important;
    }
    .streamlit-expanderHeader p { color: white !important; font-size: 16px; font-weight: 600; }
    div[data-testid="stExpander"] { border: none; }

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
            st.success("Kayıt oluşturuldu!")
            st.warning("⚠️ Lütfen SPAM/Gereksiz klasörünüzü kontrol edin.")
            st.info("Email adresinize gelen linke tıklayarak hesabınızı onaylayın.")
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")

def resend_confirmation(email):
    try:
        supabase.auth.resend_otp({"type": "signup", "email": email})
        st.success(f"{email} adresine onay maili tekrar gönderildi.")
    except Exception as e:
        st.error(f"Hata: {e} (Lütfen bekleyip tekrar deneyin)")

def reset_password(email):
    try:
        # Added redirect_to to ensure it knows where to send the user back
        # We use the generic streamlit URL, or you can hardcode your specific app url
        supabase.auth.reset_password_email(email, options={"redirect_to": "https://paticheck.streamlit.app"})
        st.success("Şifre sıfırlama linki email adresinize gönderildi (Spam klasörünü kontrol edin).")
    except Exception as e:
        st.error(f"Hata: {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

# --- DATA LOGIC ---
def update_entries(edited_df):
    try:
        records = edited_df.to_dict('records')
        for r in records:
            r['date_applied'] = str(r['date_applied'])
            r['next_due_date'] = str(r['next_due_date'])
            
        supabase.table("vaccinations").upsert(records).execute()
        st.success("✅ Değişiklikler kaydedildi!")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Güncelleme Hatası: {e}")

# --- APP FLOW ---
if st.session_state["user"] is None:
    st.title("🐾 PatiCheck")
    
    tab1, tab2, tab3 = st.tabs(["Giriş Yap", "Kayıt Ol", "Şifremi Unuttum"])
    
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
        
        st.write("---")
        st.caption("Mail gelmedi mi?")
        resend_email = st.text_input("Email Adresi", key="resend_mail", placeholder="Onay maili gelmeyen adres")
        if st.button("Onay Mailini Tekrar Gönder"):
            if resend_email: resend_confirmation(resend_email)
            else: st.warning("Lütfen email adresi girin.")

    with tab3:
        st.write("Şifrenizi sıfırlamak için email adresinizi girin.")
        reset_email = st.text_input("Email", key="reset_mail")
        if st.button("Sıfırlama Linki Gönder", type="primary"):
            if reset_email: reset_password(reset_email)
            else: st.warning("Email adresi gerekli.")

else:
    # --- LOGGED IN ---
    with st.sidebar:
        st.write(f"👤 {st.session_state['user'].email}")
        if st.button("Çıkış Yap", use_container_width=True): logout()
    
    st.sidebar.title("🐾 PatiCheck")
    menu = st.sidebar.radio("Menü", ["Anasayfa", "Evcil Hayvanlar", "Yeni Kayıt"])

    rows = supabase.table("vaccinations").select("*").execute().data
    df = pd.DataFrame(rows)

    # --- HOME PAGE (DASHBOARD) ---
    if menu == "Anasayfa":
        st.header("👋 Hoşgeldiniz!")
        st.write("PatiCheck ile evcil hayvanlarınızın takibini kolayca yapın.")
        
        if df.empty:
            st.info("Henüz bir kayıt oluşturmadınız. Başlamak için 'Yeni Kayıt' menüsünü kullanın.")
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            today = date.today()
            
            # KPI Cards
            col1, col2, col3 = st.columns(3)
            
            pet_count = df["pet_name"].nunique()
            col1.metric("Evcil Hayvan", f"{pet_count} Adet")
            
            upcoming = df[
                (df["next_due_date"] >= today) & 
                (df["next_due_date"] <= today + timedelta(days=30))
            ]
            col2.metric("Yaklaşan Aşılar", f"{len(upcoming)} Adet")
            
            overdue = df[df["next_due_date"] < today]
            col3.metric("Gecikmiş", f"{len(overdue)} Adet", delta_color="inverse")
            
            st.write("---")
            st.subheader("⚠️ Durum Özeti")
            
            if not overdue.empty:
                st.error(f"Dikkat! {len(overdue)} adet gecikmiş işleminiz var.")
                st.dataframe(overdue[["pet_name", "vaccine_type", "next_due_date"]], hide_index=True)
            elif not upcoming.empty:
                st.success(f"Önümüzdeki 30 gün içinde {len(upcoming)} aşı planlanıyor.")
                st.dataframe(upcoming[["pet_name", "vaccine_type", "next_due_date"]], hide_index=True)
            else:
                st.success("Harika! Yakın zamanda yapılması gereken bir işlem görünmüyor.")

    # --- PET PROFILES ---
    elif menu == "Evcil Hayvanlar":
        st.header("🐶🐱 Profil ve Geçmiş")
        
        if df.empty:
            st.info("Kayıt yok.")
        else:
            df["next_due_date"] = pd.to_datetime(df["next_due_date"]).dt.date
            df["date_applied"] = pd.to_datetime(df["date_applied"]).dt.date
            df = df.sort_values("next_due_date")
            pets = df["pet_name"].unique()

            for pet in pets:
                p_df = df[df["pet_name"] == pet]
                today = date.today()
                closest_date = p_df["next_due_date"].min()
                days_until = (closest_date - today).days
                
                status = "✅ Durum İyi"
                if days_until < 0: status = f"⚠️ Gecikti!"
                elif days_until < 7: status = f"🚨 {days_until} Gün Kaldı!"
                elif days_until < 30: status = f"⚠️ Yaklaşıyor"

                future_vax = p_df[p_df["next_due_date"] >= today]
                future_vax = future_vax.sort_values("next_due_date")

                with st.expander(f"{pet} | {status}"):
                    c1, c2 = st.columns(2)
                    last_weight = p_df.iloc[-1]['weight'] if 'weight' in p_df.columns else 0
                    c1.metric("Son Kilo", f"{last_weight} kg")
                    
                    with c2:
                        st.caption("Sıradaki İşlemler")
                        if not future_vax.empty:
                            for _, row in future_vax.head(3).iterrows():
                                v_name = row['vaccine_type']
                                v_date = row['next_due_date'].strftime('%d.%m.%Y')
                                st.markdown(f"""<div style="margin-bottom: 8px; font-size: 15px; display: flex; align-items: center;">
                                        <span style="color: #FFFFFF; font-weight: 600; margin-right: 10px;">{v_name}</span>
                                        <span style="color: #FF6B6B; font-weight: bold;">{v_date}</span>
                                    </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown("✅ *Planlanan işlem yok*")
                    
                    st.write("---")
                    
                    notes_df = p_df.sort_values("date_applied", ascending=False)
                    valid_notes = [n for n in notes_df["notes"].unique() if n and str(n).strip() != "None" and str(n).strip() != ""]
                    if valid_notes:
                        st.info(f"ℹ️ **Veteriner / Not:** {valid_notes[0]}")

                    st.write("---")
                    
                    if len(p_df) > 0:
                        st.subheader("📉 Kilo Geçmişi")
                        st.caption(f"{pet} için kilo değişim grafiği.")
                        chart_df = p_df.sort_values("date_applied")

                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=chart_df["date_applied"], y=chart_df["weight"],
                            mode='lines+markers', line=dict(color='#FF6B6B', width=3, shape='spline'),
                            marker=dict(size=8, color='#0E1117', line=dict(color='#FF6B6B', width=2)),
                            fill='tozeroy', fillcolor='rgba(255, 107, 107, 0.1)', name='Kilo',
                            hovertemplate='<b>Tarih:</b> %{x|%d.%m.%Y}<br><b>Kilo:</b> %{y} kg<extra></extra>'
                        ))
                        if len(chart_df) == 1:
                            val = chart_df["weight"].iloc[0]
                            fig.add_hline(y=val, line_dash="dot", line_color="#444", annotation_text="Başlangıç", annotation_position="top right")

                        fig.update_layout(
                            height=250, margin=dict(t=10,b=0,l=0,r=0), 
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=False, showline=False, tickformat="%d.%m"),
                            yaxis=dict(showgrid=True, gridcolor='#262730', zeroline=False),
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    st.write("---")
                    
                    st.caption("📜 Geçmiş İşlemler (Düzenlemek için hücreye tıklayın)")
                    edit_df = p_df.copy()
                    
                    edited_data = st.data_editor(
                        edit_df,
                        column_config={
                            "id": None, "user_id": None, "created_at": None,
                            "pet_name": st.column_config.TextColumn("İsim", disabled=True),
                            "vaccine_type": "Aşı Tipi",
                            "date_applied": st.column_config.DateColumn("Yapılan Tarih", format="DD.MM.YYYY"),
                            "next_due_date": st.column_config.DateColumn("Sonraki Tarih", format="DD.MM.YYYY"),
                            "weight": st.column_config.NumberColumn("Kilo", format="%.1f"),
                            "notes": "Notlar"
                        },
                        hide_index=True, use_container_width=True, key=f"editor_{pet}"
                    )
                    
                    if not edited_data.equals(p_df):
                        if st.button("💾 Değişiklikleri Kaydet", key=f"save_{pet}"):
                            update_entries(edited_data)

    elif menu == "Yeni Kayıt":
        st.header("💉 Yeni Giriş")
        
        # Initialize key for clear functionality
        if 'w_input' not in st.session_state: st.session_state.w_input = None
        
        c1, c2 = st.columns(2)
        existing_pets = list(df["pet_name"].unique()) if not df.empty else []
        opts = existing_pets + ["➕ Yeni Ekle..."]
        
        with c1:
            sel = st.selectbox("Evcil Hayvan", opts)
            pet = st.text_input("İsim") if sel == "➕ Yeni Ekle..." else sel
            
            vaccine_list = ["Karma", "Kuduz", "Lösemi", "İç Parazit", "Dış Parazit", "Bronşin", "Lyme", "Check-up"]
            vac = st.selectbox("İşlem", vaccine_list)
            
            # FIX: Weight Input with value=None for blank start
            w = st.number_input("Kilo (kg) - Sadece rakam", step=0.1, key="weight_val", value=st.session_state.w_input, placeholder="0.0")
            
            if st.button("Kilo Sıfırla"):
                st.session_state.w_input = None
                st.rerun()

        with c2:
            d1 = st.date_input("Uygulama Tarihi")
            
            # FIX: Manual Date Logic
            mode = st.radio("Tarih Hesaplama", ["Otomatik (Süre Seç)", "Manuel (Tarih Seç)"], horizontal=True, label_visibility="collapsed")
            
            if mode == "Otomatik (Süre Seç)":
                dur = st.selectbox("Süre", ["1 Ay", "2 Ay", "1 Yıl"])
                if "Yıl" in dur: m = 12
                else: m = int(dur.split()[0])
                d2 = d1 + timedelta(days=m*30)
            else:
                d2 = st.date_input("Sonraki Tarih", min_value=d1)
                
            st.info(f"Sonraki Tarih: {d2.strftime('%d.%m.%Y')}")
            
            notes = st.text_area("Notlar / Veteriner Bilgisi (Opsiyonel)", placeholder="Sadece yeni bilgi varsa yazın.")

        if st.button("Kaydet", type="primary"):
            # Ensure weight is not None before saving
            final_w = w if w is not None else 0.0
            
            data = {
                "user_id": st.session_state["user"].id,
                "pet_name": pet, "vaccine_type": vac,
                "date_applied": str(d1), "next_due_date": str(d2), "weight": final_w,
                "notes": notes
            }
            supabase.table("vaccinations").insert(data).execute()
            st.success("✅ Kayıt Başarıyla Eklendi!")
            time.sleep(0.5)
            st.rerun()
