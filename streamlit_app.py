import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 🎨 Configuración Estilo Chile
st.set_page_config(page_title="Control Restaurante Santos", layout="wide")
st.title("🍴 Sistema de Ventas (Pesos Chilenos)")

# 🔗 ENLACE DIRECTO
URL_DIRECTA = "https://docs.google.com/spreadsheets/d/1Y6y_hTRG-FJ6RdWfF6vETzxpyHBKvCLG9GgXa4eelbM/edit#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 💰 REGISTRO DE VENTAS ---
st.subheader("Registrar Ingresos")
col1, col2 = st.columns(2)

with col1:
    # Ajusté el precio a un promedio de almuerzo en Chile (ej: $5.000)
    if st.button("🍲 ALMUERZO ($5.000)", use_container_width=True):
        try:
            nueva_fila = pd.DataFrame([{
                "ID_Venta": datetime.now().strftime("%Y%m%d%H%M%S"),
                "Fecha": datetime.now().strftime("%Y-%m-%d"),
                "Hora": datetime.now().strftime("%H:%M:%S"),
                "Categoria": "Almuerzo",
                "Producto": "Menú Completo",
                "Monto": 5000,
                "Tipo": "PAGADO"
            }])
            
            # Leemos y agregamos la fila
            df_actual = conn.read(spreadsheet=URL_DIRECTA)
            df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
            
            # Intentamos actualizar
            conn.update(spreadsheet=URL_DIRECTA, data=df_final)
            st.success("✅ Venta guardada correctamente")
        except Exception as e:
            st.error(f"Error de permisos: Necesitas conectar Google Cloud para escribir. {e}")

with col2:
    if st.button("🥤 BEBIDA ($1.500)", use_container_width=True):
        st.info("Botón de bebida configurado")

# --- 📊 VISUALIZACIÓN ---
st.divider()
st.subheader("Últimos Registros")
try:
    data = conn.read(spreadsheet=URL_DIRECTA)
    st.dataframe(data.tail(10), use_container_width=True)
except:
    st.write("Esperando datos...")
