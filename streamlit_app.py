import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 🎨 Configuración visual
st.set_page_config(page_title="Control de Restaurante", layout="wide")
st.title("🍴 Sistema de Registro de Ventas")

# 🔌 Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 💰 BOTONES DE REGISTRO ---
st.subheader("Registrar Ingresos")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🍲 ALMUERZO (S/. 15.00)", use_container_width=True):
        # Creamos la fila con los datos
        nueva_fila = pd.DataFrame([{
            "ID_Venta": datetime.now().strftime("%Y%m%d%H%M%S"),
            "Fecha": datetime.now().strftime("%Y-%m-%d"),
            "Hora": datetime.now().strftime("%H:%M:%S"),
            "Categoria": "Almuerzo",
            "Producto": "Menu Completo",
            "Monto": 15.00,
            "Tipo": "PAGADO"
        }])
        
        # Leemos los datos actuales de la Hoja 1
        df_existente = conn.read(worksheet="Hoja 1")
        # Unimos lo nuevo con lo viejo
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        # 💾 Guardamos los cambios de vuelta en Google Sheets
        conn.update(worksheet="Hoja 1", data=df_final)
        st.success("✅ ¡Venta de Almuerzo guardada con éxito!")

with col2:
    st.button("🥤 BEBIDA", use_container_width=True)

with col3:
    st.button("💸 GASTO", use_container_width=True)

# --- 📊 VISUALIZACIÓN ---
st.divider()
st.subheader("Últimas 10 Ventas")
df_mostrar = conn.read(worksheet="Hoja 1")
st.dataframe(df_mostrar.tail(10), use_container_width=True)
