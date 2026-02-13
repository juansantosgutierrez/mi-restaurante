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

# 🏢 Estructura de 2 Columnas
col_menu, col_lista = st.columns([3, 1])

with col_menu:
    st.title("🍴 Menú Restaurante Santos")
    
    with st.expander("🍔 COMIDA", expanded=True):
        st.markdown("<style>button[data-baseweb='tab'] {font-size: 20px !important;}</style>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
        
        with t1:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                # CAMBIO: Usamos "Producto", "Monto" y "Categoria" igual que en el Excel
                if st.button("🐢\n\nTortuga\nNormal\n\n$2.500", key="tortuga"):
                    st.session_state.pedido_temporal.append({"Producto": "Tortuga Normal", "Monto": 2500, "Categoria": "Desayuno"})
                    st.rerun()

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

# 📋 COLUMNA DERECHA
with col_lista:
    st.markdown("### 📝 Pedido Actual")
    
    if not st.session_state.pedido_temporal:
        st.write("Selecciona productos...")
    else:
        total = 0
        for i, item in enumerate(st.session_state.pedido_temporal):
            # Mostramos usando los nuevos nombres
            st.write(f"• {item['Producto']} - **${item['Monto']:,}**")
            total += item['Monto']
        
        st.divider()
        st.markdown(f"## TOTAL: ${total:,}")
        
        if st.button("✅ FINALIZAR VENTA", use_container_width=True, type="primary"):
            try:
                df_existente = conn.read(spreadsheet=URL_DIRECTA)
                df_nuevo = pd.DataFrame(st.session_state.pedido_temporal)
                
                ahora = datetime.now()
                df_nuevo["ID_Venta"] = ahora.strftime("%Y%m%d%H%M%S")
                df_nuevo["Fecha"] = ahora.strftime("%Y-%m-%d")
                df_nuevo["Hora"] = ahora.strftime("%H:%M:%S")
                df_nuevo["Tipo"] = "PAGADO"
                
                # REORDENAR: Aseguramos que el orden sea ID, Fecha, Hora, Categoria, Producto, Monto, Tipo
                df_nuevo = df_nuevo[["ID_Venta", "Fecha", "Hora", "Categoria", "Producto", "Monto", "Tipo"]]
                
                df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                conn.update(spreadsheet=URL_DIRECTA, data=df_final)
                
                st.success("¡Venta guardada!")
                st.session_state.pedido_temporal = []
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
