import streamlit as st
import pandas as pd
import json
import os
import requests
import plotly.express as px
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero) ---
st.set_page_config(page_title="Sistema Financiero - Adrián", layout="wide", page_icon="💰")

# Estilos visuales
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

# --- 2. FUNCIONES DE APOYO ---
def parse_date(date_obj):
    if not date_obj: return datetime.now()
    if isinstance(date_obj, dict) and '$date' in date_obj:
        return datetime.fromtimestamp(date_obj['$date'] / 1000)
    return datetime.now()

def save_data(data):
    # Nota: En Streamlit Cloud, el guardado en el archivo local es temporal.
    pass

# --- 3. SISTEMA DE SEGURIDAD (Loggeo) ---
def check_password():
    def password_entered():
        if st.session_state["username"] == "ttoty13" and st.session_state["password"] == "922292":
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

# --- 4. LÓGICA PRINCIPAL DEL DASHBOARD ---
if check_password():
    
    # Botón lateral para salir
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["password_correct"] = False
        st.rerun()

    # Inicialización preventiva de variables (Evita el error 'investments not defined')
    JSON_FILE = 'backup-finanzas-17741715347314445276-2026-01-02.json'
    root_data = {}
    piggy_banks = []
    investments = []
    categories = []

    # Carga de datos
    if not os.path.exists(JSON_FILE):
        st.error(f"No se encontró el archivo de datos: {JSON_FILE}")
    else:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            st.session_state.data = json.load(f)
        
        root_data = st.session_state.data.get('data', {})
        piggy_banks = root_data.get('piggyBanks', [])
        investments = root_data.get('investments', [])
        categories = root_data.get('categories', [])

    # --- RENDERIZADO DE LA INTERFAZ ---
    st.title("💰 Mi Panel Financiero")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen", "💸 Gastos", "🏦 Cuentas", "⚙️ Configuración"])

    with tab1:
        st.subheader("Estado de Activos")
        if piggy_banks:
            df_pb = pd.DataFrame(piggy_banks)
            # Aseguramos que amount sea numérico
            df_pb['amount'] = pd.to_numeric(df_pb['amount'], errors='coerce').fillna(0)
            
            saldos = df_pb.groupby('currency')['amount'].sum()
            cols = st.columns(len(saldos) if len(saldos) > 0 else 1)
            for i, (moneda, total) in enumerate(saldos.items()):
                cols[i].metric(label=f"Total {moneda}", value=f"${total:,.2f}")
            
            fig = px.pie(df_pb, values='amount', names='currency', title="Distribución por Moneda")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de cuentas para mostrar en el resumen.")

    with tab2:
        st.subheader("Flujo de Fondos")
        st.write("Aquí se mostrarán los movimientos y categorías de gastos.")
        # Podés agregar aquí tu lógica de filtrado de fechas si la tenés

    with tab3:
        st.subheader("Detalle de Cuentas (PiggyBanks)")
        if piggy_banks:
            st.dataframe(pd.DataFrame(piggy_banks)[['name', 'amount', 'currency', 'type']], use_container_width=True)
        else:
            st.warning("No hay cuentas registradas.")

    with tab4:
        st.subheader("⚙️ Configuración de Datos")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.write("**Inversiones**")
            if investments:
                ed_i = st.data_editor(pd.DataFrame(investments), column_order=["name", "currency", "order"], num_rows="dynamic", key="cfg_i")
                if st.button("💾 Guardar Inv."):
                    root_data['investments'] = ed_i.to_dict('records')
                    st.success("Cambios preparados (Ver nota de guardado)")
            else:
                st.write("Sin inversiones definidas.")

        with c2:
            st.write("**Balance / Categorías**")
            if categories:
                ed_c = st.data_editor(pd.DataFrame(categories), column_order=["name", "currency", "order"], num_rows="dynamic", key="cfg_c")
                if st.button("💾 Guardar Bal."):
                    root_data['categories'] = ed_c.to_dict('records')
                    st.success("Cambios preparados")

        with c3:
            st.write("**PiggyBanks**")
            if piggy_banks:
                ed_pb = st.data_editor(pd.DataFrame(piggy_banks), column_order=["name", "type", "currency", "id"], num_rows="dynamic", key="cfg_pb")
                if st.button("💾 Guardar Cuentas"):
                    root_data['piggyBanks'] = ed_pb.to_dict('records')
                    st.success("Cambios preparados")
