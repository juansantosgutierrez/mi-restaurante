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

# CSS: Hace que el pedido flote y oculta el lector
st.markdown("""
    <style>
    [data-testid="stSidebarUserContent"] { padding-top: 1rem; }
    .stColumn > div { position: sticky; top: 50px; height: auto; }
    
    div[data-testid="stTextInput"]:has(input[placeholder="oculto_scanner"]) {
        position: absolute !important;
        left: -9999px !important;
        opacity: 0 !important;
        height: 0px !important;
        width: 0px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- MEMORIA Y CACHÉ ---
if 'pedido_temporal' not in st.session_state:
    st.session_state.pedido_temporal = []
if 'modo_editor' not in st.session_state:
    st.session_state.modo_editor = False
if 'msj_scanner' not in st.session_state:
    st.session_state.msj_scanner = ""

@st.cache_data(ttl=2)
def leer_menu_rapido():
    try: 
        response = supabase.table("menu_dia").select("*").execute()
        df = pd.DataFrame(response.data)
        return df if not df.empty else pd.DataFrame(columns=["id", "categoria", "producto", "monto", "codigo"])
    except: 
        return pd.DataFrame(columns=["id", "categoria", "producto", "monto", "codigo"])

# --- MODALES ---
@st.dialog("➕ Nuevo Producto")
def modal_nuevo(cat):
    n = st.text_input(f"Nombre del {cat}")
    p = st.number_input("Precio ($)", min_value=0, step=100, value=None, placeholder="Ej: 1500")
    c = st.text_input("Código de Barras (Opcional - Pistolea aquí)")
    
    if st.button("Guardar"):
        if n and p is not None and p > 0:
            datos_nuevos = {"categoria": cat, "producto": n, "monto": int(p)}
            if c:
                datos_nuevos["codigo"] = c.strip()
            supabase.table("menu_dia").insert(datos_nuevos).execute()
            st.cache_data.clear() 
            st.rerun()

@st.dialog("📦 Venta Especial")
def modal_otros():
    desc = st.text_input("¿Qué se vendió?")
    m = st.number_input("Monto ($)", min_value=0, step=100, value=None, placeholder="Ej: 5000")
    if st.button("Agregar al Pedido"):
        if desc and m is not None and m > 0:
            st.session_state.pedido_temporal.append({"categoria": "Otros", "producto": desc, "monto": int(m)})
            st.rerun()

@st.dialog("💸 Gasto")
def modal_gastos():
    st.info("🕒 **Registro de Gasto** (La hora se guarda automáticamente)")
    m = st.number_input("Monto ($)", min_value=0, step=500, value=None, placeholder="Ej: 10000")
    d = st.text_input("Descripción")
    
    if st.button("Guardar Gasto"):
        if m is not None and m > 0:
            supabase.table("gastos").insert({
                "monto": int(m), 
                "descripcion": d
            }).execute()
            st.success("Gasto guardado correctamente")
            st.rerun()

@st.dialog("🤝 Registro DEBO / Vueltos Pendientes", width="large")
def modal_debo():
    with st.expander("➕ Agregar Nuevo Registro", expanded=False):
        nom = st.text_input("Nombre de la persona")
        mon = st.number_input("Monto ($)", min_value=0, step=100, value=None, placeholder="Ej: 2000 (Opcional)", key="debo_monto")
        desc = st.text_input("Descripción (Ej: Vuelto pendiente $1000)")
        if st.button("💾 Guardar Registro", type="primary"):
            if nom and desc:
                datos = {"nombre": nom, "descripcion": desc}
                if mon is not None and mon > 0:
                    datos["monto"] = int(mon)
                supabase.table("debo").insert(datos).execute()
                st.rerun() 
            else:
                st.error("Ingresa al menos el nombre y la descripción.")

    st.divider()
    
    st.caption("📅 Registros del día:")
    fecha_sel = st.date_input("Fecha", datetime.now(), label_visibility="collapsed")
    fecha_ini = f"{fecha_sel}T00:00:00"
    fecha_fin = f"{fecha_sel}T23:59:59"
    
    try:
        res = supabase.table("debo").select("*").gte("created_at", fecha_ini).lte("created_at", fecha_fin).order("created_at", desc=True).execute()
        registros = res.data
    except Exception as err:
        registros = []
        
    if not registros:
        st.info("ℹ️ No hay registros pendientes para esta fecha.")
    else:
        for item in registros:
            c1, c2, c3 = st.columns([5, 2, 2])
            with c1:
                monto_str = f" (${int(item['monto']):,})".replace(",", ".") if item.get('monto') else ""
                st.markdown(f"**👤 {item['nombre']}**{monto_str}")
                st.caption(f"📝 {item.get('descripcion', '')}")
            with c2:
                try:
                    dt = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                    f_format = dt.strftime("%H:%M hrs")
                except:
                    f_format = item.get('created_at', '')
                st.caption(f"🕒 {f_format}")
            with c3:
                if st.button("↩️ Devolver", key=f"dev_{item['id']}"):
                    supabase.table("debo").delete().eq("id", item['id']).execute()
                    st.rerun()
            st.markdown("---")

def procesar_scanner():
    codigo_leido = st.session_state.lector_codigo.strip()
    if codigo_leido:
        menu_actual = leer_menu_rapido() 
        if "codigo" in menu_actual.columns:
            menu_actual['codigo_str'] = menu_actual['codigo'].fillna('').astype(str).str.strip()
            producto_encontrado = menu_actual[menu_actual['codigo_str'] == codigo_leido]
            if not producto_encontrado.empty:
                row = producto_encontrado.iloc[0]
                st
