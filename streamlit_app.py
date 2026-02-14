import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Restaurante Santos", layout="wide")
URL_DIRECTA = "https://docs.google.com/spreadsheets/d/1Y6y_hTRG-FJ6RdWfF6vETzxpyHBKvCLG9GgXa4eelbM/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- MEMORIA ---
if 'pedido_temporal' not in st.session_state:
    st.session_state.pedido_temporal = []
if 'modo_editor' not in st.session_state:
    st.session_state.modo_editor = False

# --- FUNCIONES ---
def leer_menu():
    try:
        return conn.read(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", ttl=0).dropna(how="all")
    except:
        return pd.DataFrame(columns=["Categoria", "Producto", "Monto"])

# --- VENTANA GASTOS (CON LISTA DESPLEGABLE) ---
@st.dialog("💸 Registrar Gasto")
def modal_gastos():
    st.write("Detalla el gasto aquí:")
    monto = st.number_input("Monto ($)", min_value=0, step=500)
    desc = st.text_input("Descripción (Ej: Saco de pan)")
    
    # Lista desplegable para no ralentizar la app
    origen_plata = st.selectbox(
        "¿De dónde sale la plata?",
        ["Bebestible", "Comida", "Tienda", "Caja General"]
    )
    
    if st.button("Guardar Gasto"):
        if monto > 0 and desc:
            df_g = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Monto": int(monto), # Forzamos a que sea entero
                "Descripcion": desc,
                "Saco De": origen_plata
            }])
            df_act = conn.read(spreadsheet=URL_DIRECTA, worksheet="Gastos", ttl=0).dropna(how="all")
            conn.update(spreadsheet=URL_DIRECTA, worksheet="Gastos", data=pd.concat([df_act, df_g], ignore_index=True))
            st.success("Gasto registrado")
            st.rerun()

# --- VENTANA AGREGAR PRODUCTO ---
@st.dialog("➕ Nuevo Producto")
def modal_nuevo(cat):
    n = st.text_input(f"Nombre del {cat}")
    p = st.number_input("Precio ($)", min_value=0, step=100)
    if st.button("Guardar"):
        df_act = leer_menu()
        df_n = pd.DataFrame([{"Categoria": cat, "Producto": n, "Monto": int(p)}])
        conn.update(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", data=pd.concat([df_act, df_n], ignore_index=True))
        st.rerun()

# --- INTERFAZ ---
df_menu = leer_menu()
c1, c2, c3 = st.columns([2, 1, 1])
c1.title("🍴 Restaurante Santos")
if c2.button("💸 GASTOS", use_container_width=True): modal_gastos()
txt = "🔄 CERRAR EDITOR" if st.session_state.modo_editor else "➕ AGREGAR MENU HOY"
if c3.button(txt, use_container_width=True):
    st.session_state.modo_editor = not st.session_state.modo_editor
    st.rerun()

col_m, col_p = st.columns([3, 1])

with col_m:
    def mostrar_seccion(tit, cat):
        st.markdown(f"### {tit}")
        items = df_menu[df_menu["Categoria"] == cat]
        grid = st.columns(5)
        for i, (idx, row) in enumerate(items.iterrows()):
            with grid[i % 5]:
                if st.session_state.modo_editor:
                    if st.button("❌", key=f"d_{idx}"):
                        conn.update(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", data=df_menu.drop(idx))
                        st.rerun()
                # Formato CLP: Sin decimales y con punto de miles
                if st.button(f"{row['Producto']}\n\n${int(row['Monto']):,}".replace(",", "."), key=f"b_{idx}", use_container_width=True):
                    st.session_state.pedido_temporal.append(row.to_dict())
                    st.rerun()
        if st.session_state.modo_editor:
            with grid[len(items) % 5]:
                if st.button(f"➕\n\nNuevo\n{tit}", key=f"a_{cat}", use_container_width=True):
                    modal_nuevo(cat)

    with st.expander("🍔 COMIDA", expanded=True):
        t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
        with t1: mostrar_seccion("Desayuno", "Desayuno")
        with t2: mostrar_seccion("Almuerzo", "Almuerzo")
        with t3: mostrar_seccion("Cena", "Cena")
    mostrar_seccion("🥤 BEBESTIBLE", "Bebestible")
    mostrar_seccion("🏪 TIENDA", "Tienda")

with col_p:
    st.subheader("📝 Pedido")
    total = sum(int(i["Monto"]) for i in st.session_state.pedido_temporal)
    for i, item in enumerate(st.session_state.pedido_temporal):
        st.write(f"• {item['Producto']} (${int(item['Monto']):,})".replace(",", "."))
    st.divider()
    # Total en negrita y grande sin decimales
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
            st.session_state.pedido_temporal = []; st.rerun()
