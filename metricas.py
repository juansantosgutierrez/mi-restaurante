import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 🎨 Configuración de pantalla
st.set_page_config(page_title="Métricas Santos", page_icon="📊", layout="wide")

# Custom CSS para estilo minimalista
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    .stSelectbox label {
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 SISTEMA DE SEGURIDAD (PRIVACIDAD)
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso Restringido")
    st.write("Panel de administración exclusivo.")
    clave = st.text_input("Ingresa la clave de administrador:", type="password")
    if st.button("Entrar", type="primary"):
        if clave == "12345": 
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("❌ Clave incorrecta.")
    st.stop()

# ==========================================
# CONFIGURACIÓN DE SUPABASE ⚡
# ==========================================
URL_SUPABASE = "https://luklxueplpxdktreuloa.supabase.co"
KEY_SUPABASE = "sb_publishable_KxAtLO6z0_4SUtbpQDWekQ_mKXZZebX"
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

def obtener_hora_chile():
    return datetime.now(ZoneInfo("America/Santiago"))

# --- 📥 DESCARGAR DATOS DE SUPABASE ---
@st.cache_data(ttl=5)
def cargar_datos():
    res_ventas = supabase.table("ventas").select("*").execute()
    df_v = pd.DataFrame(res_ventas.data)
    
    res_gastos = supabase.table("gastos").select("*").execute()
    df_g = pd.DataFrame(res_gastos.data)
    
    try:
        res_debo = supabase.table("debo").select("*").execute()
        df_d = pd.DataFrame(res_debo.data)
    except:
        df_d = pd.DataFrame()
    
    if not df_v.empty:
        df_v['created_at'] = pd.to_datetime(df_v['created_at'], utc=True).dt.tz_convert('America/Santiago')
        df_v['fecha_str'] = df_v['created_at'].dt.strftime('%d-%m-%Y')
        df_v['categoria_upper'] = df_v['categoria'].fillna('').astype(str).str.strip().str.upper()

    if not df_g.empty:
        df_g['created_at'] = pd.to_datetime(df_g['created_at'], utc=True).dt.tz_convert('America/Santiago')
        df_g['fecha_str'] = df_g['created_at'].dt.strftime('%d-%m-%Y')

    if not df_d.empty:
        df_d['created_at'] = pd.to_datetime(df_d['created_at'], utc=True).dt.tz_convert('America/Santiago')
        df_d['fecha_str'] = df_d['created_at'].dt.strftime('%d-%m-%Y')

    return df_v, df_g, df_d

st.title("📊 Panel de Control - Restaurante Santos")
st.caption(f"🕒 Última actualización: {obtener_hora_chile().strftime('%d-%m-%Y %H:%M:%S hrs')}")

if st.button("🔄 Refrescar Datos Ahora"):
    st.cache_data.clear()
    st.rerun()

df_ventas, df_gastos, df_debo = cargar_datos()

# ==========================================
# 📅 SELECTOR DE FECHAS EN MENÚ DESPLEGABLE
# ==========================================
fechas_lista = []
if not df_ventas.empty and 'fecha_str' in df_ventas.columns:
    fechas_lista.extend(df_ventas['fecha_str'].unique().tolist())

hoy_str = obtener_hora_chile().strftime('%d-%m-%Y')
if hoy_str not in fechas_lista:
    fechas_lista.append(hoy_str)

fechas_ordenadas = sorted(list(set(fechas_lista)), key=lambda x: datetime.strptime(x, '%d-%m-%Y'), reverse=True)

opciones_desplegable = ["Hoy (" + hoy_str + ")", "Todos los tiempos", "Últimos 7 días", "Todo el mes"] + fechas_ordenadas

opcion_seleccionada = st.selectbox("📅 Selecciona el periodo o un día específico:", opciones_desplegable)

if "Hoy" in opcion_seleccionada:
    ventas_filtradas = df_ventas[df_ventas['fecha_str'] == hoy_str] if not df_ventas.empty else pd.DataFrame()
    gastos_filtrados = df_gastos[df_gastos['fecha_str'] == hoy_str] if not df_gastos.empty else pd.DataFrame()
    debo_filtrado = df_debo[df_debo['fecha_str'] == hoy_str] if not df_debo.empty else pd.DataFrame()
elif opcion_seleccionada == "Todos los tiempos":
    ventas_filtradas = df_ventas
    gastos_filtrados = df_gastos
    debo_filtrado = df_debo
elif opcion_seleccionada == "Últimos 7 días":
    hace_7 = (obtener_hora_chile() - timedelta(days=7)).date()
    ventas_filtradas = df_ventas[df_ventas['created_at'].dt.date >= hace_7] if not df_ventas.empty else pd.DataFrame()
    gastos_filtrados = df_gastos[df_gastos['created_at'].dt.date >= hace_7] if not df_gastos.empty else pd.DataFrame()
    debo_filtrado = df_debo[df_debo['created_at'].dt.date >= hace_7] if not df_debo.empty else pd.DataFrame()
elif opcion_seleccionada == "Todo el mes":
    primer_dia_mes = obtener_hora_chile().date().replace(day=1)
    ventas_filtradas = df_ventas[df_ventas['created_at'].dt.date >= primer_dia_mes] if not df_ventas.empty else pd.DataFrame()
    gastos_filtrados = df_gastos[df_gastos['created_at'].dt.date >= primer_dia_mes] if not df_gastos.empty else pd.DataFrame()
    debo_filtrado = df_debo[df_debo['created_at'].dt.date >= primer_dia_mes] if not df_debo.empty else pd.DataFrame()
else:
    fecha_elegida = opcion_seleccionada
    ventas_filtradas = df_ventas[df_ventas['fecha_str'] == fecha_elegida] if not df_ventas.empty else pd.DataFrame()
    gastos_filtrados = df_gastos[df_gastos['fecha_str'] == fecha_elegida] if not df_gastos.empty else pd.DataFrame()
    debo_filtrado = df_debo[df_debo['fecha_str'] == fecha_elegida] if not df_debo.empty else pd.DataFrame()

# ==========================================
# 🧮 CÁLCULOS Y SEPARACIÓN DE CATEGORÍAS
# ==========================================
if not ventas_filtradas.empty:
    desayuno_total = ventas_filtradas[ventas_filtradas['categoria_upper'] == "DESAYUNO"]['monto'].sum()
    almuerzo_total = ventas_filtradas[ventas_filtradas['categoria_upper'] == "ALMUERZO"]['monto'].sum()
    cena_total = ventas_filtradas[ventas_filtradas['categoria_upper'] == "CENA"]['monto'].sum()
    
    bebestible_total = ventas_filtradas[ventas_filtradas['categoria_upper'] == "BEBESTIBLE"]['monto'].sum()
    chela_total = ventas_filtradas[ventas_filtradas['categoria_upper'] == "CHELA"]['monto'].sum()
    tienda_otros_total = ventas_filtradas[ventas_filtradas['categoria_upper'].isin(["TIENDA", "OTROS"])]['monto'].sum()
    caja_vecina_total = ventas_filtradas[ventas_filtradas['categoria_upper'].isin(["CAJA VECINA", "RECARGA"])]['monto'].sum()
    
    ventas_comida_total = desayuno_total + almuerzo_total + cena_total
    ventas_otras_cat_total = bebestible_total + chela_total + tienda_otros_total
    ventas_restaurante_total = ventas_comida_total + ventas_otras_cat_total
else:
    desayuno_total = almuerzo_total = cena_total = bebestible_total = chela_total = tienda_otros_total = caja_vecina_total = ventas_comida_total = ventas_otras_cat_total = ventas_restaurante_total = 0

total_gastos = gastos_filtrados['monto'].sum() if not gastos_filtrados.empty else 0
total_vueltos_pendientes = debo_filtrado['monto_devolver'].fillna(0).sum() if not debo_filtrado.empty and 'monto_devolver' in debo_filtrado.columns else 0

ganancia_neta = ventas_restaurante_total - total_gastos

# ==========================================
# 🧱 TARJETAS MINIMALISTAS (CUADROS BORDADOS)
# ==========================================

# 1. BLOQUE COMIDA
with st.container(border=True):
    st.markdown("#### 🍔 Ventas de Comida")
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    col_c1.metric("🍳 Desayunos", f"${int(desayuno_total):,}".replace(",", "."))
    col_c2.metric("🍲 Almuerzos", f"${int(almuerzo_total):,}".replace(",", "."))
    col_c3.metric("🌙 Cenas", f"${int(cena_total):,}".replace(",", "."))
    col_c4.metric("🔥 TOTAL COMIDA", f"${int(ventas_comida_total):,}".replace(",", "."))

# 2. BLOQUE OTRAS CATEGORÍAS
with st.container(border=True):
    st.markdown("#### 🥤 Otras Categorías (Bebidas, Chelas, Tienda)")
    col_o1, col_o2, col_o3, col_o4 = st.columns(4)
    col_o1.metric("🥤 Bebestibles", f"${int(bebestible_total):,}".replace(",", "."))
    col_o2.metric("🍺 Chelas", f"${int(chela_total):,}".replace(",", "."))
    col_o3.metric("🏪 Tienda / Otros", f"${int(tienda_otros_total):,}".replace(",", "."))
    col_o4.metric("🛍️ TOTAL OTRAS CAT.", f"${int(ventas_otras_cat_total):,}".replace(",", "."))

# 3. BALANCE GENERAL DE GANANCIAS
with st.container(border=True):
    st.markdown("#### 🏆 Balance General y Ganancia Neta")
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("💰 Ventas Totales Restaurante", f"${int(ventas_restaurante_total):,}".replace(",", "."))
    col_r2.metric("📉 Gastos Registrados", f"${int(total_gastos):,}".replace(",", "."))
    col_r3.metric("🏆 GANANCIA NETA REAL", f"${int(ganancia_neta):,}".replace(",", "."))

# 4. INFORMACIÓN DE CAJA Y RETENCIONES (APARTE DE LA GANANCIA)
with st.container(border=True):
    st.markdown("#### 🏦 Movimientos de Caja y Vueltos (Aparte de la Ganancia)")
    col_i1, col_i2 = st.columns(2)
    col_i1.metric("🏦 Movimientos Caja Vecina / Recargas", f"${int(caja_vecina_total):,}".replace(",", "."), help="Dinero procesado por servicios de caja vecina.")
    col_i2.metric("🤝 Vueltos Pendientes (Debería sobrar en caja)", f"${int(total_vueltos_pendientes):,}".replace(",", "."), help="Dinero retenido en caja perteneciente a clientes por vuelto pendiente.")

st.markdown("---")

# ==========================================
# 📈 GRÁFICOS SEPARADOS (COMIDA VS OTROS)
# ==========================================
st.subheader("📊 Distribución de Ventas")
col_g1, col_g2 = st.columns(2)

with col_g1:
    with st.container(border=True):
        st.markdown("##### 🍕 Porcentaje por Comida")
        if not ventas_filtradas.empty:
            df_comida = ventas_filtradas[ventas_filtradas['categoria_upper'].isin(["DESAYUNO", "ALMUERZO", "CENA"])]
            if not df_comida.empty:
                agrupado_comida = df_comida.groupby("categoria")["monto"].sum().reset_index()
                fig_pie_comida = px.pie(agrupado_comida, values='monto', names='categoria', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie_comida.update_layout(margin=dict(t=20, b=20, l=10, r=10))
                st.plotly_chart(fig_pie_comida, use_container_width=True)
            else:
                st.info("Sin ventas de comida en este periodo.")
        else:
            st.info("Sin datos.")

with col_g2:
    with st.container(border=True):
        st.markdown("##### 🥤 Porcentaje por Otras Categorías")
        if not ventas_filtradas.empty:
            df_otros = ventas_filtradas[ventas_filtradas['categoria_upper'].isin(["BEBESTIBLE", "CHELA", "TIENDA", "OTROS"])]
            if not df_otros.empty:
                agrupado_otros = df_otros.groupby("categoria")["monto"].sum().reset_index()
                fig_pie_otros = px.pie(agrupado_otros, values='monto', names='categoria', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
                fig_pie_otros.update_layout(margin=dict(t=20, b=20, l=10, r=10))
                st.plotly_chart(fig_pie_otros, use_container_width=True)
            else:
                st.info("Sin ventas de otros productos en este periodo.")
        else:
            st.info("Sin datos.")

# ==========================================
# 🔥 RANKINGS TOP MÁS VENDIDOS
# ==========================================
st.subheader("🔥 Lo Más Vendido")
col_r_top1, col_r_top2 = st.columns(2)

with col_r_top1:
    with st.container(border=True):
        st.markdown("##### 🍳 Top Comidas Más Vendidas")
        if not ventas_filtradas.empty:
            df_top_comida = ventas_filtradas[ventas_filtradas['categoria_upper'].isin(["DESAYUNO", "ALMUERZO", "CENA"])]
            if not df_top_comida.empty:
                df_rank_comida = df_top_comida.groupby("producto")["monto"].sum().reset_index().sort_values(by="monto", ascending=False).head(5)
                fig_bar_comida = px.bar(df_rank_comida, x="monto", y="producto", orientation='h', color="monto", color_continuous_scale="Oranges")
                fig_bar_comida.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=20, b=20, l=10, r=10))
                st.plotly_chart(fig_bar_comida, use_container_width=True)
            else:
                st.info("Sin ventas de comida.")
        else:
            st.info("Sin datos.")

with col_r_top2:
    with st.container(border=True):
        st.markdown("##### 🍺 Top Otros Productos Más Vendidos")
        if not ventas_filtradas.empty:
            df_top_otros = ventas_filtradas[ventas_filtradas['categoria_upper'].isin(["BEBESTIBLE", "CHELA", "TIENDA", "OTROS"])]
            if not df_top_otros.empty:
                df_rank_otros = df_top_otros.groupby("producto")["monto"].sum().reset_index().sort_values(by="monto", ascending=False).head(5)
                fig_bar_otros = px.bar(df_rank_otros, x="monto", y="producto", orientation='h', color="monto", color_continuous_scale="Blues")
                fig_bar_otros.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=20, b=20, l=10, r=10))
                st.plotly_chart(fig_bar_otros, use_container_width=True)
            else:
                st.info("Sin ventas de otros productos.")
        else:
            st.info("Sin datos.")

# ==========================================
# 📋 TABLAS DE DETALLES (DEBO)
# ==========================================
st.markdown("---")
with st.container(border=True):
    st.subheader("📝 Detalle de Registros Pendientes (Debo)")
    if not debo_filtrado.empty:
        tabla_debo = debo_filtrado[['created_at', 'nombre', 'monto', 'monto_devolver', 'descripcion']].copy()
        tabla_debo['created_at'] = tabla_debo['created_at'].dt.strftime('%d-%m-%Y %H:%M')
        tabla_debo.columns = ['Fecha/Hora', 'Cliente', 'Monto Recibido ($)', 'Debo Entregar ($)', 'Descripción']
        st.dataframe(tabla_debo.sort_values(by="Fecha/Hora", ascending=False), use_container_width=True)
    else:
        st.info("No hay registros de DEBO en este periodo.")
