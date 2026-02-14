import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 🎨 Configuración de pantalla
st.set_page_config(page_title="Restaurante Santos", layout="wide")

# Conexión a Google Sheets
URL_DIRECTA = "https://docs.google.com/spreadsheets/d/1Y6y_hTRG-FJ6RdWfF6vETzxpyHBKvCLG9GgXa4eelbM/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# 🧠 Memoria de la App
if 'pedido_temporal' not in st.session_state:
    st.session_state.pedido_temporal = []

# --- 🛠️ VENTANA FLOTANTE DE GASTOS ---
@st.dialog("Registrar Gasto")
def modal_gastos():
    st.write("Anota los detalles del gasto aquí abajo:")
    monto_gasto = st.number_input("Monto Gastado ($)", min_value=0, step=100)
    desc_gasto = st.text_input("Descripción (Ej: Saco para agua)")
    
    if st.button("Guardar Gasto", type="primary"):
        if monto_gasto > 0 and desc_gasto:
            try:
                # Crear datos del gasto
                df_gasto = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Monto": monto_gasto,
                    "Descripcion": desc_gasto
                }])
                
                # Leer hoja de Gastos y actualizar
                df_actual_gastos = conn.read(spreadsheet=URL_DIRECTA, worksheet="Gastos")
                df_final_gastos = pd.concat([df_actual_gastos, df_gasto], ignore_index=True)
                conn.update(spreadsheet=URL_DIRECTA, worksheet="Gastos", data=df_final_gastos)
                
                st.success(f"Gasto de ${monto_gasto} guardado correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: Asegúrate de que la pestaña se llame 'Gastos'. {e}")
        else:
            st.warning("Por favor completa el monto y la descripción.")

# --- 🔝 BARRA SUPERIOR (Botones de Control) ---
col_titulo, col_btn1, col_btn2 = st.columns([2, 1, 1])

with col_titulo:
    st.title("🍴 Menú Restaurante Santos")

with col_btn1:
    if st.button("💸 GASTOS", use_container_width=True):
        modal_gastos()

with col_btn2:
    if st.button("➕ AGREGAR MENU HOY", use_container_width=True):
        st.info("Próximamente: Aquí configuraremos el menú dinámico.")

# --- 🏢 ESTRUCTURA DE VENTAS (Lo que ya teníamos) ---
col_menu, col_lista = st.columns([3, 1])

with col_menu:
    with st.expander("🍔 COMIDA", expanded=True):
        st.markdown("<style>button[data-baseweb='tab'] {font-size: 20px !important;}</style>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
        
        with t1:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                if st.button("🐢\n\nTortuga\nNormal\n\n$2.500", key="tortuga"):
                    st.session_state.pedido_temporal.append({"Producto": "Tortuga Normal", "Monto": 2500, "Categoria": "Desayuno"})
                    st.rerun()
        # ... (Resto de los botones de Almuerzo, Cena, Bebestible y Tienda iguales que antes)
        with t2:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                if st.button("🍱\n\nMenú\n\n$3.500", key="menu"):
                    st.session_state.pedido_temporal.append({"Producto": "Menú", "Monto": 3500, "Categoria": "Almuerzo"})
                    st.rerun()
            with c2:
                if st.button("🍛\n\nSegundo\nSolo\n\n$2.500", key="segundo"):
                    st.session_state.pedido_temporal.append({"Producto": "Segundo Solo", "Monto": 2500, "Categoria": "Almuerzo"})
                    st.rerun()
            with c3:
                if st.button("🥣\n\nSopa\nSola\n\n$1.500", key="sopa"):
                    st.session_state.pedido_temporal.append({"Producto": "Sopa Sola", "Monto": 1500, "Categoria": "Almuerzo"})
                    st.rerun()
        with t3:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                if st.button("🍽️\n\nCena\n\n$3.500", key="cena"):
                    st.session_state.pedido_temporal.append({"Producto": "Cena", "Monto": 3500, "Categoria": "Cena"})
                    st.rerun()

    with st.expander("🥤 BEBESTIBLE", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("🥤\n\nCoca Cola\n\n$2.000", key="coca"):
                st.session_state.pedido_temporal.append({"Producto": "Coca Cola", "Monto": 2000, "Categoria": "Bebestible"})
                st.rerun()

    with st.expander("🏪 TIENDA", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("🍰\n\nQueque\n\n$1.000", key="queque"):
                st.session_state.pedido_temporal.append({"Producto": "Queque", "Monto": 1000, "Categoria": "Tienda"})
                st.rerun()

# 📋 COLUMNA DERECHA (LISTA)
with col_lista:
    st.markdown("### 📝 Pedido Actual")
    if not st.session_state.pedido_temporal:
        st.write("Selecciona productos...")
    else:
        total = 0
        for i, item in enumerate(st.session_state.pedido_temporal):
            st.write(f"• {item['Producto']} - **${item['Monto']:,}**")
            total += item['Monto']
        st.divider()
        st.markdown(f"## TOTAL: ${total:,}")
        if st.button("✅ FINALIZAR VENTA", use_container_width=True, type="primary"):
            try:
                df_existente = conn.read(spreadsheet=URL_DIRECTA, worksheet="Hoja 1")
                df_nuevo = pd.DataFrame(st.session_state.pedido_temporal)
                ahora = datetime.now()
                df_nuevo["ID_Venta"] = ahora.strftime("%Y%m%d%H%M%S")
                df_nuevo["Fecha"] = ahora.strftime("%Y-%m-%d")
                df_nuevo["Hora"] = ahora.strftime("%H:%M:%S")
                df_nuevo["Tipo"] = "PAGADO"
                df_nuevo = df_nuevo[["ID_Venta", "Fecha", "Hora", "Categoria", "Producto", "Monto", "Tipo"]]
                df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                conn.update(spreadsheet=URL_DIRECTA, worksheet="Hoja 1", data=df_final)
                st.success("¡Venta guardada!")
                st.session_state.pedido_temporal = []
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar venta: {e}")
