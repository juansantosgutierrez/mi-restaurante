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

# --- VENTANA: RECARGAS ---
@st.dialog("📲 Realizar Recarga")
def modal_recarga():
    operador = st.selectbox("Selecciona Operador", ["WOM", "ENTEL", "MOVISTAR", "CLARO"])
    monto_r = st.number_input("Monto de la Recarga ($)", min_value=0, step=500)
    if st.button("Agregar al Pedido"):
        if monto_r > 0:
            st.session_state.pedido_temporal.append({
                "Categoria": "Recarga", "Producto": f"Recarga {operador}", "Monto": int(monto_r)
            })
            st.rerun()

# --- VENTANA: OTROS (Venta Especial) ---
@st.dialog("📦 Venta Especial / Otros")
def modal_otros():
    descripcion = st.text_input("¿Qué se vendió?")
    monto_o = st.number_input("Monto ($)", min_value=0, step=100)
    if st.button("Agregar al Pedido"):
        if descripcion and monto_o > 0:
            st.session_state.pedido_temporal.append({
                "Categoria": "Otros", "Producto": descripcion, "Monto": int(monto_o)
            })
            st.rerun()

# --- VENTANA: GASTOS ---
@st.dialog("💸 Registrar Gasto")
def modal_gastos():
    m = st.number_input("Monto ($)", min_value=0, step=500)
    d = st.text_input("Descripción")
    o = st.selectbox("¿De dónde sale la plata?", ["Comida", "Bebestible", "Tienda", "Recarga", "Chela", "Otros", "Caja General"])
    if st.button("Guardar Gasto"):
        df_g = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "Monto": int(m), "Descripcion": d, "Saco De": o}])
        df_act = conn.read(spreadsheet=URL_DIRECTA, worksheet="Gastos", ttl=0).dropna(how="all")
        conn.update(spreadsheet=URL_DIRECTA, worksheet="Gastos", data=pd.concat([df_act, df_g], ignore_index=True))
        st.rerun()

# --- LÓGICA DE INTERFAZ ---
def leer_menu():
    try: return conn.read(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", ttl=0).dropna(how="all")
    except: return pd.DataFrame(columns=["Categoria", "Producto", "Monto"])

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
    def mostrar_seccion(tit, cat, especial=None):
        st.markdown(f"---")
        st.markdown(f"### {tit}")
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
                        if st.button("❌", key=f"d_{idx}"):
                            conn.update(spreadsheet=URL_DIRECTA, worksheet="Menu_Dia", data=df_menu.drop(idx))
                            st.rerun()
                    p_fmt = f"${int(row['Monto']):,}".replace(",", ".")
                    if st.button(f"{row['Producto']}\n\n{p_fmt}", key=f"b_{idx}", use_container_width=True):
                        st.session_state.pedido_temporal.append(row.to_dict())
                        st.rerun()
            if st.session_state.modo_editor:
                with grid[len(items) % 5]:
                    if st.button(f"➕\n\nNuevo\n{tit}", key=f"a_{cat}", use_container_width=True):
                        # Aquí llamarías al modal_nuevo creado anteriormente
                        pass

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
    st.subheader("📝 Pedido")
    total = sum(int(i["Monto"]) for i in st.session_state.pedido_temporal)
    for item in st.session_state.pedido_temporal:
        st.write(f"• {item['Producto']} (${int(item['Monto']):,})".replace(",", "."))
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
            st.session_state.pedido_temporal = []; st.rerun()
