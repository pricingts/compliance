-- Crear tabla de perfiles
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL -- e.g., 'cliente', 'proveedor', etc.
);

-- Crear tabla de solicitudes (clientes o proveedores)
CREATE TABLE clients_requests (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER NOT NULL REFERENCES profiles(id),
    company_name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trading TEXT,
    location TEXT,
    language TEXT,
    reminder_frequency TEXT,
    colaborador_nombre TEXT,
    colaborador_cedula TEXT,
    created_by_email TEXT
);


-- Crear tabla de tipos de documentos requeridos por perfil
CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER NOT NULL REFERENCES profiles(id),
    name TEXT NOT NULL,
    description TEXT,
    is_required BOOLEAN DEFAULT TRUE,
    UNIQUE(profile_id, name)
);

-- Crear tabla de documentos cargados por solicitud
CREATE TABLE uploaded_documents (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES clients_requests(id) ON DELETE CASCADE,
    document_type_id INTEGER NOT NULL REFERENCES document_types(id),
    file_name TEXT,
    drive_link TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by TEXT,
    UNIQUE(request_id, document_type_id) -- evita duplicados
);

-- Insertar perfiles base
INSERT INTO profiles (name) VALUES
  ('cliente'),
  ('proveedor'),

-- =============================
-- DOCUMENTOS PARA PERFIL CLIENTE
-- =============================
INSERT INTO document_types (profile_id, name) VALUES
((SELECT id FROM profiles WHERE name = 'cliente'), 'Contrato de responsabilidad clientes'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Compromiso de pago'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Autorización tratamiento de datos personales'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Declaración de origen de fondos y/o bienes'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Formato de vinculación (Circular 0170)'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Formulario de acuerdos de confidencialidad'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Verificación de Acuerdos'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Cámara de Comercio'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'RUT'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Cédula de Representante Legal'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'EEFF - Estado de Resultados'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'EEFF - Flujo de Efectivo'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'EEFF - Cambios en el Patrimonio'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'EEFF - Cambios en la Situación Financiera'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'EEFF - Notas contables'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Certificación EEFF Contador'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Dictamen Revisor Fiscal'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Dictamen Contador Público Externo'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Copia Cédula y Tarjeta Profesional Contador/Revisor'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'RUB actualizado'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Composición accionaria'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Declaración de renta'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Certificación bancaria'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Certificación comercial 1'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Certificación comercial 2'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Registro fotográfico empresa'),
((SELECT id FROM profiles WHERE name = 'cliente'), 'Certificaciones de calidad');

-- =============================
-- DOCUMENTOS PARA PERFIL PROVEEDOR
-- =============================
INSERT INTO document_types (profile_id, name) VALUES
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Formulario de Registro de Proveedores (CUM-REG-002)'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Formulario de acuerdos de seguridad (CUM-REG-003)'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Certificado Cámara de Comercio'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Composición accionaria'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Certificado NIT / RUC / RUS / RUT / TAX ID'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Documento de identificación Representante Legal'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Referencia comercial'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Referencia bancaria'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Certificados de Sistemas de Gestión'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Habilitación Ministerio de Transporte'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Certificado SGSST (ARL)'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Plan de seguridad vial'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Documentos de limpieza y desinfección'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Plan de contingencia'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Póliza de Responsabilidad Civil'),
((SELECT id FROM profiles WHERE name = 'proveedor'), 'Certificación BASC')
