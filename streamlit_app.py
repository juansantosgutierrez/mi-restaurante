import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Control de Restaurante", layout="wide")

st.title("🍴 Sistema de Registro de Ventas")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- BOTONES DE VENTAS ---
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
            "Monto": 15.00,
            "Tipo": "PAGADO"
        }])
        # Leemos los datos de la "Hoja 1"
        df_existente = conn.read(worksheet="Hoja 1")
        df_final = pd.concat([df_existente, nueva_venta], ignore_index=True)
        # Guardamos en la "Hoja 1"
        conn.update(worksheet="Hoja 1", data=df_final)
        st.success("✅ Almuerzo registrado")

with col2:
    st.button("🥤 BEBIDA", use_container_width=True)

with col3:
    st.button("💸 GASTO", use_container_width=True)

# --- TABLA DE VENTAS ---
st.divider()
st.subheader("Últimos Registros")
data = conn.read(worksheet="Hoja 1")
st.dataframe(data.tail(10), use_container_width=True)
