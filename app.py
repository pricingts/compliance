import streamlit as st
from services.authentication import check_authentication
from collections import defaultdict

st.set_page_config(page_title="Compliance Platform", layout="wide")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image("images/logo_trading.png", width=800)

check_authentication()

user = st.user.name

with st.sidebar:
    page = st.radio("Go to", ["Home",  "Solicitud de Creación", "Registro de Proveedores/ Clientes", "Progreso"])

if page == "Solicitud de Creación":
    import views.request as payment 
    payment.show()

elif page == "Registro de Proveedores/ Clientes":
    import views.upload_documents as pre
    pre.show()

elif page == "Progreso":
    import views.visualization as nt
    nt.show()