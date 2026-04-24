import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Financiero - Adrián", page_icon="💰")

# --- 2. FUNCIÓN DE LOGGEO ---
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

# --- 3. LÓGICA DEL SISTEMA ---
if check_password():
    
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
            
            # --- SISTEMA DE DIAGNÓSTICO ---
            columnas_disponibles = df_pb.columns.tolist()
            
            if 'currency' in columnas_disponibles and 'amount' in columnas_disponibles:
                # Si las columnas están bien, corre el sistema normal
                saldos = df_pb.groupby('currency')['amount'].sum()
                cols = st.columns(len(saldos))
                for i, (moneda, total) in enumerate(saldos.items()):
                    cols[i].metric(label=f"Total {moneda}", value=f"${total:,.2f}")

                fig = px.pie(df_pb, values='amount', names='currency', title="Distribución por Moneda")
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Detalle de Cuentas")
                st.dataframe(df_pb[['name', 'amount', 'currency']], use_container_width=True)
            else:
                # Si fallan los nombres, mostramos qué encontró realmente el sistema
                st.warning("⚠️ Alerta de Datos: Los nombres de las columnas en tu JSON no coinciden con lo esperado.")
                st.write("**Columnas que se encontraron en tu archivo:**", columnas_disponibles)
                st.write("**Vista previa de los datos brutos:**")
                st.dataframe(df_pb.head())
        else:
            st.warning("No hay datos de cuentas disponibles en el JSON.")
