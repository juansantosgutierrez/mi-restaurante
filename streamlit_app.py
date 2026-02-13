import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 🎨 Configuración de pantalla
st.set_page_config(page_title="Restaurante Santos", layout="wide")

# Conexión a Google Sheets
URL_DIRECTA = "https://docs.google.com/spreadsheets/d/1Y6y_hTRG-FJ6RdWfF6vETzxpyHBKvCLG9GgXa4eelbM/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# 🧠 Memoria de la App: Inicializar la lista si está vacía
if 'pedido_temporal' not in st.session_state:
    st.session_state.pedido_temporal = []

# 🏢 Estructura de 2 Columnas: [Menú (3 partes), Lista (1 parte)]
col_menu, col_lista = st.columns([3, 1])

with col_menu:
    st.title("🍴 Menú Restaurante Santos")
    
    # --- SECCIÓN 1: COMIDA ---
    with st.expander("🍔 COMIDA", expanded=True):
        # Estilo para que Desayuno, Almuerzo y Cena se vean grandes
        st.markdown("<style>button[data-baseweb='tab'] {font-size: 20px !important;}</style>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
        
        with t1:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                if st.button("🐢\n\nTortuga\nNormal\n\n$2.500", key="tortuga_btn"):
                    st.session_state.pedido_temporal.append({"prod": "Tortuga Normal", "precio": 2500, "cat": "Desayuno"})
                    st.rerun()

    # --- SECCIÓN 2: BEBESTIBLE ---
    with st.expander("🥤 BEBESTIBLE", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("🥤\n\nCoca Cola\n\n$2.000", key="coca_btn"):
                st.session_state.pedido_temporal.append({"prod": "Coca Cola", "precio": 2000, "cat": "Bebestible"})
                st.rerun()

    # --- SECCIÓN 3: TIENDA ---
    with st.expander("🏪 TIENDA", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("🍰\n\nQueque\n\n$1.000", key="queque_btn"):
                st.session_state.pedido_temporal.append({"prod": "Queque", "precio": 1000, "cat": "Tienda"})

# 📋 COLUMNA DERECHA: LA LISTA DE PEDIDOS
with col_lista:
    st.markdown("### 📝 Pedido Actual")
    
    if not st.session_state.pedido_temporal:
        st.write("Selecciona productos...")
    else:
        total = 0
        for i, item in enumerate(st.session_state.pedido_temporal):
            st.write(f"{item['prod']} - **${item['precio']:,}**")
            total += item['precio']
        
        st.divider()
        st.markdown(f"## TOTAL: ${total:,}")
        
        if st.button("✅ FINALIZAR VENTA", use_container_width=True, type="primary"):
            # Aquí pondremos la lógica para guardar toda la lista en GSheets
            st.success("¡Guardado!")
            st.session_state.pedido_temporal = []
            st.rerun()
