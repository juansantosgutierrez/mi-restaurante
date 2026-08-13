import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components
import time
import re
import uuid

# --- 🕒 FUNCIONES DE HORA CHILENA ---
def obtener_hora_chile():
    return datetime.now(ZoneInfo("America/Santiago"))

def formatear_hora_supabase(fecha_utc_str):
    try:
        dt = datetime.fromisoformat(fecha_utc_str.replace('Z', '+00:00'))
        dt_chile = dt.astimezone(ZoneInfo("America/Santiago"))
        return dt_chile.strftime("%H:%M hrs")
    except:
        return fecha_utc_str

# --- 🛡️ FILTRO DICTATORIAL ---
def filtro_estricto(texto):
    if not texto: return ""
    t = str(texto).upper()
    t = t.replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U').replace('Ñ','N')
    t_limpio = re.sub(r'[^A-Z0-9\s+]', '', t)
    return t_limpio.strip()

# --- ☕ FUNCIÓN INTELIGENTE PARA AGREGAR BEBIDA AL DESAYUNO ---
def aplicar_bebida_desayuno(categoria, producto):
    cat = filtro_estricto(categoria).upper()
    prod = filtro_estricto(producto).upper()
    
    if cat == "DESAYUNO":
        excluir = ["CALDO", "CAFE", "TE", "MATE"]
        if not any(x in prod for x in excluir):
            bebida_seleccionada = st.session_state.get("bebida_desayuno", "Ninguna")
            if bebida_seleccionada != "Ninguna":
                prod = f"{prod} + {filtro_estricto(bebida_seleccionada).upper()}"
    return prod

# 🎨 Configuración de pantalla
st.set_page_config(page_title="Restaurante Santos", layout="wide")

URL_SUPABASE = "https://luklxueplpxdktreuloa.supabase.co"
KEY_SUPABASE = "sb_publishable_KxAtLO6z0_4SUtbpQDWekQ_mKXZZebX"
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

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

if 'pedido_temporal' not in st.session_state:
    st.session_state.pedido_temporal = []
if 'modo_editor' not in st.session_state:
    st.session_state.modo_editor = False
if 'msj_scanner' not in st.session_state:
    st.session_state.msj_scanner = ""
if 'ticket_imprimir' not in st.session_state:
    st.session_state.ticket_imprimir = None

@st.cache_data(ttl=2)
def leer_menu_rapido():
    try: 
        response = supabase.table("menu_dia").select("*").execute()
        df = pd.DataFrame(response.data)
        return df if not df.empty else pd.DataFrame(columns=["id", "categoria", "producto", "monto", "codigo"])
    except: 
        return pd.DataFrame(columns=["id", "categoria", "producto", "monto", "codigo"])

