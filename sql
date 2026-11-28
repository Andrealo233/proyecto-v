CREATE DATABASE IF NOT EXISTS veredal_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE veredal_db;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    documento VARCHAR(30) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    clave VARCHAR(255) NOT NULL
);

CREATE TABLE asociados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    documento VARCHAR(30) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    vereda VARCHAR(80),
    estrato INT DEFAULT 1,
    tarifa VARCHAR(30) DEFAULT 'Residencial',
    medidor VARCHAR(30),
    ultimo_pago DATE,
    estado ENUM('Activo', 'Suspendido') DEFAULT 'Activo'
);

CREATE TABLE lecturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    servicio VARCHAR(80) NOT NULL,
    vereda VARCHAR(80),
    lectura_anterior INT NOT NULL,
    lectura_actual INT NOT NULL,
    consumo INT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE facturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(30) UNIQUE NOT NULL,
    asociado VARCHAR(120) NOT NULL,
    documento VARCHAR(30),
    valor DECIMAL(10,2) NOT NULL,
    estado ENUM('Pagada', 'Pendiente', 'Vencida') DEFAULT 'Pendiente',
    fecha DATE,
    periodo VARCHAR(20),
    m3 INT,
    fecha_pago DATE,
    metodo VARCHAR(30)
);

CREATE TABLE pqrs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    asunto VARCHAR(200) NOT NULL,
    sector VARCHAR(80),
    prioridad VARCHAR(20) DEFAULT 'Media',
    estado VARCHAR(30) DEFAULT 'En proceso',
    fecha DATE
);

CREATE TABLE publicaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(160) NOT NULL,
    contenido TEXT NOT NULL,
    activo TINYINT NOT NULL DEFAULT 1,
    creado_por VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_publicaciones_inicio (activo, actualizado_en)
);

CREATE TABLE instalaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asociado VARCHAR(120) NOT NULL,
    vereda VARCHAR(80) NOT NULL,
    estado ENUM('Instalado', 'En proceso', 'Cancelado') DEFAULT 'En proceso',
    fecha DATE
);

CREATE TABLE actividad_reciente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(30) NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    detalle VARCHAR(255) NOT NULL,
    estado VARCHAR(30) NOT NULL,
    icono VARCHAR(10) NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE telemetria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bocatoma_caudal_ls DECIMAL(10,2),
    tanque_principal_nivel INT,
    tanque_alto_nivel INT,
    ph DECIMAL(10,2),
    cloro_residual DECIMAL(10,2),
    turbidez DECIMAL(10,2),
    presion_red DECIMAL(10,2),
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumo_diario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    consumo_m3 INT NOT NULL,
    caudal_ls DECIMAL(10,2)
);

INSERT INTO asociados (nombre, documento, telefono, estado) VALUES
('Juan Pérez', '1.234.567.890', '310 456 7890', 'Activo'),
('María López', '1.098.765.432', '320 111 2233', 'Activo');

CREATE TABLE servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    descripcion VARCHAR(255)
);

INSERT INTO servicios (nombre, tipo, valor, descripcion) VALUES
('Derecho de Matrícula Residencial', 'Conexión', 150000, 'Instalación nueva vivienda'),
('Acueducto Agrícola / Riego', 'Servicio', 85000, 'Riego por goteo y aspersión'),
('Medidor Ultrasónico Inteligente', 'Equipo', 220000, 'Lectura remota sin contacto'),
('Reconexión de Servicio', 'Mantenimiento', 45000, 'Restablecimiento tras suspensión'),
('Cambio de Medidor Mecánico', 'Mantenimiento', 95000, 'Actualización a digital'),
('Toma Domiciliaria Estándar', 'Conexión', 120000, 'Conexión 1/2 pulgada');

INSERT INTO facturas (numero, asociado, documento, valor, estado, fecha, periodo, m3, fecha_pago) VALUES
('FV-2025-001', 'Juan Pérez', '1.234.567.890', 55000, 'Pagada', '2025-07-10', 'Julio 2025', 28, '2025-07-10'),
('FV-2025-002', 'María López', '1.098.765.432', 48000, 'Pendiente', '2025-07-12', 'Julio 2025', 32, NULL);

INSERT INTO instalaciones (asociado, vereda, estado, fecha) VALUES
('Juan Pérez', 'El Roble', 'Instalado', '2025-06-01'),
('María López', 'La Loma', 'Instalado', '2025-06-05'),
('Carlos Méndez', 'El Roble', 'En proceso', '2025-07-01'),
('Ana Torres', 'San José', 'Cancelado', '2025-06-20');

INSERT INTO actividad_reciente (tipo, titulo, detalle, estado, icono, fecha) VALUES
('success', 'Pago recibido', 'Carlos Méndez - $58.500 - Hace 15 min', 'Completado', '💰', '2025-07-15 08:30:00'),
('info', 'Nueva lectura registrada', 'Jorge Herrera - 45 m³ - Sector San José', 'Registrado', '💧', '2025-07-14 14:20:00'),
('warning', 'Corte programado', 'Sector La Loma - Mañana 8:00 AM - Mantenimiento', 'Programado', '⚡', '2025-07-15 07:00:00'),
('danger', 'PQRS Urgente', 'Fuga en tubería madre El Roble - Sin resolver', 'En proceso', '🚨', '2025-07-14 10:00:00');

INSERT INTO telemetria (bocatoma_caudal_ls, tanque_principal_nivel, tanque_alto_nivel, ph, cloro_residual, turbidez, presion_red, ultima_actualizacion) VALUES
(42.5, 78, 65, 7.2, 0.8, 1.2, 3.8, '2025-07-15 14:30:00');

INSERT INTO consumo_diario (fecha, consumo_m3, caudal_ls) VALUES
('2025-07-09', 1250, 41.2),
('2025-07-10', 1320, 43.1),
('2025-07-11', 1180, 39.8),
('2025-07-12', 1410, 45.3),
('2025-07-13', 1290, 42.7),
('2025-07-14', 1350, 44.0),
('2025-07-15', 1380, 45.8);

