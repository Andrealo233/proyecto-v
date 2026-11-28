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
    frecuencia_pago ENUM('Mensual', 'Quincenal') NOT NULL DEFAULT 'Mensual',
    ultimo_pago DATE,
    estado ENUM('Activo', 'Suspendido') DEFAULT 'Activo'
);

CREATE TABLE viviendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asociado_id INT NOT NULL,
    identificador VARCHAR(120) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_viviendas_asociado FOREIGN KEY (asociado_id) REFERENCES asociados(id) ON DELETE CASCADE
);

CREATE TABLE configuracion_facturacion (
    id TINYINT PRIMARY KEY,
    tarifa_mensual INT NOT NULL,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO configuracion_facturacion (id, tarifa_mensual) VALUES (1, 15000);

CREATE TABLE cargos_recurrentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asociado_id INT NOT NULL,
    descripcion VARCHAR(160) NOT NULL,
    valor INT NOT NULL,
    activo TINYINT NOT NULL DEFAULT 1,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cargos_asociado FOREIGN KEY (asociado_id) REFERENCES asociados(id) ON DELETE CASCADE
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

INSERT INTO asociados (nombre, documento, telefono, estado) VALUES
('Juan Pérez', '1.234.567.890', '310 456 7890', 'Activo'),
('María López', '1.098.765.432', '320 111 2233', 'Activo');

INSERT INTO instalaciones (asociado, vereda, estado, fecha) VALUES
('Juan Pérez', 'El Roble', 'Instalado', '2025-06-01'),
('María López', 'La Loma', 'Instalado', '2025-06-05'),
('Carlos Méndez', 'El Roble', 'En proceso', '2025-07-01'),
('Ana Torres', 'San José', 'Cancelado', '2025-06-20');

INSERT INTO actividad_reciente (tipo, titulo, detalle, estado, icono, fecha) VALUES
('success', 'Pago recibido', 'Carlos Méndez - $15.000 - Hace 15 min', 'Completado', '💰', '2025-07-15 08:30:00'),
('info', 'Nivel de tanque actualizado', 'Tanque principal - Estado operativo', 'Registrado', '💧', '2025-07-14 14:20:00'),
('warning', 'Corte programado', 'Sector La Loma - Mañana 8:00 AM - Mantenimiento', 'Programado', '⚡', '2025-07-15 07:00:00'),
('danger', 'PQRS Urgente', 'Fuga en tubería madre El Roble - Sin resolver', 'En proceso', '🚨', '2025-07-14 10:00:00');

INSERT INTO telemetria (bocatoma_caudal_ls, tanque_principal_nivel, tanque_alto_nivel, ph, cloro_residual, turbidez, presion_red, ultima_actualizacion) VALUES
(42.5, 78, 65, 7.2, 0.8, 1.2, 3.8, '2025-07-15 14:30:00');

