import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import time

# 🎨 Configuración de pantalla
st.set_page_config(page_title="Restaurante Santos", layout="wide")

# ==========================================
# CONFIGURACIÓN DE SUPABASE ⚡
# ==========================================
URL_SUPABASE = "https://luklxueplpxdktreuloa.supabase.co"
KEY_SUPABASE = "sb_publishable_KxAtLO6z0_4SUtbpQDWekQ_mKXZZebX"
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# CSS para que el Pedido FLOTE
st.markdown("""
    <style>
    [data-testid="stSidebarUserContent"] { padding-top: 1rem; }
    .stColumn > div { position: sticky; top: 50px; height: auto; }
    </style>
""", unsafe_allow_html=True)

# --- MEMORIA ---
if 'pedido_temporal' not in st.session_state:
    st.session_state.pedido_temporal = []
if 'modo_editor' not in st.session_state:
    st.session_state.modo_editor = False

@st.cache_data(ttl=2)
def leer_menu_rapido():
    try: 
        response = supabase.table("menu_dia").select("*").execute()
        df = pd.DataFrame(response.data)
        return df if not df.empty else pd.DataFrame(columns=["id", "categoria", "producto", "monto"])
    except: 
        return pd.DataFrame(columns=["id", "categoria", "producto", "monto"])

# --- MODALES ---
@st.dialog("➕ Nuevo Producto")
def modal_nuevo(cat):
    n = st.text_input(f"Nombre del {cat}")
    p = st.number_input("Precio ($)", min_value=0, step=100)
    if st.button("Guardar"):
        if n and p > 0:
            supabase.table("menu_dia").insert({"categoria": cat, "producto": n, "monto": int(p)}).execute()
            st.cache_data.clear() 
            st.rerun()

@st.dialog("📲 Realizar Recarga")
def modal_recarga():
    op = st.selectbox("Operador", ["WOM", "ENTEL", "MOVISTAR", "CLARO"])
    m = st.number_input("Monto ($)", min_value=0, step=500)
    if st.button("Agregar al Pedido"):
        if m > 0:
            st.session_state.pedido_temporal.append({"categoria": "Recarga", "producto": f"Recarga {op}", "monto": int(m)})
            st.rerun()

@st.dialog("📦 Venta Especial")
def modal_otros():
    desc = st.text_input("¿Qué se vendió?")
    m = st.number_input("Monto ($)", min_value=0, step=100)
    if st.button("Agregar al Pedido"):
        if desc and m > 0:
            st.session_state.pedido_temporal.append({"categoria": "Otros", "producto": desc, "monto": int(m)})
            st.rerun()

@st.dialog("💸 Gasto")
def modal_gastos():
    m = st.number_input("Monto ($)", min_value=0, step=500)
    d = st.text_input("Descripción")
    o = st.selectbox("Saco De:", ["Comida", "Bebestible", "Tienda", "Recarga", "Chela", "Otros", "Caja General"])
    if st.button("Guardar Gasto"):
        supabase.table("gastos").insert({"monto": int(m), "descripcion": d, "origen": o}).execute()
        st.success("Gasto guardado")
        st.rerun()

# --- INTERFAZ ---
df_menu = leer_menu_rapido()
c1, c2, c3 = st.columns([2, 1, 1])
c1.title("🍴 Restaurante Santos")
if c2.button("💸 GASTOS", use_container_width=True): modal_gastos()

if c1.button("🔄 Sincronizar Datos"):
    st.cache_data.clear()
    st.rerun()

txt_btn = "🔄 CERRAR EDITOR" if st.session_state.modo_editor else "➕ AGREGAR MENU HOY"
if c3.button(txt_btn, use_container_width=True):
    st.session_state.modo_editor = not st.session_state.modo_editor
    st.rerun()

col_m, col_p = st.columns([3, 1])

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
            items = df_menu[df_menu["categoria"] == cat]
            for i, (idx, row) in enumerate(items.iterrows()):
                with grid[i % 5]:
                    if st.session_state.modo_editor:
                        if st.button("❌", key=f"d_{row['id']}"):
                            supabase.table("menu_dia").delete().eq("id", row['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                    p_f = f"${int(row['monto']):,}".replace(",", ".")
                    if st.button(f"{row['producto']}\n\n{p_f}", key=f"b_{row['id']}", use_container_width=True):
                        st.session_state.pedido_temporal.append({"categoria": row['categoria'], "producto": row['producto'], "monto": row['monto']})
                        st.rerun()
            if st.session_state.modo_editor:
                with grid[len(items) % 5]:
                    if st.button(f"➕\n\nNuevo\n{titulo}", key=f"a_{cat}", use_container_width=True): modal_nuevo(cat)

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
    total = sum(int(i["monto"]) for i in st.session_state.pedido_temporal)
    
    for i, item in enumerate(st.session_state.pedido_temporal):
        p_i = f"${int(item['monto']):,}".replace(",", ".")
        ctx, cbt = st.columns([4, 1])
        ctx.write(f"• {item['producto']} ({p_i})")
        if cbt.button("🗑️", key=f"del_ped_{i}"):
            st.session_state.pedido_temporal.pop(i)
            st.rerun()
            
    st.divider()
    st.markdown(f"## TOTAL: ${total:,}".replace(",", "."))
    
    if st.button("✅ FINALIZAR VENTA", type="primary", use_container_width=True):
        if st.session_state.pedido_temporal:
            try:
                ventas_to_insert = []
                for item in st.session_state.pedido_temporal:
                    es_comida = item["categoria"] in ["Desayuno", "Almuerzo", "Cena"]
                    ventas_to_insert.append({
                        "producto": item["producto"],
                        "monto": int(item["monto"]),
                        "categoria": item["categoria"],
                        "tipo": "PAGADO",
                        "estado_impresion": "IMPRESO" if es_comida else "N/A"
                    })

                supabase.table("ventas").insert(ventas_to_insert).execute()

                # 🖨️ Mandar a imprimir cada plato por separado
                for item in st.session_state.pedido_temporal:
                    if item["categoria"] in ["Desayuno", "Almuerzo", "Cena"]:
                        # DISEÑO NUEVO: Nombre local izquierda, Plato centro, Fecha abajo
                        ticket_html = f"""
                        <div style="width: 180px; font-family: sans-serif; padding: 0; margin: 0;">
                            <div style="font-size: 10px; text-align: left; margin-bottom: 5px;">Restaurante Santos</div>
                            <div style="text-align: center;">
                                <h2 style="font-size: 22px; margin: 2px 0; font-weight: bold; text-transform: uppercase;">{item['producto']}</h2>
                                <p style="font-size: 10px; margin: 0; color: #333;">({item['categoria']})</p>
                            </div>
                        </div>
                        """
                        # JS para imprimir SIN encabezados del navegador
                        js_print = f"""
                        <script>
                        var frame = document.createElement('iframe');
                        frame.style.display = 'none';
                        document.body.appendChild(frame);
                        var d = frame.contentWindow.document;
                        d.write('<html><head><style>@page {{ margin: 0; }} body {{ margin: 0.5cm; }}</style></head><body onload="window.print();">{ticket_html}</body></html>');
                        d.close();
                        </script>
                        """
                        components.html(js_print, height=0)
                        time.sleep(0.4) 

                st.success("✅ Venta Guardada e Impresa.")
                st.session_state.pedido_temporal = []
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
