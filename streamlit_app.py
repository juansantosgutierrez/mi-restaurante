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

@st.cache_data(ttl=2)
def leer_menu_rapido():
    try: 
        response = supabase.table("menu_dia").select("*").execute()
        df = pd.DataFrame(response.data)
        return df if not df.empty else pd.DataFrame(columns=["id", "categoria", "producto", "monto", "codigo"])
    except: 
        return pd.DataFrame(columns=["id", "categoria", "producto", "monto", "codigo"])

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

# --- NUEVO MODAL: CAJA VECINA ---
@st.dialog("🏦 CAJA VECINA")
def modal_cajavecina():
    st.write("Selecciona el monto cobrado:")
    opcion = st.radio("Monto rápido:", ["$1.000", "$2.000", "$3.000", "$4.000", "$5.000", "Otro monto"], horizontal=True, label_visibility="collapsed")
    
    monto_final = 0
    if opcion == "Otro monto":
        monto_custom = st.number_input("Ingresa el monto exacto ($)", min_value=0, step=1000, value=None)
        if monto_custom:
            monto_final = int(monto_custom)
    else:
        monto_final = int(opcion.replace("$", "").replace(".", ""))
        
    if st.button("✅ Registrar en Caja", type="primary", use_container_width=True):
        if monto_final > 0:
            st.session_state.pedido_temporal.append({
                "categoria": "CAJA VECINA", 
                "producto": "CAJA VECINA", 
                "monto": monto_final
            })
            st.rerun()

# --- MODAL DEBO ACTUALIZADO ---
@st.dialog("🤝 Registro DEBO / Vueltos Pendientes", width="large")
def modal_debo():
    with st.expander("➕ Agregar Nuevo Registro", expanded=False):
        nom = st.text_input("Nombre de la persona")
        c1, c2 = st.columns(2)
        with c1:
            mon_recibido = st.number_input("Monto que me dio ($)", min_value=0, step=100, value=None, placeholder="Ej: 5000")
        with c2:
            mon_devolver = st.number_input("Debo entregar: ($)", min_value=0, step=100, value=None, placeholder="Ej: 3000")
            
        desc = st.text_input("Descripción (Ej: Falta vuelto o Motivo)")
        
        if st.button("💾 Guardar Registro", type="primary"):
            if nom and desc:
                datos = {"nombre": filtro_estricto(nom), "descripcion": filtro_estricto(desc)}
                if mon_recibido is not None: datos["monto"] = int(mon_recibido)
                if mon_devolver is not None: datos["monto_devolver"] = int(mon_devolver)
                
                supabase.table("debo").insert(datos).execute()
                st.rerun() 
            else:
                st.error("Ingresa al menos el nombre y la descripción.")

    st.divider()
    st.caption("📅 Registros del día:")
    fecha_sel = st.date_input("Fecha", obtener_hora_chile().date(), label_visibility="collapsed")
    fecha_ini = f"{fecha_sel}T00:00:00"
    fecha_fin = f"{fecha_sel}T23:59:59"
    try:
        res = supabase.table("debo").select("*").gte("created_at", fecha_ini).lte("created_at", fecha_fin).order("created_at", desc=True).execute()
        registros = res.data
    except Exception: registros = []
        
    if not registros:
        st.info("ℹ️ No hay registros pendientes para esta fecha.")
    else:
        for item in registros:
            c1, c2, c3 = st.columns([5, 2, 2])
            with c1:
                t_dio = f" | Me dio: ${int(item['monto']):,}".replace(",", ".") if item.get('monto') else ""
                t_deb = f" | **DEBO DAR: ${int(item['monto_devolver']):,}**".replace(",", ".") if item.get('monto_devolver') else ""
                st.markdown(f"**👤 {item['nombre']}** {t_dio} {t_deb}")
                st.caption(f"📝 {item.get('descripcion', '')}")
            with c2:
                hora_bonita = formatear_hora_supabase(item.get('created_at', ''))
                st.caption(f"🕒 {hora_bonita}")
            with c3:
                if st.button("↩️ Devolver / Saldado", key=f"dev_{item['id']}"):
                    supabase.table("debo").delete().eq("id", item['id']).execute()
                    st.rerun()
            st.markdown("---")

def procesar_scanner():
    codigo_leido = filtro_estricto(st.session_state.lector_codigo)
    if codigo_leido:
        menu_actual = leer_menu_rapido() 
        if "codigo" in menu_actual.columns:
            menu_actual['codigo_str'] = menu_actual['codigo'].fillna('').astype(str).apply(filtro_estricto)
            producto_encontrado = menu_actual[menu_actual['codigo_str'] == codigo_leido]
            if not producto_encontrado.empty:
                row = producto_encontrado.iloc[0]
                
                prod_final = aplicar_bebida_desayuno(row['categoria'], row['producto'])
                
                st.session_state.pedido_temporal.append({
                    "categoria": filtro_estricto(row['categoria']), 
                    "producto": prod_final, 
                    "monto": row['monto']
                })
                st.session_state.msj_scanner = f"✅ {prod_final} agregado."
            else:
                st.session_state.msj_scanner = "❌ Producto no encontrado."
        else:
            st.session_state.msj_scanner = "⚠️ Falta la columna 'codigo'."
    st.session_state.lector_codigo = ""

# --- CARGAR DATOS ---
df_menu = leer_menu_rapido()

# --- INTERFAZ PRINCIPAL ---
c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
c1.title("🍴 Restaurante Santos")
if c2.button("💸 GASTOS", use_container_width=True): modal_gastos()
if c3.button("🤝 DEBO", use_container_width=True): modal_debo()
if c4.button("🏦 CAJA VECINA", use_container_width=True): modal_cajavecina()

