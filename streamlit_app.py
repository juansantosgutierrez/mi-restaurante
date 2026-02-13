import streamlit as st

st.title("🍴 Mi Restaurante Control")
st.write("¡Hola! Esta es la base de tu nueva app.")

categoria = st.selectbox("Selecciona Categoría", ["Almuerzo", "Bebida", "Gasto"])
monto = st.number_input("Monto", min_value=0)

if st.button("Registrar Venta"):
    st.success(f"Registrado: {categoria} por {monto}")
