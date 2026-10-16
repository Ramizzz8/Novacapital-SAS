-- ============================================================
-- Novacapital SAS · Esquema de la base de datos (MySQL 8 / MariaDB)
-- Solo estructura: los datos de demostración están en seed.sql
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `rol` enum('admin','asesor','cobrador','cliente') NOT NULL DEFAULT 'cliente',
  `activo` tinyint(1) DEFAULT '1',
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `ultima_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `clientes`;
CREATE TABLE `clientes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int DEFAULT NULL,
  `tipo_documento` enum('CC','CE','TI','PP') NOT NULL,
  `numero_documento` varchar(20) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `fecha_nacimiento` date NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `celular` varchar(20) NOT NULL,
  `direccion` varchar(200) DEFAULT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  `departamento` varchar(100) DEFAULT NULL,
  `tipo_cliente` enum('empleado_publico','pensionado') NOT NULL,
  `entidad_empleadora` varchar(200) DEFAULT NULL,
  `salario_mensual` decimal(15,2) DEFAULT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `estado` enum('activo','inactivo','bloqueado') DEFAULT 'activo',
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero_documento` (`numero_documento`),
  KEY `idx_clientes_documento` (`numero_documento`),
  KEY `idx_usuario_id` (`usuario_id`),
  FULLTEXT KEY `idx_fulltext_clientes` (`nombres`,`apellidos`,`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `prestamos`;
