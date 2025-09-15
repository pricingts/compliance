import streamlit as st
import re
from database.crud.clientes import insert_client_request, get_profile_id
from services.sheets_writer import save_request

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def forms():

    tipo_solicitud = st.selectbox(
        "Tipo de solicitud",
        ["cliente", "proveedor"],
        key="tipo_solicitud"
    )

    profile_id = get_profile_id(tipo_solicitud)
    if not profile_id:
        st.error("❌ El perfil seleccionado no existe en la base de datos.")
        return

    comerciales = [
        "Pedro Luis Bruges", "Andrés Consuegra", "Ivan Zuluaga", "Sharon Zuñiga",
        "Johnny Farah", "Felipe Hoyos", "Jorge Sánchez",
        "Irina Paternina", "Stephanie Bruges"
    ]

    # -------- Campos condicionales solicitante --------
    requested_by = None
    requested_by_type = None
    if tipo_solicitud.lower() == "cliente":
        requested_by = st.selectbox("Comercial", comerciales, key="comercial")
        requested_by_type = "comercial"
    elif tipo_solicitud.lower() == "proveedor":
        requested_by = st.text_input("Nombre de quien solicita", key="solicitante_proveedor")
        requested_by_type = "solicitante_proveedor"

    # -------- Campos generales para cliente/proveedor --------
    col1, col2, col3 = st.columns(3)
    with col1:
        company_name = st.text_input("Nombre de la Compañía", key="nombre_compania")
        language = st.selectbox("¿Qué idioma hablan?", ["Español", "Inglés"], key="idioma_compania")
    with col2:
        trading = st.selectbox(
            "Desde qué trading se va a crear",
            ["Colombia", "Mexico", "Panama", "Estados Unidos", "Chile", "Ecuador", "Peru", "Hong Kong"],
            key="trading_creacion"
        )
        email = st.text_input("Correo electrónico", key="correo_compania")
    with col3:
        location = st.text_input("¿Dónde está la compañía?", key="ubicacion_compania")
        reminder_frequency = st.selectbox(
            "Frecuencia de recordatorio",
            ["Una vez por semana", "Dos veces por semana", "Tres veces por semana"],
            key="frecuencia_recordatorio"
        )

    # -------- Botón de guardado (sin st.form) --------
    if st.button("Guardar", key="guardar_general"):
        # Validaciones mínimas
        if not company_name:
            st.error("❌ Debes ingresar el nombre de la compañía.")
            return
        if email and not EMAIL_RE.match(email):
            st.error("❌ El correo electrónico no parece válido.")
            return
        if tipo_solicitud.lower() == "proveedor" and not requested_by:
            st.error("❌ Debes ingresar el nombre de quien solicita (proveedor).")
            return

        # Persistir en DB
        request_id = insert_client_request(
            profile_id=profile_id,
            company_name=company_name,
            email=email or None,
            trading=trading,
            location=location or None,
            language=language,
            reminder_frequency=reminder_frequency,
            requested_by=requested_by,
            requested_by_type=requested_by_type
        )

        # Guardar también en Google Sheets (incluye request_id para trazabilidad)
        save_request({
            "request_id": request_id,
            "profile_id": profile_id,
            "tipo_solicitud": tipo_solicitud,
            "company_name": company_name,
            "email": email,
            "trading": trading,
            "location": location,
            "language": language,
            "reminder_frequency": reminder_frequency,
            "requested_by": requested_by,
            "requested_by_type": requested_by_type
        })

        # Feedback
        st.success(f"✅ Solicitud guardada correctamente")
        # st.write("**Nombre de la Compañía:**", company_name)
        # st.write("**Desde qué trading:**", trading)
        # st.write("**Ubicación:**", location or "—")
        # st.write("**Idioma:**", language)
        # st.write("**Correo electrónico:**", email or "—")
        # st.write("**Frecuencia de Recordatorio:**", reminder_frequency)
        # if requested_by_type == "comercial":
        #     st.write("**Comercial:**", requested_by)
        # elif requested_by_type == "solicitante_proveedor":
        #     st.write("**Solicitante (proveedor):**", requested_by)
        # st.write("**Tipo de solicitud:**", tipo_solicitud)