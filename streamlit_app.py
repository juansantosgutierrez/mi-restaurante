import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Restaurante Santos", layout="wide")
st.title("🍴 Sistema de Ventas - Restaurante Santos")

# Enlace a tu hoja
URL_DIRECTA = "https://docs.google.com/spreadsheets/d/1Y6y_hTRG-FJ6RdWfF6vETzxpyHBKvCLG9GgXa4eelbM/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para guardar ventas
def registrar_venta(producto, precio, categoria):
    try:
        nueva_fila = pd.DataFrame([{
            "ID_Venta": datetime.now().strftime("%Y%m%d%H%M%S"),
            "Fecha": datetime.now().strftime("%Y-%m-%d"),
            "Hora": datetime.now().strftime("%H:%M:%S"),
            "Categoria": categoria,
            "Producto": producto,
            "Monto": precio,
            "Tipo": "PAGADO"
        }])
        df_actual = conn.read(spreadsheet=URL_DIRECTA)
        df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(spreadsheet=URL_DIRECTA, data=df_final)
        st.success(f"✅ {producto} registrado (${precio})")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- SECCIÓN 1: COMIDA 🍲 ---
with st.expander("🍔 COMIDA", expanded=True):
    tab1, tab2, tab3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
    
    with tab1:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("🐢\n\nTortuga\nNormal\n\n$2.500", use_container_width=True):
                registrar_venta("Tortuga Normal", 2500, "Desayuno")
            
    with tab2:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("🍱\n\nMenú\nCompleto\n\n$3.500", use_container_width=True):
                registrar_venta("Menú", 3500, "Almuerzo")
            
    with tab3:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("🍽️\n\nCena\n\n$3.500", use_container_width=True):
                registrar_venta("Cena", 3500, "Cena")

# --- SECCIÓN 2: BEBESTIBLE 🥤 ---
with st.expander("🥤 BEBESTIBLE", expanded=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("🥤\n\nCoca Cola\n\n$2.000", use_container_width=True):
            registrar_venta("Coca Cola", 2000, "Bebestible")

# --- SECCIÓN 3: TIENDA 🏪 ---
with st.expander("🏪 TIENDA", expanded=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("🍰\n\nQueque\n\n$1.000", use_container_width=True):
            registrar_venta("Queque", 1000, "Tienda")

# --- VISUALIZACIÓN ---
st.divider()
st.subheader("📊 Últimos Registros")
try:
    data = conn.read(spreadsheet=URL_DIRECTA)
    st.dataframe(data.tail(5), use_container_width=True)
except:
    st.info("Sincronizando con Google Sheets...")
