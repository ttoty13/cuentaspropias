import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Financiero - Adrián", page_icon="💰")

# --- 2. FUNCIÓN DE LOGGEO SEGURA ---
def check_password():
    def password_entered():
        # Usamos .get() para evitar el AttributeError si la memoria tarda en cargar
        user = st.session_state.get("username", "")
        pwd = st.session_state.get("password", "")
        
        if user == "ttoty13" and pwd == "922292":
            st.session_state["password_correct"] = True
            # Limpiamos las variables de forma segura
            if "password" in st.session_state:
                del st.session_state["password"]  
            if "username" in st.session_state:
                del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Si ya se validó antes, pasa directo
    if st.session_state.get("password_correct", False):
        return True

    # Pantalla de Login
    st.title("🔐 Acceso al Sistema")
    st.text_input("Usuario", key="username")
    st.text_input("Contraseña", type="password", key="password")
    st.button("Ingresar", on_click=password_entered)
    
    # Mensaje de error si se equivocó
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("❌ Usuario o contraseña incorrectos.")
        
    return False

# --- 3. LÓGICA DEL SISTEMA ---
if check_password():
    
    # Botón para salir y bloquear la app de nuevo
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["password_correct"] = False
        st.rerun()

    JSON_FILE = 'backup-finanzas-17741715347314445276-2026-01-02.json'

    if not os.path.exists(JSON_FILE):
        st.error(f"No se encontró el archivo {JSON_FILE}")
    else:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f).get('data', {})

        st.title("💰 Mi Panel Financiero")
        
        piggy_banks = data.get('piggyBanks', [])
        if piggy_banks:
            df_pb = pd.DataFrame(piggy_banks)
            columnas_disponibles = df_pb.columns.tolist()
            
            if 'currency' in columnas_disponibles and 'amount' in columnas_disponibles:
                # Métricas
                saldos = df_pb.groupby('currency')['amount'].sum()
                cols = st.columns(len(saldos))
                for i, (moneda, total) in enumerate(saldos.items()):
                    cols[i].metric(label=f"Total {moneda}", value=f"${total:,.2f}")

                # Gráfico
                fig = px.pie(df_pb, values='amount', names='currency', title="Distribución por Moneda")
                st.plotly_chart(fig, use_container_width=True)

                # Tabla
                st.subheader("Detalle de Cuentas")
                st.dataframe(df_pb[['name', 'amount', 'currency']], use_container_width=True)
            else:
                st.warning("⚠️ Alerta de Datos: Los nombres de las columnas en tu JSON no coinciden con lo esperado.")
                st.write("**Columnas encontradas:**", columnas_disponibles)
                st.dataframe(df_pb.head())
        else:
            st.warning("No hay datos de cuentas disponibles en el JSON.")