CREATE TABLE `prestamos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int NOT NULL,
  `numero_prestamo` varchar(50) NOT NULL,
  `monto_solicitado` decimal(15,2) NOT NULL,
  `monto_aprobado` decimal(15,2) DEFAULT NULL,
  `tasa_interes` decimal(5,2) NOT NULL,
  `plazo_meses` int NOT NULL,
  `cuota_mensual` decimal(15,2) DEFAULT NULL,
  `fecha_solicitud` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_aprobacion` timestamp NULL DEFAULT NULL,
  `fecha_desembolso` timestamp NULL DEFAULT NULL,
  `estado` enum('solicitado','en_analisis','aprobado','rechazado','desembolsado','finalizado') NOT NULL,
  `observaciones` text,
  `banco` varchar(100) DEFAULT NULL,
  `cuenta_bancaria` varchar(50) DEFAULT NULL,
  `usuario_aprobador_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero_prestamo` (`numero_prestamo`),
  KEY `usuario_aprobador_id` (`usuario_aprobador_id`),
  KEY `idx_prestamos_cliente` (`cliente_id`),
  KEY `idx_prestamos_estado` (`estado`),
  FULLTEXT KEY `idx_fulltext_prestamos` (`numero_prestamo`,`observaciones`),
  CONSTRAINT `prestamos_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`),
  CONSTRAINT `prestamos_ibfk_2` FOREIGN KEY (`usuario_aprobador_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `pagos`;
CREATE TABLE `pagos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `prestamo_id` int NOT NULL,
  `numero_cuota` int NOT NULL,
  `fecha_vencimiento` date NOT NULL,
  `fecha_pago` timestamp NULL DEFAULT NULL,
  `valor_cuota` decimal(15,2) NOT NULL,
  `valor_pagado` decimal(15,2) DEFAULT NULL,
  `capital` decimal(15,2) NOT NULL,
  `interes` decimal(15,2) NOT NULL,
  `saldo_pendiente` decimal(15,2) NOT NULL,
  `estado` enum('pendiente','pagado','mora','vencido') DEFAULT 'pendiente',
  `dias_mora` int DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_pagos_prestamo` (`prestamo_id`),
  KEY `idx_pagos_estado` (`estado`),
  KEY `idx_pagos_fecha_vencimiento` (`fecha_vencimiento`),
  CONSTRAINT `pagos_ibfk_1` FOREIGN KEY (`prestamo_id`) REFERENCES `prestamos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `asignaciones_asesores`;
CREATE TABLE `asignaciones_asesores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int NOT NULL,
  `asesor_id` int NOT NULL,
  `fecha_asignacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_desasignacion` timestamp NULL DEFAULT NULL,
  `activa` tinyint(1) DEFAULT '1',
  `notas` text,
  PRIMARY KEY (`id`),
  KEY `idx_cliente` (`cliente_id`),
  KEY `idx_asesor` (`asesor_id`),
  KEY `idx_activa` (`activa`),
  CONSTRAINT `asignaciones_asesores_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `asignaciones_asesores_ibfk_2` FOREIGN KEY (`asesor_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `bitacora`;
CREATE TABLE `bitacora` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `accion` varchar(100) NOT NULL,
  `modulo` varchar(50) DEFAULT NULL,
  `tabla_afectada` varchar(50) DEFAULT NULL,
  `registro_id` int DEFAULT NULL,
  `descripcion` text,
  `ip_address` varchar(45) DEFAULT NULL,
  `fecha` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `bitacora_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `campanas`;
CREATE TABLE `campanas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) NOT NULL,
  `descripcion` text,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  `tasa_especial` decimal(5,2) DEFAULT NULL,
  `monto_minimo` decimal(15,2) DEFAULT NULL,
  `monto_maximo` decimal(15,2) DEFAULT NULL,
  `activa` tinyint(1) DEFAULT '1',
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `configuracion_sistema`;
CREATE TABLE `configuracion_sistema` (
  `id` int NOT NULL AUTO_INCREMENT,
  `clave` varchar(100) NOT NULL,
  `valor` text,
  `tipo` enum('string','number','boolean','json') DEFAULT 'string',
  `descripcion` text,
  `categoria` varchar(50) DEFAULT NULL,
  `fecha_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `clave` (`clave`),
  KEY `idx_clave` (`clave`),
  KEY `idx_categoria` (`categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `documentos`;
CREATE TABLE `documentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int DEFAULT NULL,
  `prestamo_id` int DEFAULT NULL,
  `tipo_documento` enum('cedula','certificado_laboral','nomina','extracto_bancario','certificado_pension','rut','carta_autorizacion','contrato','pagare','carta_instrucciones','otro') NOT NULL,
  `nombre_archivo` varchar(255) NOT NULL,
  `ruta_archivo` varchar(500) NOT NULL,
  `fecha_carga` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `prestamo_id` (`prestamo_id`),
  CONSTRAINT `documentos_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`),
  CONSTRAINT `documentos_ibfk_2` FOREIGN KEY (`prestamo_id`) REFERENCES `prestamos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `notificaciones`;
CREATE TABLE `notificaciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `titulo` varchar(200) NOT NULL,
  `mensaje` text NOT NULL,
  `tipo` enum('info','success','warning','error') DEFAULT 'info',
  `leida` tinyint(1) DEFAULT '0',
  `url_accion` varchar(500) DEFAULT NULL,
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_lectura` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_usuario` (`usuario_id`),
  KEY `idx_leida` (`leida`),
  KEY `idx_fecha` (`fecha_creacion`),
  CONSTRAINT `notificaciones_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `plantillas_documentos`;
CREATE TABLE `plantillas_documentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) NOT NULL,
  `tipo` enum('contrato','pagare','carta','certificado','otro') NOT NULL,
  `contenido_html` text NOT NULL,
  `variables_disponibles` json DEFAULT NULL,
  `activa` tinyint(1) DEFAULT '1',
  `usuario_creador_id` int DEFAULT NULL,
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `ultima_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `usuario_creador_id` (`usuario_creador_id`),
  KEY `idx_tipo` (`tipo`),
  KEY `idx_activa` (`activa`),
  CONSTRAINT `plantillas_documentos_ibfk_1` FOREIGN KEY (`usuario_creador_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tablas que la aplicación también crea al vuelo (CREATE TABLE IF NOT EXISTS)
DROP TABLE IF EXISTS `password_resets`;
CREATE TABLE `password_resets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `token` varchar(64) NOT NULL,
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `expira_en` datetime NOT NULL,
  `usado` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  CONSTRAINT `password_resets_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `documentos_cliente`;
CREATE TABLE `documentos_cliente` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int NOT NULL,
  `tipo` enum('cedula','comprobante_ingresos','desprendible_pago','carta_laboral','otro') NOT NULL DEFAULT 'otro',
  `nombre_original` varchar(255) NOT NULL,
  `nombre_archivo` varchar(255) NOT NULL,
  `fecha_subida` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `documentos_cliente_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- Registra en la bitácora cada préstamo nuevo
DROP TRIGGER IF EXISTS `tr_prestamo_insert`;
DELIMITER ;;
CREATE TRIGGER `tr_prestamo_insert` AFTER INSERT ON `prestamos` FOR EACH ROW
BEGIN
    DECLARE v_usuario INT;
    SELECT MIN(id) INTO v_usuario FROM usuarios WHERE activo = TRUE;
    IF v_usuario IS NOT NULL THEN
        INSERT INTO bitacora (usuario_id, accion, tabla_afectada, registro_id, descripcion)
        VALUES (v_usuario, 'INSERT', 'prestamos', NEW.id, CONCAT('Préstamo creado: ', NEW.numero_prestamo));
    END IF;
END;;
DELIMITER ;

DROP VIEW IF EXISTS `v_cartera_vigente`;
CREATE VIEW `v_cartera_vigente` AS select `p`.`id` AS `id`,`p`.`numero_prestamo` AS `numero_prestamo`,`c`.`nombres` AS `nombres`,`c`.`apellidos` AS `apellidos`,`p`.`monto_aprobado` AS `monto_aprobado`,`p`.`tasa_interes` AS `tasa_interes`,`p`.`plazo_meses` AS `plazo_meses`,`p`.`cuota_mensual` AS `cuota_mensual`,`p`.`fecha_desembolso` AS `fecha_desembolso`,(select sum((`pagos`.`valor_cuota` - `pagos`.`valor_pagado`)) from `pagos` where ((`pagos`.`prestamo_id` = `p`.`id`) and (`pagos`.`estado` <> 'pagado'))) AS `saldo_pendiente`,(select count(0) from `pagos` where ((`pagos`.`prestamo_id` = `p`.`id`) and (`pagos`.`estado` = 'pagado'))) AS `cuotas_pagadas`,(select count(0) from `pagos` where (`pagos`.`prestamo_id` = `p`.`id`)) AS `total_cuotas` from (`prestamos` `p` join `clientes` `c` on((`p`.`cliente_id` = `c`.`id`))) where (`p`.`estado` = 'desembolsado');

DROP VIEW IF EXISTS `v_estadisticas_generales`;
CREATE VIEW `v_estadisticas_generales` AS select (select count(0) from `clientes` where (`clientes`.`estado` = 'activo')) AS `total_clientes_activos`,(select count(0) from `prestamos` where (`prestamos`.`estado` = 'desembolsado')) AS `total_prestamos_activos`,(select coalesce(sum(`prestamos`.`monto_aprobado`),0) from `prestamos` where (`prestamos`.`estado` = 'desembolsado')) AS `monto_total_cartera`,(select coalesce(sum(`pagos`.`valor_pagado`),0) from `pagos` where (`pagos`.`estado` = 'pagado')) AS `monto_total_cobrado`,(select coalesce(sum((`pagos`.`valor_cuota` - `pagos`.`valor_pagado`)),0) from `pagos` where (`pagos`.`estado` in ('mora','vencido'))) AS `monto_total_mora`,(select count(0) from `prestamos` where (`prestamos`.`estado` = 'solicitado')) AS `solicitudes_pendientes`,(select count(0) from `prestamos` where (cast(`prestamos`.`fecha_solicitud` as date) = curdate())) AS `solicitudes_hoy`;
