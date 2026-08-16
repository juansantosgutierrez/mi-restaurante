import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 🎨 Configuración de pantalla
st.set_page_config(page_title="Admin Santos", layout="wide")

# --- 🕒 FUNCIONES DE HORA ---
def obtener_hora_chile():
    return datetime.now(ZoneInfo("America/Santiago"))

# CONEXIÓN SUPABASE
@st.cache_resource
def init_connection():
    URL_SUPABASE = "https://luklxueplpxdktreuloa.supabase.co"
    KEY_SUPABASE = "sb_publishable_KxAtLO6z0_4SUtbpQDWekQ_mKXZZebX"
    return create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = init_connection()

st.title("📊 Panel de Administración - Restaurante Santos")

# --- FILTRO DE FECHA ---
fecha_seleccionada = st.date_input("📅 Selecciona la fecha a revisar", obtener_hora_chile().date())
fecha_inicio = f"{fecha_seleccionada}T00:00:00"
fecha_fin = f"{fecha_seleccionada}T23:59:59"

# --- OBTENER DATOS DE SUPABASE ---
@st.cache_data(ttl=5)
def cargar_datos(inicio, fin):
    # Ventas
    res_ventas = supabase.table("ventas").select("*").gte("created_at", inicio).lte("created_at", fin).execute()
    df_ventas = pd.DataFrame(res_ventas.data) if res_ventas.data else pd.DataFrame(columns=["id", "producto", "monto", "categoria", "created_at"])
    
    # Gastos
    res_gastos = supabase.table("gastos").select("*").gte("created_at", inicio).lte("created_at", fin).execute()
    df_gastos = pd.DataFrame(res_gastos.data) if res_gastos.data else pd.DataFrame(columns=["id", "monto", "descripcion", "created_at"])
    
    # Debo
    res_debo = supabase.table("debo").select("*").gte("created_at", inicio).lte("created_at", fin).execute()
    df_debo = pd.DataFrame(res_debo.data) if res_debo.data else pd.DataFrame(columns=["id", "nombre", "monto_devolver", "descripcion", "created_at"])
    
    return df_ventas, df_gastos, df_debo

df_ventas, df_gastos, df_debo = cargar_datos(fecha_inicio, fecha_fin)

# --- PROCESAMIENTO DE CATEGORÍAS ---
if not df_ventas.empty:
    # Estandarizar categorías
    df_ventas['categoria'] = df_ventas['categoria'].str.upper().fillna("OTROS")
    
    # Agrupar Tienda, Caja Vecina y Recargas en "TIENDA"
    tienda_keywords = ["TIENDA", "CAJA VECINA", "RECARGAS"]
    df_ventas['grupo'] = df_ventas['categoria'].apply(
        lambda x: "TIENDA" if any(k in x for k in tienda_keywords) else (
                  "OTROS" if x not in ["DESAYUNO", "ALMUERZO", "CENA"] else x)
    )
    
    total_ingresos = df_ventas['monto'].sum()
else:
    total_ingresos = 0

total_gastos = df_gastos['monto'].sum() if not df_gastos.empty else 0
total_neto = total_ingresos - total_gastos

# --- MÉTRICAS PRINCIPALES ---
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("💰 INGRESOS TOTALES", f"${int(total_ingresos):,}".replace(",", "."))
c2.metric("💸 GASTOS TOTALES", f"${int(total_gastos):,}".replace(",", "."))
c3.metric("🏆 TOTAL NETO (Caja Final)", f"${int(total_neto):,}".replace(",", "."))
st.divider()

# --- DETALLE DE VENTAS Y GRÁFICOS ---
st.header("📈 Desglose de Ventas por Categoría")

if not df_ventas.empty:
    grupos = ["DESAYUNO", "ALMUERZO", "CENA", "TIENDA", "OTROS"]
    
    for grupo in grupos:
        df_grupo = df_ventas[df_ventas['grupo'] == grupo]
        
        if not df_grupo.empty:
            st.subheader(f"🍽️ {grupo.capitalize()}")
            
            # Totales del grupo
            dinero_grupo = df_grupo['monto'].sum()
            platos_vendidos = len(df_grupo)
            
            st.markdown(f"**Total vendido en {grupo.capitalize()}:** ${int(dinero_grupo):,} | **Cantidad de ventas:** {platos_vendidos}".replace(",", "."))
            
            # Preparar datos para el gráfico (Contar cuántas veces se vendió cada producto)
            resumen_productos = df_grupo.groupby('producto').size().reset_index(name='Cantidad')
            resumen_productos = resumen_productos.sort_values(by='Cantidad', ascending=False)
            
            # Gráfico de barras
            st.bar_chart(resumen_productos.set_index('producto'), y='Cantidad', height=300)
else:
    st.info("No hay ventas registradas para esta fecha.")

st.divider()

# --- SECCIÓN DE GASTOS DETALLADOS ---
st.header("📉 Detalle de Gastos")
if not df_gastos.empty:
    st.error(f"**Total gastado hoy:** ${int(total_gastos):,}".replace(",", "."))
    
    # Crear una tabla visualmente agradable para los gastos
    for idx, row in df_gastos.iterrows():
        try:
            hora = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')).astimezone(ZoneInfo("America/Santiago")).strftime("%H:%M")
        except:
            hora = "--:--"
            
        c1, c2, c3 = st.columns([1, 4, 2])
        c1.write(f"🕒 {hora}")
        c2.write(f"📝 {row['descripcion']}")
        c3.write(f"**${int(row['monto']):,}**".replace(",", "."))
        st.markdown("---")
else:
    st.success("No hay gastos registrados en esta fecha.")

st.divider()

# --- SECCIÓN DE DEBO ---
st.header("🤝 Registro de DEBO (Vueltos pendientes)")
if not df_debo.empty:
    for idx, row in df_debo.iterrows():
        c1, c2 = st.columns([4, 2])
        with c1:
            st.markdown(f"**👤 {row['nombre']}** - {row.get('descripcion', 'Vuelto')}")
        with c2:
            st.warning(f"Debes: **${int(row['monto_devolver']):,}**".replace(",", "."))
        st.markdown("---")
else:
    st.info("No hay deudas pendientes registradas hoy.")

# Botón para actualizar la página
if st.button("🔄 Actualizar Datos", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
