import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Financiero - Adrián", page_icon="💰")

# --- 2. FUNCIÓN DE LOGGEO ---
def check_password():
    """Retorna True si el usuario ingresó las credenciales correctas."""

    def password_entered():
        """Verifica si las credenciales coinciden con lo solicitado."""
        if (
            st.session_state["username"] == "ttoty13"
            and st.session_state["password"] == "922292"
        ):
            st.session_state["password_correct"] = True
            # Borramos las credenciales de la memoria por seguridad
            del st.session_state["password"]  
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Pantalla inicial de loggeo
        st.title("🔐 Acceso al Sistema")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        return False
    
    elif not st.session_state["password_correct"]:
        # Si falló la clave, mostramos el error y los campos de nuevo
        st.title("🔐 Acceso al Sistema")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        st.error("❌ Usuario o contraseña incorrectos.")
        return False
    
    else:
        # Acceso concedido
        return True

# --- 3. LÓGICA DEL SISTEMA (Solo corre si el loggeo es exitoso) ---
if check_password():
    
    # Botón para cerrar sesión (opcional)
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- CARGA DE DATOS ---
    # Asegurate de que el nombre del JSON sea el correcto en tu GitHub
    JSON_FILE = 'backup-finanzas-17741715347314445276-2026-01-02.json'

    if not os.path.exists(JSON_FILE):
        st.error(f"No se encontró el archivo {JSON_FILE}")
    else:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f).get('data', {})

        # --- INTERFAZ DEL DASHBOARD ---
        st.title("💰 Mi Panel Financiero")
        
        piggy_banks = data.get('piggyBanks', [])
        if piggy_banks:
            df_pb = pd.DataFrame(piggy_banks)
            
            # Métricas principales
            saldos = df_pb.groupby('currency')['amount'].sum()
            cols = st.columns(len(saldos))
            for i, (moneda, total) in enumerate(saldos.items()):
                cols[i].metric(label=f"Total {moneda}", value=f"${total:,.2f}")

            # Gráfico de Distribución
            fig = px.pie(df_pb, values='amount', names='currency', title="Distribución por Moneda")
            st.plotly_chart(fig, use_container_width=True)

            # Detalle de cuentas
            st.subheader("Detalle de Cuentas")
            st.dataframe(df_pb[['name', 'amount', 'currency']], use_container_width=True)
        else:
            st.warning("No hay datos de cuentas disponibles en el JSON.")

