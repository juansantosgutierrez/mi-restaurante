import streamlit as st

# Configuración inicial
st.set_page_config(page_title="Restaurante Santos", layout="wide")
st.title("🍴 Gestión de Ventas - Restaurante Santos")

# Inicializamos el estado de la selección si no existe
if 'seleccion' not in st.session_state:
    st.session_state.seleccion = None

# --- MENÚ PRINCIPAL ---
st.subheader("Seleccione una Categoría")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🍳 DESAYUNO", use_container_width=True):
        st.session_state.seleccion = "Desayuno"

with col2:
    if st.button("🍲 ALMUERZO", use_container_width=True):
        st.session_state.seleccion = "Almuerzo"

with col3:
    if st.button("🌙 CENA", use_container_width=True):
        st.session_state.seleccion = "Cena"

# --- SECCIÓN DINÁMICA ---
st.divider()

if st.session_state.seleccion == "Desayuno":
    st.info("☕ Opciones de Desayuno")
    # Aquí irán los botones de Paila de huevo, Té, etc.
    if st.button("⬅️ Volver al menú principal"):
        st.session_state.seleccion = None

elif st.session_state.seleccion == "Almuerzo":
    st.info("🍲 Opciones de Almuerzo")
    # Aquí irán los botones de Menú Completo, Solo Segundo, etc.
    if st.button("⬅️ Volver al menú principal"):
        st.session_state.seleccion = None

elif st.session_state.seleccion == "Cena":
    st.info("🌙 Opciones de Cena")
    if st.button("⬅️ Volver al menú principal"):
        st.session_state.seleccion = None
