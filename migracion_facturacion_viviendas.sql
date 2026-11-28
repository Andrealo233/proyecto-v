USE veredal_db;

ALTER TABLE asociados
    ADD COLUMN frecuencia_pago ENUM('Mensual', 'Quincenal') NOT NULL DEFAULT 'Mensual';

CREATE TABLE IF NOT EXISTS viviendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asociado_id INT NOT NULL,
    identificador VARCHAR(120) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_viviendas_asociado
        FOREIGN KEY (asociado_id) REFERENCES asociados(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS configuracion_facturacion (
    id TINYINT PRIMARY KEY,
    tarifa_mensual INT NOT NULL,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO configuracion_facturacion (id, tarifa_mensual)
VALUES (1, 15000);

CREATE TABLE IF NOT EXISTS cargos_recurrentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asociado_id INT NOT NULL,
    descripcion VARCHAR(160) NOT NULL,
    valor INT NOT NULL,
    activo TINYINT NOT NULL DEFAULT 1,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cargos_asociado
        FOREIGN KEY (asociado_id) REFERENCES asociados(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Existing associates intentionally receive no properties, the administrator assigns them.
-- Previous meter and consumption tables/columns remain untouched as historical data.
