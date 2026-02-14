import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 🎨 Configuración
st.set_page_config(page_title="Restaurante Santos", layout="wide")

# CSS para Pedido Flotante
st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div:nth-child(2) [data-testid="stVerticalBlock"] {
        position: sticky;
        top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

URL_DIRECTA = "https://docs.google.com/spreadsheets/d/1Y6y_hTRG-FJ6RdWfF6vETzxpyHBKvCLG9GgXa4eelbM/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- MEMORIA (Optimización de velocidad) ---
if 'pedido_temporal' not in st.session_state:
    st.session_state.pedido_temporal = []
if 'modo_editor' not in st.session_state:
    st.session_state.modo_editor = False
if 'menu_cache' not in st.session_state:
    st.session_state.menu_cache = None

# --- FUNCIONES ---
def leer_menu():
    # Solo lee de Sheets si la memoria está vacía para ganar velocidad
    if st.session_state.menu_cache is None:
        try:
            st.session_state.menu_cache = conn.read(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", ttl=0).dropna(how="all")
        except:
            st.session_state.menu_cache = pd.DataFrame(columns=["Categoria", "Producto", "Monto"])
    return st.session_state.menu_cache

def reset_cache():
    st.session_state.menu_cache = None

# --- MODALES ---
@st.dialog("➕ Nuevo Producto")
def modal_nuevo(cat):
    n = st.text_input(f"Nombre del {cat}")
    p = st.number_input("Precio ($)", min_value=0, step=100)
    if st.button("Guardar"):
        if n and p > 0:
            df_act = leer_menu()
            df_n = pd.DataFrame([{"Categoria": cat, "Producto": n, "Monto": int(p)}])
            conn.update(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", data=pd.concat([df_act, df_n], ignore_index=True))
            reset_cache()
            st.rerun()

@st.dialog("📲 Recarga")
def modal_recarga():
    op = st.selectbox("Operador", ["WOM", "ENTEL", "MOVISTAR", "CLARO"])
    m = st.number_input("Monto ($)", min_value=0, step=500)
    if st.button("Agregar"):
        if m > 0:
            st.session_state.pedido_temporal.append({"Categoria": "Recarga", "Producto": f"Recarga {op}", "Monto": int(m)})
            st.rerun()

@st.dialog("📦 Venta Especial")
def modal_otros():
    desc = st.text_input("¿Qué se vendió?")
    m = st.number_input("Monto ($)", min_value=0, step=100)
    if st.button("Agregar"):
        if desc and m > 0:
            st.session_state.pedido_temporal.append({"Categoria": "Otros", "Producto": desc, "Monto": int(m)})
            st.rerun()

@st.dialog("💸 Gasto")
def modal_gastos():
    m = st.number_input("Monto ($)", min_value=0, step=500)
    d = st.text_input("Descripción")
    o = st.selectbox("Saco De:", ["Comida", "Bebestible", "Tienda", "Recarga", "Chela", "Otros", "Caja General"])
    if st.button("Guardar Gasto"):
        df_g = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "Monto": int(m), "Descripcion": d, "Saco De": o}])
        df_act = conn.read(spreadsheet=URL_DIRECTA, worksheet="Gastos", ttl=0).dropna(how="all")
        conn.update(spreadsheet=URL_DIRECTA, worksheet="Gastos", data=pd.concat([df_act, df_g], ignore_index=True))
        st.rerun()

# --- INTERFAZ ---
df_menu = leer_menu()
c1, c2, c3 = st.columns([2, 1, 1])
c1.title("🍴 Restaurante Santos")
if c2.button("💸 GASTOS", use_container_width=True): modal_gastos()
txt_btn = "🔄 CERRAR EDITOR" if st.session_state.modo_editor else "➕ AGREGAR MENU HOY"
if c3.button(txt_btn, use_container_width=True):
    st.session_state.modo_editor = not st.session_state.modo_editor
    st.rerun()

col_m, col_p = st.columns([3, 1.2]) # Un poco más ancho para los botones de borrar

with col_m:
    def mostrar_seccion(titulo, cat, especial=None):
        st.header(titulo)
        grid = st.columns(5)
        if especial == "Recarga":
            with grid[0]:
                if st.button("📲\n\nRECARGAR", use_container_width=True): modal_recarga()
        elif especial == "Otros":
            with grid[0]:
                if st.button("📦\n\nVENTA ESPECIAL", use_container_width=True): modal_otros()
        else:
            items = df_menu[df_menu["Categoria"] == cat]
            for i, (idx, row) in enumerate(items.iterrows()):
                with grid[i % 5]:
                    if st.session_state.modo_editor:
                        if st.button("❌", key=f"del_menu_{idx}"):
                            conn.update(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", data=df_menu.drop(idx))
                            reset_cache()
                            st.rerun()
                    p_f = f"${int(row['Monto']):,}".replace(",", ".")
                    if st.button(f"{row['Producto']}\n\n{p_f}", key=f"btn_{idx}", use_container_width=True):
                        st.session_state.pedido_temporal.append(row.to_dict())
                        st.rerun()
            if st.session_state.modo_editor:
                with grid[len(items) % 5]:
                    if st.button(f"➕\n\nNuevo\n{titulo}", key=f"add_{cat}", use_container_width=True):
                        modal_nuevo(cat)

    with st.expander("🍔 COMIDA", expanded=True):
        t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
        with t1: mostrar_seccion("Desayuno", "Desayuno")
        with t2: mostrar_seccion("Almuerzo", "Almuerzo")
        with t3: mostrar_seccion("Cena", "Cena")
    
    mostrar_seccion("🥤 BEBESTIBLE", "Bebestible")
    mostrar_seccion("🏪 TIENDA", "Tienda")
    mostrar_seccion("📲 RECARGA", "Recarga", especial="Recarga")
    mostrar_seccion("🍺 CHELA", "Chela")
    mostrar_seccion("📦 OTROS", "Otros", especial="Otros")

with col_p:
    st.subheader("📝 Pedido Actual")
    total = 0
    # Listar pedido con opción de borrar
    for i, item in enumerate(st.session_state.pedido_temporal):
        total += int(item["Monto"])
        p_i = f"${int(item['Monto']):,}".replace(",", ".")
        col_txt, col_btn = st.columns([4, 1])
        col_txt.write(f"• {item['Producto']} ({p_f})")
        if col_btn.button("🗑️", key=f"del_item_{i}"):
            st.session_state.pedido_temporal.pop(i)
            st.rerun()
            
    st.divider()
    st.markdown(f"## TOTAL: ${total:,}".replace(",", "."))
    if st.button("✅ FINALIZAR VENTA", type="primary", use_container_width=True):
        if st.session_state.pedido_temporal:
            df_v = pd.DataFrame(st.session_state.pedido_temporal)
            ahora = datetime.now()
            df_v["ID_Venta"] = ahora.strftime("%Y%m%d%H%M%S")
            df_v["Fecha"] = ahora.strftime("%Y-%m-%d")
            df_v["Hora"] = ahora.strftime("%H:%M:%S")
            df_v["Tipo"] = "PAGADO"
            df_v = df_v[["ID_Venta", "Fecha", "Hora", "Categoria", "Producto", "Monto", "Tipo"]]
            df_h = conn.read(spreadsheet=URL_DIRECTA, worksheet="Hoja 1", ttl=0).dropna(how="all")
            conn.update(spreadsheet=URL_DIRECTA, worksheet="Hoja 1", data=pd.concat([df_h, df_v], ignore_index=True))
            st.session_state.pedido_temporal = []
            st.rerun()