if c1.button("🔄 Sincronizar Datos"):
    st.cache_data.clear()
    st.rerun()

txt_btn = "🔄 CERRAR EDITOR" if st.session_state.modo_editor else "➕ MENÚ HOY"
if c5.button(txt_btn, use_container_width=True):
    st.session_state.modo_editor = not st.session_state.modo_editor
    st.rerun()

col_m, col_p = st.columns([3, 1])

# COLUMNA IZQUIERDA: MENÚ
with col_m:
    def mostrar_seccion(titulo, cat, especial=None):
        st.header(titulo)
        grid = st.columns(5)
        if especial == "Otros":
            with grid[0]:
                if st.button("📦\n\nVENTA ESPECIAL", use_container_width=True): modal_otros()
        else:
            cat_limpia = filtro_estricto(cat)
            items = df_menu[df_menu["categoria"].apply(lambda x: filtro_estricto(str(x))) == cat_limpia]
            for i, (idx, row) in enumerate(items.iterrows()):
                with grid[i % 5]:
                    if st.session_state.modo_editor:
                        if st.button("❌", key=f"d_{row['id']}"):
                            supabase.table("menu_dia").delete().eq("id", row['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                    p_f = f"${int(row['monto']):,}".replace(",", ".")
                    
                    if st.button(f"{row['producto']}\n\n{p_f}", key=f"b_{row['id']}", use_container_width=True):
                        prod_final = aplicar_bebida_desayuno(row['categoria'], row['producto'])
                        
                        st.session_state.pedido_temporal.append({
                            "categoria": filtro_estricto(row['categoria']), 
                            "producto": prod_final, 
                            "monto": row['monto']
                        })
                        st.rerun()
            
            if st.session_state.modo_editor:
                with grid[len(items) % 5]:
                    btn_label = "➕\n\nNuevo\n" + str(titulo)
                    if st.button(btn_label, key="add_btn_" + cat, use_container_width=True):
                        modal_nuevo(cat)

    with st.expander("🍔 COMIDA", expanded=True):
        t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
        with t1: 
            st.radio("☕ Bebida incluida (Solo sándwiches/atún):", ["Ninguna", "Té", "Café", "Mate"], horizontal=True, key="bebida_desayuno")
            mostrar_seccion("Desayuno", "Desayuno")
        with t2: mostrar_seccion("Almuerzo", "Almuerzo")
        with t3: mostrar_seccion("Cena", "Cena")
    
    mostrar_seccion("🥤 BEBESTIBLE", "Bebestible")
    mostrar_seccion("🏪 TIENDA", "Tienda")
    mostrar_seccion("🍺 CHELA", "Chela")
    mostrar_seccion("📦 OTROS", "Otros", especial="Otros")

# COLUMNA DERECHA: CARRITO Y ESCÁNER INVISIBLE
with col_p:
    st.text_input("Lector Oculto", key="lector_codigo", on_change=procesar_scanner, placeholder="oculto_scanner", label_visibility="collapsed")
    
    components.html("""
        <script>
        function enfocarLector() {
            var parent = window.parent.document;
            var activo = parent.activeElement;
            if (activo && (activo.tagName === 'INPUT' || activo.tagName === 'TEXTAREA')) {
                if (activo.placeholder !== "oculto_scanner") { return; }
            }
            var lector = parent.querySelector('input[placeholder="oculto_scanner"]');
            if (lector) { lector.focus(); }
        }
        setInterval(enfocarLector, 500);
        </script>
    """, height=0)
    
    if st.session_state.msj_scanner:
        if "✅" in st.session_state.msj_scanner: st.success(st.session_state.msj_scanner)
        else: st.error(st.session_state.msj_scanner)
        st.session_state.msj_scanner = ""

    st.subheader("📝 Pedido Actual")
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
                    cat_limpia = filtro_estricto(item.get("categoria", "")).upper()
                    es_comida = cat_limpia in ["DESAYUNO", "ALMUERZO", "CENA"]
                    
                    ventas_to_insert.append({
                        "producto": item["producto"],
                        "monto": int(item["monto"]),
                        "categoria": item.get("categoria", ""),
                        "tipo": "PAGADO",
                        "estado_impresion": "PENDIENTE" if es_comida else "N/A"
                    })

                supabase.table("ventas").insert(ventas_to_insert).execute()
                
                conteo_comidas = {}
                for item in st.session_state.pedido_temporal:
                    cat_mayuscula = filtro_estricto(item.get("categoria", "")).upper()
                    
                    if cat_mayuscula in ["DESAYUNO", "ALMUERZO", "CENA"]:
                        prod_limpio = item.get("producto", "")
                        clave = (prod_limpio, cat_mayuscula)
                        conteo_comidas[clave] = conteo_comidas.get(clave, 0) + 1

                html_tickets = ""
                sello_invisible = f"<div id='{uuid.uuid4()}' style='display: none;'></div>"
                
                if conteo_comidas:
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
                else:
                    # TICKET FANTASMA PARA QUE LA GAVETA SALTE SI SOLO SON BEBIDAS O CAJA VECINA
                    html_tickets = "<div style='font-size: 1px; color: white;'>.</div>"
                
                # LA ORDEN DE IMPRESIÓN SE ENVÍA SIEMPRE
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

                st.session_state.pedido_temporal = []
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # --- ZONA SEGURA DE IMPRESIÓN ---
    if st.session_state.get("ticket_imprimir"):
        components.html(st.session_state.ticket_imprimir, height=0)
        st.success("✅ Venta registrada (Gaveta abriendo...).")
        st.session_state.ticket_imprimir = ""
