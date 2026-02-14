import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Restaurante Santos", layout="wide")
URL_DIRECTA = "https://docs.google.com/spreadsheets/d/1Y6y_hTRG-FJ6RdWfF6vETzxpyHBKvCLG9GgXa4eelbM/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- MEMORIA TEMPORAL ---
if 'pedido_temporal' not in st.session_state:
    st.session_state.pedido_temporal = []
if 'modo_editor' not in st.session_state:
    st.session_state.modo_editor = False

# --- FUNCIONES DE BASE DE DATOS ---
def leer_menu():
    try:
        return conn.read(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia").dropna(how="all")
    except:
        return pd.DataFrame(columns=["Categoria", "Producto", "Monto"])

def guardar_item_menu(cat, prod, precio):
    df_actual = leer_menu()
    nuevo = pd.DataFrame([{"Categoria": cat, "Producto": prod, "Monto": precio}])
    df_final = pd.concat([df_actual, nuevo], ignore_index=True)
    conn.update(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", data=df_final)

def borrar_item_menu(index_borrar):
    df_actual = leer_menu()
    df_final = df_actual.drop(index_borrar)
    conn.update(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", data=df_final)

# --- VENTANAS FLOTANTES ---
@st.dialog("➕ Agregar al Menú")
def modal_nuevo_item(categoria):
    nombre = st.text_input(f"Nombre del {categoria}")
    precio = st.number_input("Precio ($)", min_value=0, step=100)
    if st.button("Guardar"):
        if nombre and precio > 0:
            guardar_item_menu(categoria, nombre, precio)
            st.rerun()

@st.dialog("💸 Gastos")
def modal_gastos():
    monto = st.number_input("Monto ($)", min_value=0)
    desc = st.text_input("Descripción")
    if st.button("Guardar Gasto"):
        df_g = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "Monto": monto, "Descripcion": desc}])
        df_act = conn.read(spreadsheet=URL_DIRECTA, worksheet="Gastos").dropna(how="all")
        conn.update(spreadsheet=URL_DIRECTA, worksheet="Gastos", data=pd.concat([df_act, df_g], ignore_index=True))
        st.rerun()

# --- INTERFAZ ---
c_tit, c_g, c_e = st.columns([2, 1, 1])
c_tit.title("🍴 Restaurante Santos")
if c_g.button("💸 GASTOS", use_container_width=True): modal_gastos()
txt_ed = "🔄 CERRAR EDITOR" if st.session_state.modo_editor else "➕ AGREGAR MENU HOY"
if c_e.button(txt_ed, use_container_width=True):
    st.session_state.modo_editor = not st.session_state.modo_editor
    st.rerun()

df_menu = leer_menu()
col_menu, col_pedido = st.columns([3, 1])

with col_menu:
    def mostrar_seccion(categoria):
        items = df_menu[df_menu["Categoria"] == categoria]
        cols = st.columns(5)
        
        # Productos existentes
        for i, (idx, row) in enumerate(items.iterrows()):
            with cols[i % 5]:
                # Si el editor está activo, ponemos la X arriba
                if st.session_state.modo_editor:
                    if st.button(f"❌", key=f"del_{idx}"):
                        borrar_item_menu(idx)
                        st.rerun()
                
                if st.button(f"{row['Producto']}\n\n${row['Monto']:,}", key=f"btn_{idx}", use_container_width=True):
                    st.session_state.pedido_temporal.append({"Categoria": row['Categoria'], "Producto": row['Producto'], "Monto": row['Monto']})
                    st.rerun()
        
        # Botón "+" si el editor está activo
        if st.session_state.modo_editor:
            with cols[len(items) % 5]:
                if st.button(f"➕\n\nNuevo\n{categoria}", key=f"plus_{categoria}", use_container_width=True):
                    modal_nuevo_item(categoria)

    with st.expander("🍔 COMIDA", expanded=True):
        t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
        with t1: mostrar_seccion("Desayuno")
        with t2: mostrar_seccion("Almuerzo")
        with t3: mostrar_seccion("Cena")
    
    st.markdown("### 🥤 BEBESTIBLE")
    mostrar_seccion("Bebestible")
    st.markdown("### 🏪 TIENDA")
    mostrar_seccion("Tienda")

with col_pedido:
    st.subheader("📝 Pedido")
    total = sum(i["Monto"] for i in st.session_state.pedido_temporal)
    for i, item in enumerate(st.session_state.pedido_temporal):
        st.write(f"• {item['Producto']} (${item['Monto']:,})")
    st.divider()
    st.markdown(f"## TOTAL: ${total:,}")
    if st.button("✅ FINALIZAR VENTA", type="primary", use_container_width=True):
        if st.session_state.pedido_temporal:
            df_v = pd.DataFrame(st.session_state.pedido_temporal)
            ahora = datetime.now()
            df_v["ID_Venta"] = ahora.strftime("%Y%m%d%H%M%S")
            df_v["Fecha"] = ahora.strftime("%Y-%m-%d")
            df_v["Hora"] = ahora.strftime("%H:%M:%S")
            df_v["Tipo"] = "PAGADO"
            df_v = df_v[["ID_Venta", "Fecha", "Hora", "Categoria", "Producto", "Monto", "Tipo"]]
            df_hist = conn.read(spreadsheet=URL_DIRECTA, worksheet="Hoja 1").dropna(how="all")
            conn.update(spreadsheet=URL_DIRECTA, worksheet="Hoja 1", data=pd.concat([df_hist, df_v], ignore_index=True))
            st.session_state.pedido_temporal = []; st.rerun()
