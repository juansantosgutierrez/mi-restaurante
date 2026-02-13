import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 🎨 Configuración de la interfaz
st.set_page_config(page_title="Control de Restaurante", layout="wide")
st.title("🍴 Sistema de Registro de Ventas")

# 🔗 ENLACE DIRECTO (El que copiaste de la pestaña)
URL_DIRECTA = "https://docs.google.com/spreadsheets/d/1Y6y_hTRG-FJ6RdWfF6vETzxpyHBKvCLG9GgXa4eelbM/edit?gid=0#gid=0"

# Establecemos la conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 💰 SECCIÓN DE REGISTRO ---
st.subheader("Registrar Ingresos")
col1, col2, col3 = st.columns(3)

with col1:
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
            
            # Leemos y actualizamos usando la URL directa
            df_existente = conn.read(spreadsheet=URL_DIRECTA, worksheet="Hoja 1")
            df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
            conn.update(spreadsheet=URL_DIRECTA, worksheet="Hoja 1", data=df_final)
            st.success("✅ ¡Venta guardada en Google Sheets!")
        except Exception as e:
            st.error(f"Error al intentar guardar: {e}")

with col2:
    st.button("🥤 BEBIDA", use_container_width=True)

with col3:
    st.button("💸 GASTO", use_container_width=True)

# --- 📊 VISUALIZACIÓN DE DATOS ---
st.divider()
st.subheader("Últimos Registros en Hoja 1")
try:
    # Intentamos mostrar la tabla
    data = conn.read(spreadsheet=URL_DIRECTA, worksheet="Hoja 1")
    st.dataframe(data.tail(10), use_container_width=True)
except Exception as e:
    st.info("Aún no hay datos para mostrar o la conexión está cargando...")
    st.warning(f"Detalle técnico: {e}")
