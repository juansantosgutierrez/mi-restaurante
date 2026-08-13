import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 🎨 Configuración de pantalla
st.set_page_config(page_title="Métricas Santos", page_icon="📊", layout="wide")

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
        # AQUÍ CAMBIAS TU CONTRASEÑA. AHORA MISMO ES: 12345
        if clave == "12345": 
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("❌ Clave incorrecta.")
    st.stop() # Detiene todo si no hay clave

# ==========================================
# CONFIGURACIÓN DE SUPABASE ⚡
# ==========================================
URL_SUPABASE = "https://luklxueplpxdktreuloa.supabase.co"
KEY_SUPABASE = "sb_publishable_KxAtLO6z0_4SUtbpQDWekQ_mKXZZebX"
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# --- 🕒 FUNCIONES DE FECHA ---
def obtener_hora_chile():
    return datetime.now(ZoneInfo("America/Santiago"))

# --- 📥 DESCARGAR DATOS DE SUPABASE ---
@st.cache_data(ttl=10) # Se actualiza cada 10 segundos para no saturar
def cargar_datos():
    # Descargar ventas
    res_ventas = supabase.table("ventas").select("*").execute()
    df_v = pd.DataFrame(res_ventas.data)
    
    # Descargar gastos
    res_gastos = supabase.table("gastos").select("*").execute()
    df_g = pd.DataFrame(res_gastos.data)
    
    # Convertir fechas a hora chilena (AQUÍ ESTÁ LA CORRECCIÓN utc=True)
    if not df_v.empty:
        df_v['created_at'] = pd.to_datetime(df_v['created_at'], utc=True).dt.tz_convert('America/Santiago')
    if not df_g.empty:
        df_g['created_at'] = pd.to_datetime(df_g['created_at'], utc=True).dt.tz_convert('America/Santiago')
        
    return df_v, df_g

st.title("📊 Panel de Control - Restaurante Santos")
st.write(f"Última actualización: {obtener_hora_chile().strftime('%H:%M:%S hrs')}")

if st.button("🔄 Refrescar Datos Ahora"):
    st.cache_data.clear()
    st.rerun()

df_ventas, df_gastos = cargar_datos()

# ==========================================
# 🎛️ FILTROS DE TIEMPO (Igual que Power BI)
# ==========================================
filtro = st.radio("Selecciona el periodo:", ["Hoy", "Ayer", "Últimos 7 días", "Todo el mes"], horizontal=True)

hoy = obtener_hora_chile().date()

if filtro == "Hoy":
    fecha_inicio = pd.to_datetime(hoy).tz_localize('America/Santiago')
elif filtro == "Ayer":
    fecha_inicio = pd.to_datetime(hoy - timedelta(days=1)).tz_localize('America/Santiago')
elif filtro == "Últimos 7 días":
    fecha_inicio = pd.to_datetime(hoy - timedelta(days=7)).tz_localize('America/Santiago')
else:
    # Primer día del mes actual
    fecha_inicio = pd.to_datetime(hoy.replace(day=1)).tz_localize('America/Santiago')

# Filtrar las tablas según la fecha elegida
if not df_ventas.empty:
    ventas_filtradas = df_ventas[df_ventas['created_at'] >= fecha_inicio]
else:
    ventas_filtradas = pd.DataFrame()

if not df_gastos.empty:
    gastos_filtrados = df_gastos[df_gastos['created_at'] >= fecha_inicio]
else:
    gastos_filtrados = pd.DataFrame()

# ==========================================
# 🧮 CÁLCULOS MATEMÁTICOS (KPIs)
# ==========================================
total_ventas = ventas_filtradas['monto'].sum() if not ventas_filtradas.empty else 0
total_gastos = gastos_filtrados['monto'].sum() if not gastos_filtrados.empty else 0

# Las recargas de caja vecina no son ganancia real del restaurante, las separamos.
if not ventas_filtradas.empty:
    ventas_reales = ventas_filtradas[~ventas_filtradas['categoria'].isin(["CAJA VECINA", "RECARGA"])]['monto'].sum()
    caja_vecina_total = ventas_filtradas[ventas_filtradas['categoria'].isin(["CAJA VECINA", "RECARGA"])]['monto'].sum()
else:
    ventas_reales = 0
    caja_vecina_total = 0

ganancia_neta = ventas_reales - total_gastos

# ==========================================
# 💵 TARJETAS DE RESUMEN (MÉTRICAS)
# ==========================================
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Ventas Restaurante", f"${int(ventas_reales):,}".replace(",", "."))
c2.metric("🏦 Movimientos Caja Vecina", f"${int(caja_vecina_total):,}".replace(",", "."))
c3.metric("📉 Gastos Salientes", f"${int(total_gastos):,}".replace(",", "."))

# Color dinámico para la ganancia
color_ganancia = "normal"
if ganancia_neta > 0: color_ganancia = "normal" # Streamlit pone verde el normal con flecha arriba
elif ganancia_neta < 0: color_ganancia = "inverse" # Rojo

c4.metric("🏆 GANANCIA NETA", f"${int(ganancia_neta):,}".replace(",", "."), delta=int(ganancia_neta), delta_color=color_ganancia)

st.markdown("---")

# ==========================================
# 📈 GRÁFICOS INTERACTIVOS (Tipo Power BI)
# ==========================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("🍕 Ventas por Categoría")
    if not ventas_filtradas.empty:
        # Agrupar por categoría
        ventas_cat = ventas_filtradas[~ventas_filtradas['categoria'].isin(["CAJA VECINA", "RECARGA"])]
        if not ventas_cat.empty:
            df_agrupado = ventas_cat.groupby("categoria")["monto"].sum().reset_index()
            # Gráfico de torta (Pie Chart) usando Plotly
            fig_pie = px.pie(df_agrupado, values='monto', names='categoria', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay ventas de comida en este periodo.")
    else:
        st.info("No hay datos para mostrar.")

with col_graf2:
    st.subheader("🔥 Top 5 Productos Más Vendidos")
    if not ventas_filtradas.empty:
        ventas_prod = ventas_filtradas[~ventas_filtradas['categoria'].isin(["CAJA VECINA", "RECARGA"])]
        if not ventas_prod.empty:
            df_top = ventas_prod.groupby("producto")["monto"].sum().reset_index().sort_values(by="monto", ascending=False).head(5)
            # Gráfico de barras horizontales
            fig_bar = px.bar(df_top, x="monto", y="producto", orientation='h', color="monto", color_continuous_scale="Blues")
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay productos vendidos en este periodo.")
    else:
        st.info("No hay datos para mostrar.")

# ==========================================
# 📋 TABLA DE DETALLES RÁPIDOS
# ==========================================
st.subheader("📝 Últimas 10 ventas del periodo")
if not ventas_filtradas.empty:
    tabla_mostrar = ventas_filtradas[['created_at', 'producto', 'categoria', 'monto']].copy()
    tabla_mostrar['created_at'] = tabla_mostrar['created_at'].dt.strftime('%d/%m/%Y %H:%M')
    tabla_mostrar.columns = ['Fecha/Hora', 'Producto', 'Categoría', 'Monto ($)']
    st.dataframe(tabla_mostrar.sort_values(by="Fecha/Hora", ascending=False).head(10), use_container_width=True)
