import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Adrián", page_icon="💰", layout="wide")

# --- 2. CONTROL DE ACCESO ---
def check_password():
    def password_entered():
        if st.session_state["username"] == "ttoty13" and st.session_state["password"] == "922292":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        return False
    return st.session_state["password_correct"]

# --- 3. PROCESAMIENTO DE DATOS ---
if check_password():
    st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.update({"password_correct": False}))
    
    # Nombre de tu archivo backup
    JSON_FILE = 'backup-finanzas-17741715347314445276-2026-01-02.json'

    if not os.path.exists(JSON_FILE):
        st.error(f"❌ Error de entrada: No se encuentra el archivo {JSON_FILE} en el repositorio.")
    else:
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Navegación segura en el árbol JSON
            data_content = raw_data.get('data', {})
            if data_content is None: data_content = {}
            
            pb_list = data_content.get('piggyBanks', [])
            
            if pb_list:
                df = pd.DataFrame(pb_list)
                # Normalizamos nombres de columnas a minúsculas
                df.columns = [str(c).lower() for c in df.columns]
                
                # Verificamos columnas críticas
                if 'currency' in df.columns and 'amount' in df.columns:
                    # Aseguramos que 'amount' sea numérico (Float)
                    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
                    
                    # Generamos el diccionario de saldos de forma segura
                    resumen_saldos = df.groupby('currency')['amount'].sum().to_dict()
                    
                    st.title("💰 Mi Panel Financiero")
                    
                    # Verificamos que el diccionario tenga datos antes de iterar
                    if resumen_saldos:
                        cols = st.columns(len(resumen_saldos))
                        for i, (moneda, total) in enumerate(resumen_saldos.items()):
                            cols[i].metric(label=f"Total {moneda}", value=f"${total:,.2f}")
                        
                        # Visualización
                        fig = px.pie(df, values='amount', names='currency', title="Distribución de Activos")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        with st.expander("🔍 Auditoría de Datos"):
                            st.dataframe(df)
                    else:
                        st.warning("Los datos están presentes pero no hay montos numéricos válidos.")
                else:
                    st.error(f"Columnas no encontradas. El sistema detectó: {list(df.columns)}")
            else:
                st.info("El archivo JSON está vacío o no contiene la clave 'piggyBanks'.")
                
        except Exception as e:
            st.error(f"Falla en el procesamiento de datos: {str(e)}")
