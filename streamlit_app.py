import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Restaurante Santos", layout="wide")

# CSS para agrandar las pestañas (Tabs) y estilos de botones
st.markdown("""
    <style>
    /* Tamaño de letra para Desayuno, Almuerzo, Cena */
    button[data-baseweb="tab"] div {
        font-size: 24px !important;
        font-weight: bold;
    }
    /* Estilo para botones seleccionados (verde suave) */
    .stButton > button[data-selected="true"] {
        background-color: #d4edda !important;
        border: 2px solid #28a745 !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Función para saber si un producto ya está seleccionado
def esta_en_carrito(nombre):
    return any(item['prod'] == nombre for item in st.session_state.carrito)

# --- PANEL LATERAL (RESUMEN) ---
with st.sidebar:
    st.header("📋 Resumen del Pedido")
    if not st.session_state.carrito:
        st.write("No hay productos seleccionados.")
    else:
        total = 0
        for i, item in enumerate(st.session_state.carrito):
            col_item, col_borrar = st.columns([4, 1])
            col_item.write(f"**{item['prod']}**\n${item['precio']:,}")
            if col_borrar.button("❌", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()
            total += item['precio']
        
        st.divider()
        st.subheader(f"TOTAL: ${total:,}")
        
        if st.button("✅ CONFIRMAR Y FINALIZAR", use_container_width=True, type="primary"):
            # Aquí va la lógica de guardado en GSheets que ya tenemos
            st.success("Venta procesada con éxito")
            st.session_state.carrito = []
            st.rerun()

# --- CUERPO PRINCIPAL ---
st.header("COMIDA")
with st.expander("Opciones", expanded=True):
    t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
    
    with t1:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            prod, precio = "Tortuga Normal", 2500
            seleccionado = esta_en_carrito(prod)
            # Usamos un truco de HTML/CSS para el color verde si está seleccionado
            if st.button(f"🐢\n{prod}\n${precio:,}", use_container_width=True, key="btn_tortuga"):
                if not seleccionado:
                    st.session_state.carrito.append({"prod": prod, "precio": precio, "cat": "Desayuno"})
                    st.rerun()

st.header("BEBESTIBLE")
# (Aquí iría la cuadrícula de bebidas con la misma lógica)

st.header("TIENDA")
# (Aquí iría la cuadrícula de tienda)
