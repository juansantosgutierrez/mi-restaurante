import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de la página para modo PC
st.set_page_config(page_title="Control de Restaurante", layout="wide")

st.title("🍴 Sistema de Registro de Ventas")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- BOTONES GRANDES DE VENTAS ---
st.subheader("Registrar Ingresos")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🍲 ALMUERZO", use_container_width=True):
        nueva_venta = pd.DataFrame([{
            "ID_Venta": datetime.now().strftime("%Y%m%d%H%M%S"),
            "Fecha": datetime.now().strftime("%Y-%m-%d"),
            "Hora": datetime.now().strftime("%H:%M:%S"),
            "Categoria": "Almuerzo",
            "Producto": "Plato Único",
            "Monto": 15.00,  # Puedes cambiar el precio aquí
            "Tipo": "PAGADO"
        }])
        df_existente = conn.read()
        df_final = pd.concat([df_existente, nueva_venta], ignore_index=True)
        conn.update(data=df_final)
        st.success("✅ Almuerzo registrado")

with col2:
    if st.button("🥤 BEBIDA", use_container_width=True):
        # Aquí puedes agregar lógica similar para bebidas
        st.info("Configura aquí el registro de bebidas")

with col3:
    if st.button("💸 GASTO", use_container_width=True):
        st.warning("Formulario de gasto")

# --- VISUALIZACIÓN ---
st.divider()
st.subheader("Ventas del Día")
data = conn.read()
st.dataframe(data.tail(10), use_container_width=True)
