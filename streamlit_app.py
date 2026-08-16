import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components
import re
import uuid

# --- 🕒 FUNCIONES DE HORA CHILENA ---
def obtener_hora_chile():
    return datetime.now(ZoneInfo("America/Santiago"))

# --- 🛡️ FILTRO DICTATORIAL (Rápido) ---
def filtro_estricto(texto):
    if not texto: return ""
    t = str(texto).upper().translate(str.maketrans('ÁÉÍÓÚÑ', 'AEIOUN'))
    return re.sub(r'[^A-Z0-9\s+]', '', t).strip()

# 🎨 Configuración de pantalla ultra-ancha
st.set_page_config(page_title="Restaurante Santos", layout="wide")

# CONEXIÓN SUPABASE (Optimizada para no recargar)
@st.cache_resource
def init_connection():
    URL_SUPABASE = "https://luklxueplpxdktreuloa.supabase.co"
    KEY_SUPABASE = "sb_publishable_KxAtLO6z0_4SUtbpQDWekQ_mKXZZebX"
    return create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = init_connection()

st.markdown("""
    <style>
    [data-testid="stSidebarUserContent"] { padding-top: 1rem; }
    .stColumn > div { position: sticky; top: 50px; height: auto; }
    div[data-testid="stTextInput"]:has(input[placeholder="oculto_scanner"]) {
        position: absolute !important; left: -9999px !important; opacity: 0 !important;
        height: 0px !important; width: 0px !important; margin: 0 !important; padding: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# INICIALIZAR VARIABLES
for key in ['pedido_temporal', 'modo_editor', 'lector_codigo', 'ticket_imprimir', 'msj_toast']:
    if key not in st.session_state:
        st.session_state[key] = [] if key == 'pedido_temporal' else (False if key == 'modo_editor' else "")

# CACHÉ DEL MENÚ (Ultra rápido)
@st.cache_data(ttl=2)
def leer_menu_rapido():
    try: 
        df = pd.DataFrame(supabase.table("menu_dia").select("*").execute().data)
        return df if not df.empty else pd.DataFrame(columns=["id", "categoria", "producto", "monto", "codigo"])
    except: 
        return pd.DataFrame(columns=["id", "categoria", "producto", "monto", "codigo"])

df_menu = leer_menu_rapido()

# --- FUNCION MAESTRA PARA COBRAR E IMPRIMIR ---
def ejecutar_finalizar_venta():
    if not st.session_state.pedido_temporal: return

    ventas_to_insert = []
    conteo_comidas = {}
    
    for item in st.session_state.pedido_temporal:
        cat_limpia = filtro_estricto(item.get("categoria", ""))
        es_comida = cat_limpia in ["DESAYUNO", "ALMUERZO", "CENA"]
        
        ventas_to_insert.append({
            "producto": item["producto"],
            "monto": int(item["monto"]),
            "categoria": item.get("categoria", ""),
            "tipo": "PAGADO",
            "estado_impresion": "PENDIENTE" if es_comida else "N/A"
        })
        
        if es_comida:
            clave = (item.get("producto", ""), cat_limpia)
            conteo_comidas[clave] = conteo_comidas.get(clave, 0) + 1

    supabase.table("ventas").insert(ventas_to_insert).execute()

    if conteo_comidas:
        html_tickets = ""
        fecha_ticket = obtener_hora_chile().strftime("%d/%m/%y, %H:%M")
        
        for (prod, cat), cantidad in conteo_comidas.items():
            texto_cantidad = f"{cantidad}x " if cantidad > 1 else ""
            partes = prod.split(" + ")
            comida_principal = partes[0]
            bebida_agregada = f"<div style='font-size: 20px; font-weight: bold; margin-top: 2px; color: #000;'>+ {partes[1]}</div>" if len(partes) > 1 else ""

            html_tickets += f"""
            <div style="page-break-after: always; text-align: left; width: 100%; font-family: 'Arial', sans-serif; padding: 0; margin: 0; color: black;">
                <p style="font-size: 12px; margin: 0;">{fecha_ticket}</p>
                <p style="font-size: 12px; margin: 0; margin-bottom: 15px;">Restaurante Santos</p>
                <div style="text-align: center; margin-top: 10px;">
                    <h1 style="font-size: 28px; margin: 0; font-weight: bold; text-transform: uppercase; line-height: 1.1;">{texto_cantidad}{comida_principal}</h1>
                    {bebida_agregada}
                    <p style="font-size: 14px; margin: 5px 0 20px 0; text-transform: uppercase;">({cat})</p>
                </div>
            </div>
            """
        
        # SISTEMA DE IMPRESIÓN DIRECTO (Codificación nativa sin trucos raros, 100% anti letras chinas)
        st.session_state.ticket_imprimir = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>@page {{ margin: 0; }} body {{ margin: 0; padding: 0; }}</style>
        </head>
        <body>
            {html_tickets}
            <script>
                setTimeout(function(){{ window.print(); }}, 1000);
            </script>
        </body>
        </html>
        """
        st.session_state.msj_toast = "✅ Venta registrada (Imprimiendo Ticket)"
    else:
        st.session_state.ticket_imprimir = ""
        st.session_state.msj_toast = "✅ Venta rápida registrada (Sin ticket)."
        
    st.session_state.pedido_temporal = []

# --- MODALES OPTIMIZADOS CON TECLA ENTER ---

@st.dialog("☕ Elegir Bebida")
def modal_desayuno(row):
    st.write(f"Has seleccionado: **{row['producto']}**")
    with st.form("form_bebida", clear_on_submit=True):
        bebida = st.radio("¿Qué bebida llevará?", ["Ninguna", "Té", "Café", "Mate"], horizontal=True)
        if st.form_submit_button("✅ Confirmar y Agregar", type="primary", use_container_width=True):
            prod = row['producto']
            if bebida != "Ninguna":
                prod = f"{prod} + {filtro_estricto(bebida)}"
            
            st.session_state.pedido_temporal.append({
                "categoria": filtro_estricto(row['categoria']), 
                "producto": prod, 
                "monto": row['monto']
            })
            st.rerun()

@st.dialog("➕ Nuevo Producto")
def modal_nuevo(cat):
    with st.form("form_nuevo_prod", clear_on_submit=True):
        n = st.text_input(f"Nombre del {cat}")
        p = st.number_input("Precio ($)", min_value=0, step=100, value=None)
        c = st.text_input("Código de Barras (Opcional)")
        if st.form_submit_button("Guardar (Presiona Enter)"):
            if n and p:
                datos = {"categoria": filtro_estricto(cat), "producto": filtro_estricto(n), "monto": int(p)}
                if c: datos["codigo"] = filtro_estricto(c)
                supabase.table("menu_dia").insert(datos).execute()
                st.cache_data.clear()
                st.rerun()

@st.dialog("📦 Venta Especial")
def modal_otros():
    with st.form("form_otros", clear_on_submit=True):
        desc = st.text_input("¿Qué se vendió?")
        m = st.number_input("Monto ($)", min_value=0, step=100, value=None)
        if st.form_submit_button("Agregar al Pedido (Presiona Enter)"):
            if desc and m:
                st.session_state.pedido_temporal.append({"categoria": "OTROS", "producto": filtro_estricto(desc), "monto": int(m)})
                st.rerun()

@st.dialog("💸 Gasto")
def modal_gastos():
    with st.form("form_gasto", clear_on_submit=True):
        m = st.number_input("Monto ($)", min_value=0, step=500, value=None)
        d = st.text_input("Descripción")
        if st.form_submit_button("Guardar Gasto (Presiona Enter)"):
            if m:
                supabase.table("gastos").insert({"monto": int(m), "descripcion": filtro_estricto(d)}).execute()
                st.success("Guardado")
                st.rerun()

@st.dialog("🏦 CAJA VECINA")
def modal_cajavecina():
    montos = [1000, 2000, 3000, 4000, 5000]
    cols = st.columns(3) + st.columns(2)
    for idx, monto in enumerate(montos):
        if cols[idx].button(f"${monto:,}".replace(',', '.'), use_container_width=True):
            st.session_state.pedido_temporal.append({"categoria": "CAJA VECINA", "producto": "CAJA VECINA", "monto": monto})
            st.rerun()
    st.divider()
    with st.form("form_cv", clear_on_submit=True):
        m_custom = st.number_input("Otro monto ($):", min_value=0, step=500, value=None)
        if st.form_submit_button("✅ Agregar (Presiona Enter)", type="primary", use_container_width=True):
            if m_custom:
                st.session_state.pedido_temporal.append({"categoria": "CAJA VECINA", "producto": "CAJA VECINA", "monto": int(m_custom)})
                st.rerun()

@st.dialog("🤝 Vender y Dejar Vuelto Pendiente")
def modal_venta_debo(total_venta):
    st.markdown(f"### Total: **${total_venta:,}**".replace(",", "."))
    nom = st.text_input("Nombre del cliente")
    mon = st.number_input("Monto que dio ($)", min_value=total_venta, step=1000, value=total_venta)
    deuda = mon - total_venta
    st.info(f"**Vuelto pendiente:** ${deuda:,}".replace(",", "."))
    
    if st.button("✅ Confirmar Venta", type="primary", use_container_width=True):
        if nom and deuda > 0:
            supabase.table("debo").insert({"nombre": filtro_estricto(nom), "descripcion": "Vuelto pendiente", "monto": int(mon), "monto_devolver": int(deuda)}).execute()
            ejecutar_finalizar_venta()
            st.rerun()
        elif deuda <= 0: st.warning("Usa Venta Exacta.")
        else: st.error("Falta el nombre.")

# LÓGICA DEL ESCÁNER INVISIBLE
def procesar_scanner():
    codigo = filtro_estricto(st.session_state.lector_codigo)
    if codigo and "codigo" in df_menu.columns:
        df_menu['codigo_str'] = df_menu['codigo'].fillna('').astype(str).apply(filtro_estricto)
        encontrado = df_menu[df_menu['codigo_str'] == codigo]
        if not encontrado.empty:
            row = encontrado.iloc[0]
            cat_limpia = filtro_estricto(row['categoria'])
            # Si el escáner lee un desayuno que casualmente tenía código de barras (raro, pero por si acaso):
            if cat_limpia == "DESAYUNO" and not any(x in row['producto'] for x in ["CALDO", "CAFE", "TE", "MATE"]):
                # Agregar sin bebida directo para no interrumpir el flujo del escáner
                st.session_state.pedido_temporal.append({"categoria": cat_limpia, "producto": row['producto'], "monto": row['monto']})
            else:
                st.session_state.pedido_temporal.append({"categoria": cat_limpia, "producto": row['producto'], "monto": row['monto']})
            
            st.session_state.msj_toast = f"✅ Escaneado"
        else:
            st.session_state.msj_toast = "❌ Producto no encontrado"
    st.session_state.lector_codigo = ""

# --- INTERFAZ PRINCIPAL ---
c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
c1.title("🍴 Restaurante Santos")
if c2.button("💸 GASTOS", use_container_width=True): modal_gastos()
if c3.button("🔄 DATOS", use_container_width=True): st.cache_data.clear(); st.rerun()
if c4.button("🏦 C. VECINA", use_container_width=True): modal_cajavecina()
if c5.button("🔄 EDITOR" if st.session_state.modo_editor else "➕ MENÚ", use_container_width=True):
    st.session_state.modo_editor = not st.session_state.modo_editor
    st.rerun()

col_m, col_p = st.columns([3, 1])

# LADO IZQUIERDO (BOTONES)
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
            for i, (_, row) in enumerate(items.iterrows()):
                with grid[i % 5]:
                    if st.session_state.modo_editor:
                        if st.button("❌", key=f"d_{row['id']}"):
                            supabase.table("menu_dia").delete().eq("id", row['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                            
                    # BOTONES DEL MENÚ
                    if st.button(f"{row['producto']}\n\n${int(row['monto']):,}".replace(",", "."), key=f"b_{row['id']}", use_container_width=True):
                        # Lógica especial para el desayuno (Abre la ventanita)
                        if cat_limpia == "DESAYUNO" and not any(x in filtro_estricto(row['producto']) for x in ["CALDO", "CAFE", "TE", "MATE"]):
                            modal_desayuno(row)
                        else:
                            st.session_state.pedido_temporal.append({
                                "categoria": cat_limpia, 
                                "producto": row['producto'], 
                                "monto": row['monto']
                            })
                            st.rerun()
                            
            if st.session_state.modo_editor:
                with grid[len(items) % 5]:
                    if st.button(f"➕\n\nNuevo\n{titulo}", key=f"add_{cat}", use_container_width=True): modal_nuevo(cat)

    with st.expander("🍔 COMIDA", expanded=True):
        t1, t2, t3 = st.tabs(["🍳 Desayuno", "🍲 Almuerzo", "🌙 Cena"])
        with t1: mostrar_seccion("Desayuno", "Desayuno")
        with t2: mostrar_seccion("Almuerzo", "Almuerzo")
        with t3: mostrar_seccion("Cena", "Cena")
    
    mostrar_seccion("🥤 BEBESTIBLE", "Bebestible")
    mostrar_seccion("🏪 TIENDA", "Tienda")
    mostrar_seccion("🍺 CHELA", "Chela")
    mostrar_seccion("📦 OTROS", "Otros", especial="Otros")

# LADO DERECHO (CARRITO)
with col_p:
    st.text_input("Lector", key="lector_codigo", on_change=procesar_scanner, placeholder="oculto_scanner", label_visibility="collapsed")
    components.html("""
        <script>
        setInterval(() => {
            var el = window.parent.document.querySelector('input[placeholder="oculto_scanner"]');
            if(el && document.activeElement !== el) el.focus();
        }, 800);
        </script>
    """, height=0)

    st.subheader("📝 Pedido")
    total = sum(int(i["monto"]) for i in st.session_state.pedido_temporal)
    
    for i, item in enumerate(st.session_state.pedido_temporal):
        ctx, cbt = st.columns([4, 1])
        ctx.write(f"• {item['producto']} (${int(item['monto']):,})".replace(",", "."))
        if cbt.button("🗑️", key=f"del_{i}"): 
            st.session_state.pedido_temporal.pop(i)
            st.rerun()
            
    st.divider()
    st.markdown(f"## TOTAL: \${total:,}".replace(",", "."))
    
    if st.session_state.pedido_temporal:
        if st.button("✅ PAGO EXACTO", type="primary", use_container_width=True):
            ejecutar_finalizar_venta()
            st.rerun()
                
        c_v2 = st.columns([1, 2, 1])[1]
        if c_v2.button("🤝 VUELTO PEND.", use_container_width=True): modal_venta_debo(total)

    if st.session_state.ticket_imprimir:
        components.html(st.session_state.ticket_imprimir, height=0, width=0)
        st.session_state.ticket_imprimir = ""
        
    if st.session_state.msj_toast:
        st.toast(st.session_state.msj_toast, icon="✅")
        st.session_state.msj_toast = ""
