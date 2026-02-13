import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 🎨 Configuración
st.set_page_config(page_title="Control de Restaurante", layout="wide")
st.title("🍴 Sistema de Registro de Ventas")

# 🔗 ENLACE DIRECTO
URL_DIRECTA = "https://docs.google.com/spreadsheets/d/1Y6y_hTRG-FJ6RdWfF6vETzxpyHBKvCLG9GgXa4eelbM/edit#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 💰 REGISTRO ---
st.subheader("Registrar Ingresos")
if st.button("🍲 ALMUERZO (S/. 15.00)", use_container_width=True):
    try:
        nueva_fila = pd.DataFrame([{
            "ID_Venta": datetime.now().strftime("%Y%m%d%H%M%S"),
            "Fecha": datetime.now().strftime("%Y-%m-%d"),
            "Hora": datetime.now().strftime("%H:%M:%S"),
            "Categoria": "Almuerzo",
            "Producto": "Menu Completo",
            "Monto": 15.00,
            "Tipo": "PAGADO"
        }])
        
        # Leemos los datos (usando solo el link para evitar errores de nombre)
        df_existente = conn.read(spreadsheet=URL_DIRECTA)
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        
        # Guardamos los datos
        conn.update(spreadsheet=URL_DIRECTA, data=df_final)
        st.success("✅ ¡Venta guardada!")
    except Exception as e:
        st.error(f"Error al intentar guardar: {e}")

# --- 📊 VISUALIZACIÓN ---
st.divider()
st.subheader("Últimos Registros")
try:
    # Intentamos leer la hoja completa
    data = conn.read(spreadsheet=URL_DIRECTA)
    st.dataframe(data.tail(10), use_container_width=True)
except Exception as e:
    st.warning(f"Detalle técnico: {e}")
