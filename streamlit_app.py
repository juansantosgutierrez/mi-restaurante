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

# CSS: Hace que el pedido flote y hace INVISIBLE la barra del escáner
st.markdown("""
    <style>
    [data-testid="stSidebarUserContent"] { padding-top: 1rem; }
    .stColumn > div { position: sticky; top: 50px; height: auto; }
    
    /* 🪄 MAGIA: Oculta la barra del escáner pero la mantiene activa en el fondo */
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

# --- MODALES (SIN EL CERO MOLESTO) ---
@st.dialog("➕ Nuevo Producto")
def modal_nuevo(cat):
    n = st.text_input(f"Nombre del {cat}")
    # value=None hace que empiece en blanco sin el 0
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

@st.dialog("📲 Realizar Recarga")
def modal_recarga():
    op = st.selectbox("Operador", ["WOM", "ENTEL", "MOVISTAR", "CLARO"])
    m = st.number_input("Monto ($)", min_value=0, step=500, value=None, placeholder="Ej: 2000")
    if st.button("Agregar al Pedido"):
        if m is not None and m > 0:
            st.session_state.pedido_temporal.append({"categoria": "Recarga", "producto": f"Recarga {op}", "monto": int(m)})
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
    m = st.number_input("Monto ($)", min_value=0, step=500, value=None, placeholder="Ej: 10000")
    d = st.text_input("Descripción")
    o = st.selectbox("Saco De:", ["Comida", "Bebestible", "Tienda", "Recarga", "Chela", "Otros", "Caja General"])
    if st.button("Guardar Gasto"):
        if m is not None and m > 0:
            supabase.table("gastos").insert({"monto": int(m), "descripcion": d, "origen": o}).execute()
            st.success("Gasto guardado")
            st.rerun()

# --- FUNCIÓN DEL LECTOR DE CÓDIGOS INVISIBLE ---
def procesar_scanner():
    codigo_leido = st.session_state.lector_codigo.strip()
    if codigo_leido:
        menu_actual = leer_menu_rapido() # Trae los datos frescos
        if "codigo" in menu_actual.columns:
            menu_actual['codigo_str'] = menu_actual['codigo'].fillna('').astype(str).str.strip()
            producto_encontrado = menu_actual[menu_actual['codigo_str'] == codigo_leido]
            
            if not producto_encontrado.empty:
                row = producto_encontrado.iloc[0]
                st.session_state.pedido_temporal.append({
                    "categoria": row['categoria'], 
                    "producto": row['producto'], 
                    "monto": row['monto']
                })
                st.session_state.msj_scanner = f"✅ {row['producto']} agregado."
            else:
                st.session_state.msj_scanner = "❌ Producto no encontrado."
        else:
            st.session_state.msj_scanner = "⚠️ Falta la columna 'codigo'."
            
    # Limpia la caja oculta automáticamente
    st.session_state.lector_codigo = ""

# --- CARGAR DATOS ---
df_menu = leer_menu_rapido()

# --- INTERFAZ PRINCIPAL ---
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

# COLUMNA IZQUIERDA: MENÚ
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
                    btn_label = "➕\n\nNuevo\n" + str(titulo)
                    if st.button(btn_label, key="add_btn_" + cat, use_container_width=True):
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

# COLUMNA DERECHA: CARRITO Y ESCÁNER INVISIBLE
with col_p:
    # 🔫 ESCÁNER 100% INVISIBLE: Escucha en el fondo todo el tiempo
    st.text_input("Lector Oculto", key="lector_codigo", on_change=procesar_scanner, placeholder="oculto_scanner", label_visibility="collapsed")
    
    # Este script JavaScript hace que siempre esté listo para pistolear, sin hacer clic
    components.html("""
        <script>
        function enfocarLector() {
            var parent = window.parent.document;
            var activo = parent.activeElement;
            
            // Si estás agregando un menú o escribiendo el precio, deja el teclado en paz
            if (activo && (activo.tagName === 'INPUT' || activo.tagName === 'TEXTAREA')) {
                if (activo.placeholder !== "oculto_scanner") {
                    return; 
                }
            }
            
            // Si no estás haciendo nada, la pistola queda activa sola
            var lector = parent.querySelector('input[placeholder="oculto_scanner"]');
            if (lector) {
                lector.focus();
            }
        }
        setInterval(enfocarLector, 500); // Revisa cada medio segundo
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
                html_tickets = ""
                
                for item in st.session_state.pedido_temporal:
                    es_comida = item["categoria"] in ["Desayuno", "Almuerzo", "Cena"]
                    ventas_to_insert.append({
                        "producto": item["producto"],
                        "monto": int(item["monto"]),
                        "categoria": item["categoria"],
                        "tipo": "PAGADO",
                        "estado_impresion": "PENDIENTE" if es_comida else "N/A"
                    })
                    
                    if es_comida:
                        html_tickets += f"""
                        <div style="page-break-after: always; text-align: center; width: 100%; font-family: sans-serif; padding: 0; margin: 0;">
                            <h1 style="font-size: 26px; margin: 0; font-weight: bold; text-transform: uppercase;">{item['producto']}</h1>
                            <p style="font-size: 11px; margin: 2px 0; text-transform: uppercase; color: #333;">({item['categoria']})</p>
                        </div>
                        """

                supabase.table("ventas").insert(ventas_to_insert).execute()
                
                if html_tickets:
                    estilo = """
                    <style>
                        @page { 
                            margin-top: 1.2cm; 
                            margin-bottom: 0cm; 
                            margin-left: 0.1cm; 
                            margin-right: 0.1cm; 
                        } 
                        body { margin: 0; padding: 0; }
                    </style>
                    """
                    components.html(f"{estilo}<script>window.print();</script>{html_tickets}", height=0)
                    st.success("✅ Venta registrada e impresión enviada.")
                    time.sleep(2) 
                else:
                    st.success("✅ Venta registrada correctamente.")

                st.session_state.pedido_temporal = []
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
