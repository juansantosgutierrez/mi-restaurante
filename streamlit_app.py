import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Restaurante Santos", layout="wide")

# Estilo personalizado para que los botones se vean más grandes y el botón de confirmar resalte
st.markdown("""
    <style>
    div.stButton > button {
        height: 100px;
        font-size: 20px !important;
    }
    .confirm-btn button {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🍴 Sistema de Ventas - Restaurante Santos")

# Inicializar el "carrito" de la sesión si no existe
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- Categorías con letras grandes ---
st.markdown("## 🍲 COMIDA")
with st.expander("Abrir opciones de comida", expanded=True):
    t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
    with t1:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("🐢\nTortuga\n$2.500", use_container_width=True):
                st.session_state.carrito.append({"prod": "Tortuga Normal", "precio": 2500, "cat": "Desayuno"})

st.markdown("## 🥤 BEBESTIBLE")
with st.container():
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("🥤\nCoca Cola\n$2.000", use_container_width=True):
            st.session_state.carrito.append({"prod": "Coca Cola", "precio": 2000, "cat": "Bebestible"})

st.markdown("## 🏪 TIENDA")
with st.container():
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("🍰\nQueque\n$1.000", use_container_width=True):
            st.session_state.carrito.append({"prod": "Queque", "precio": 1000, "cat": "Tienda"})

# --- SECCIÓN DE CONFIRMACIÓN (Derecha/Abajo) ---
st.divider()
if st.session_state.carrito:
    st.subheader("🛒 Pedido actual:")
    for item in st.session_state.carrito:
        st.write(f"- {item['prod']} (${item['precio']})")
    
    col_vacia, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("✅ CONFIRMAR Y FINALIZAR", use_container_width=True):
            # Aquí iría la lógica para guardar TODO el carrito en el Excel
            st.success("¡Venta procesada!")
            st.session_state.carrito = [] # Limpiar carrito
