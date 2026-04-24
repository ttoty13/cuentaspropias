import streamlit as st
import pandas as pd
import json
import os
import requests
import plotly.express as px
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Sistema Financiero", layout="wide", page_icon="💰")

st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.2rem; }
    .date-red { color: #ff4b4b; font-weight: bold; }
    .pb-header-expense { color: #ff4b4b; font-size: 1.2rem; font-weight: bold; } 
    .pb-header-saving { color: #2ecc71; font-size: 1.2rem; font-weight: bold; } 
    button[data-baseweb="tab"] div p { font-size: 1.1rem !important; font-weight: 500 !important; }
    .stAlert { padding: 0.5rem 1rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE LOGGEO (Capa de Seguridad) ---
def check_password():
    """Retorna True si el usuario ingresó las credenciales correctas."""
    def password_entered():
        if (
            st.session_state["username"] == "ttoty13"
            and st.session_state["password"] == "922292"
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso al Sistema")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Acceso al Sistema")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        st.error("❌ Usuario o contraseña incorrectos.")
        return False
    else:
        return True

# --- 3. EJECUCIÓN DEL SISTEMA ---
if check_password():
    
    # Botón para cerrar sesión en la barra lateral
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- FUNCIONES BASE ORIGINALES ---
    def parse_date(date_obj):
        if not date_obj: return datetime.now()
        if isinstance(date_obj, dict) and '$date' in date_obj:
            return datetime.fromtimestamp(date_obj['$date'] / 1000)
        return datetime.now()

    def save_data(data):
        # Esta función dependerá de cómo estés manejando la escritura en tu entorno
        pass

    # --- CARGA DE DATOS ---
    # Reemplazá con el nombre exacto de tu archivo JSON en GitHub
    JSON_FILE = 'backup-finanzas-17741715347314445276-2026-01-02.json'

    if not os.path.exists(JSON_FILE):
        st.error(f"No se encontró el archivo {JSON_FILE}")
    else:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            st.session_state.data = json.load(f)

        root_data = st.session_state.data.get('data', {})
        piggy_banks = root_data.get('piggyBanks', [])
        investments = root_data.get('investments', [])
        categories = root_data.get('categories', [])

        # --- AQUÍ CONTINÚA TODA TU LÓGICA ORIGINAL DE PESTAÑAS (TABS) ---
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen", "💸 Gastos", "🏦 Cuentas", "⚙️ Configuración"])

        with tab1:
            st.subheader("Estado General")
            # Tu lógica original de métricas y gráficos va aquí...
            if piggy_banks:
                df_pb = pd.DataFrame(piggy_banks)
                saldos = df_pb.groupby('currency')['amount'].sum()
                cols = st.columns(len(saldos))
                for i, (moneda, total) in enumerate(saldos.items()):
                    cols[i].metric(f"Total {moneda}", f"${total:,.2f}")

        with tab2:
            st.subheader("Flujo de Fondos")
            # Tu lógica de movimientos...

        with tab3:
            st.subheader("Mis Cuentas (PiggyBanks)")
            if piggy_banks:
                st.dataframe(pd.DataFrame(piggy_banks)[['name', 'amount', 'currency']])

        with tab4:
            st.subheader("⚙️ Configuración")
            c1, c2, c3 = st.columns(3)
            # Tus editores de datos (investments, categories, piggy_banks)...
            with c1:
                st.write("**Inversiones**")
                # (Mantené aquí el código exacto de tus editores que tenías antes)
