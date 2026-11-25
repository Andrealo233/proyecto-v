CREATE DATABASE IF NOT EXISTS veredal_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE veredal_db;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    documento VARCHAR(30) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    clave VARCHAR(100) NOT NULL
);

CREATE TABLE asociados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    documento VARCHAR(30) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    estado ENUM('Activo', 'Suspendido') DEFAULT 'Activo'
);

CREATE TABLE lecturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    servicio VARCHAR(80) NOT NULL,
    lectura_anterior INT NOT NULL,
    lectura_actual INT NOT NULL,
    consumo INT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE facturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(30) UNIQUE NOT NULL,
    asociado VARCHAR(120) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    estado ENUM('Pagada', 'Pendiente', 'Vencida') DEFAULT 'Pendiente'
);

CREATE TABLE pqrs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    asunto VARCHAR(200) NOT NULL,
    estado VARCHAR(30) DEFAULT 'En proceso'
);

INSERT INTO asociados (nombre, documento, telefono, estado) VALUES
('Juan Pérez', '1.234.567.890', '310 456 7890', 'Activo'),
('María López', '1.098.765.432', '320 111 2233', 'Activo');

INSERT INTO facturas (numero, asociado, valor, estado) VALUES
('FV-2025-001', 'Juan Pérez', 55000, 'Pagada'),
('FV-2025-002', 'María López', 48000, 'Pendiente');