# --- FUNCION MAESTRA PARA COBRAR E IMPRIMIR ---
def ejecutar_finalizar_venta():
    if not st.session_state.pedido_temporal:
        return

    ventas_to_insert = []
    
    for item in st.session_state.pedido_temporal:
        cat_limpia = filtro_estricto(item.get("categoria", "")).upper()
        es_comida = cat_limpia in ["DESAYUNO", "ALMUERZO", "CENA"]
        
        ventas_to_insert.append({
            "producto": item["producto"],
            "monto": int(item["monto"]),
            "categoria": item.get("categoria", ""),
            "tipo": "PAGADO",
            "estado_impresion": "PENDIENTE" if es_comida else "N/A"
        })

    # Guardar en base de datos
    supabase.table("ventas").insert(ventas_to_insert).execute()
    
    # Procesar conteo para impresión
    conteo_comidas = {}
    for item in st.session_state.pedido_temporal:
        cat_mayuscula = filtro_estricto(item.get("categoria", "")).upper()
        
        if cat_mayuscula in ["DESAYUNO", "ALMUERZO", "CENA"]:
            prod_limpio = item.get("producto", "")
            clave = (prod_limpio, cat_mayuscula)
            conteo_comidas[clave] = conteo_comidas.get(clave, 0) + 1

    # SOLUCIÓN AL ERROR: Solo generar HTML si hay comidas reales que imprimir
    if conteo_comidas:
        html_tickets = ""
        sello_invisible = f"<div id='{uuid.uuid4()}' style='display: none;'></div>"
        fecha_ticket = obtener_hora_chile().strftime("%d/%m/%y, %H:%M")
        
        for (prod, cat), cantidad in conteo_comidas.items():
            texto_cantidad = f"{cantidad}x " if cantidad > 1 else ""
            
            if " + " in prod:
                partes = prod.split(" + ")
                comida_principal = partes[0]
                bebida_agregada = f"<div style='font-size: 20px; font-weight: bold; margin-top: 2px; color: #000;'>+ {partes[1]}</div>"
            else:
                comida_principal = prod
                bebida_agregada = ""

            html_tickets += f"""
            <div style="page-break-after: always; text-align: left; width: 100%; font-family: 'Arial', sans-serif; padding: 0; margin: 0;">
                <p style="font-size: 12px; margin: 0; color: #000;">{fecha_ticket}</p>
                <p style="font-size: 12px; margin: 0; margin-bottom: 15px; color: #000;">Restaurante Santos</p>
                
                <div style="text-align: center; margin-top: 10px;">
                    <h1 style="font-size: 28px; margin: 0; font-weight: bold; text-transform: uppercase; line-height: 1.1;">{texto_cantidad}{comida_principal}</h1>
                    {bebida_agregada}
                    <p style="font-size: 14px; margin: 5px 0 20px 0; text-transform: uppercase; color: #000;">({cat})</p>
                </div>
            </div>
            """
        
        html_completo = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ margin: 0; }} 
                body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
            </style>
        </head>
        <body onload="setTimeout(function(){{ window.print(); }}, 500);">
            {html_tickets}
            {sello_invisible}
        </body>
        </html>
        """
        st.session_state.ticket_imprimir = html_completo
    else:
        # Si solo se escaneó bebida (ej: Coca-Cola), no se manda nada a la impresora
        st.session_state.ticket_imprimir = None
    
    # Limpiar el pedido actual
    st.session_state.pedido_temporal = []


@st.dialog("➕ Nuevo Producto")
def modal_nuevo(cat):
    n = st.text_input(f"Nombre del {cat}")
    p = st.number_input("Precio ($)", min_value=0, step=100, value=None, placeholder="Ej: 1500")
    c = st.text_input("Código de Barras (Opcional - Pistolea aquí)")
    if st.button("Guardar"):
        if n and p is not None and p > 0:
            datos_nuevos = {"categoria": filtro_estricto(cat), "producto": filtro_estricto(n), "monto": int(p)}
            if c: datos_nuevos["codigo"] = filtro_estricto(c)
            supabase.table("menu_dia").insert(datos_nuevos).execute()
            st.cache_data.clear() 
            st.rerun()

@st.dialog("📦 Venta Especial")
def modal_otros():
    desc = st.text_input("¿Qué se vendió?")
    m = st.number_input("Monto ($)", min_value=0, step=100, value=None, placeholder="Ej: 5000")
    if st.button("Agregar al Pedido"):
        if desc and m is not None and m > 0:
            st.session_state.pedido_temporal.append({"categoria": "OTROS", "producto": filtro_estricto(desc), "monto": int(m)})
            st.rerun()

@st.dialog("💸 Gasto")
def modal_gastos():
    ahora = obtener_hora_chile()
    st.info(f"🕒 **Registro de Gasto** ({ahora.strftime('%H:%M')} hrs)")
    m = st.number_input("Monto ($)", min_value=0, step=500, value=None, placeholder="Ej: 10000")
    d = st.text_input("Descripción")
    if st.button("Guardar Gasto"):
        if m is not None and m > 0:
            supabase.table("gastos").insert({"monto": int(m), "descripcion": filtro_estricto(d)}).execute()
            st.success("Gasto guardado correctamente")
            st.rerun()

@st.dialog("🏦 CAJA VECINA")
def modal_cajavecina():
    st.caption("Selección rápida:")
    # (El resto del código de tu interfaz abajo debe renderizar components.html(st.session_state.ticket_imprimir) solo si no es None)
