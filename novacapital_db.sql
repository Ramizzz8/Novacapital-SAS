-- MySQL dump 10.13  Distrib 8.0.45, for Linux (x86_64)
--
-- Host: localhost    Database: novacapital_db
-- ------------------------------------------------------
-- Server version	8.0.45-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `asignaciones_asesores`
--

DROP TABLE IF EXISTS `asignaciones_asesores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asignaciones_asesores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cliente_id` int NOT NULL,
  `asesor_id` int NOT NULL,
  `fecha_asignacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_desasignacion` timestamp NULL DEFAULT NULL,
  `activa` tinyint(1) DEFAULT '1',
  `notas` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `idx_cliente` (`cliente_id`),
  KEY `idx_asesor` (`asesor_id`),
  KEY `idx_activa` (`activa`),
  CONSTRAINT `asignaciones_asesores_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `asignaciones_asesores_ibfk_2` FOREIGN KEY (`asesor_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asignaciones_asesores`
--

LOCK TABLES `asignaciones_asesores` WRITE;
/*!40000 ALTER TABLE `asignaciones_asesores` DISABLE KEYS */;
/*!40000 ALTER TABLE `asignaciones_asesores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bitacora`
--

DROP TABLE IF EXISTS `bitacora`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bitacora` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `accion` varchar(100) NOT NULL,
  `tabla_afectada` varchar(50) DEFAULT NULL,
  `registro_id` int DEFAULT NULL,
  `descripcion` text,
  `ip_address` varchar(45) DEFAULT NULL,
  `fecha` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `bitacora_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bitacora`
--

LOCK TABLES `bitacora` WRITE;
/*!40000 ALTER TABLE `bitacora` DISABLE KEYS */;
/*!40000 ALTER TABLE `bitacora` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campanas`
--

DROP TABLE IF EXISTS `campanas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campanas`
--

LOCK TABLES `campanas` WRITE;
/*!40000 ALTER TABLE `campanas` DISABLE KEYS */;
/*!40000 ALTER TABLE `campanas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clientes`
--

DROP TABLE IF EXISTS `clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clientes`
--

LOCK TABLES `clientes` WRITE;
/*!40000 ALTER TABLE `clientes` DISABLE KEYS */;
INSERT INTO `clientes` VALUES (1,14,'CE','z3021431h','Daniel','Calve','2000-04-29','danielcalve@gmail.com','12345678','3003505858','calle falsa 123','bogota','bogota','pensionado','colpensiones',2500000.00,'2026-03-02 10:06:13','activo');
/*!40000 ALTER TABLE `clientes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `configuracion_sistema`
--

DROP TABLE IF EXISTS `configuracion_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuracion_sistema` (
  `id` int NOT NULL AUTO_INCREMENT,
  `clave` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor` text COLLATE utf8mb4_unicode_ci,
  `tipo` enum('string','number','boolean','json') COLLATE utf8mb4_unicode_ci DEFAULT 'string',
  `descripcion` text COLLATE utf8mb4_unicode_ci,
  `categoria` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fecha_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `clave` (`clave`),
  KEY `idx_clave` (`clave`),
  KEY `idx_categoria` (`categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `configuracion_sistema`
--

LOCK TABLES `configuracion_sistema` WRITE;
/*!40000 ALTER TABLE `configuracion_sistema` DISABLE KEYS */;
INSERT INTO `configuracion_sistema` VALUES (1,'tasa_interes_base','1.9','number','Tasa de interés mensual base','prestamos','2026-02-19 11:53:12'),(2,'monto_minimo','1000000','number','Monto mínimo de préstamo','prestamos','2026-02-19 11:53:12'),(3,'monto_maximo','50000000','number','Monto máximo de préstamo','prestamos','2026-02-19 11:53:12'),(4,'plazo_minimo','6','number','Plazo mínimo en meses','prestamos','2026-02-19 11:53:12'),(5,'plazo_maximo','72','number','Plazo máximo en meses','prestamos','2026-02-19 11:53:12'),(6,'tasa_mora','0.05','number','Tasa de mora diaria','pagos','2026-02-19 11:53:12'),(7,'email_notificaciones','true','boolean','Enviar notificaciones por email','notificaciones','2026-02-19 11:53:12'),(8,'dias_gracia_mora','5','number','Días de gracia antes de marcar mora','pagos','2026-02-19 11:53:12');
/*!40000 ALTER TABLE `configuracion_sistema` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `documentos`
--

DROP TABLE IF EXISTS `documentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `documentos`
--

LOCK TABLES `documentos` WRITE;
/*!40000 ALTER TABLE `documentos` DISABLE KEYS */;
/*!40000 ALTER TABLE `documentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notificaciones`
--

DROP TABLE IF EXISTS `notificaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notificaciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `titulo` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mensaje` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo` enum('info','success','warning','error') COLLATE utf8mb4_unicode_ci DEFAULT 'info',
  `leida` tinyint(1) DEFAULT '0',
  `url_accion` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_lectura` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_usuario` (`usuario_id`),
  KEY `idx_leida` (`leida`),
  KEY `idx_fecha` (`fecha_creacion`),
  CONSTRAINT `notificaciones_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notificaciones`
--

LOCK TABLES `notificaciones` WRITE;
/*!40000 ALTER TABLE `notificaciones` DISABLE KEYS */;
/*!40000 ALTER TABLE `notificaciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pagos`
--

DROP TABLE IF EXISTS `pagos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pagos`
--

LOCK TABLES `pagos` WRITE;
/*!40000 ALTER TABLE `pagos` DISABLE KEYS */;
/*!40000 ALTER TABLE `pagos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `plantillas_documentos`
--

DROP TABLE IF EXISTS `plantillas_documentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `plantillas_documentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo` enum('contrato','pagare','carta','certificado','otro') COLLATE utf8mb4_unicode_ci NOT NULL,
  `contenido_html` text COLLATE utf8mb4_unicode_ci NOT NULL,
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `plantillas_documentos`
--

LOCK TABLES `plantillas_documentos` WRITE;
/*!40000 ALTER TABLE `plantillas_documentos` DISABLE KEYS */;
/*!40000 ALTER TABLE `plantillas_documentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prestamos`
--

DROP TABLE IF EXISTS `prestamos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
  `usuario_aprobador_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero_prestamo` (`numero_prestamo`),
  KEY `usuario_aprobador_id` (`usuario_aprobador_id`),
  KEY `idx_prestamos_cliente` (`cliente_id`),
  KEY `idx_prestamos_estado` (`estado`),
  FULLTEXT KEY `idx_fulltext_prestamos` (`numero_prestamo`,`observaciones`),
  CONSTRAINT `prestamos_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`),
  CONSTRAINT `prestamos_ibfk_2` FOREIGN KEY (`usuario_aprobador_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prestamos`
--

LOCK TABLES `prestamos` WRITE;
/*!40000 ALTER TABLE `prestamos` DISABLE KEYS */;
/*!40000 ALTER TABLE `prestamos` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tr_prestamo_insert` AFTER INSERT ON `prestamos` FOR EACH ROW BEGIN
    INSERT INTO bitacora (usuario_id, accion, modulo, tabla_afectada, registro_id, descripcion)
    VALUES (COALESCE(NEW.usuario_aprobador_id, 1), 'INSERT', 'prestamos', 'prestamos', NEW.id, 
            CONCAT('Préstamo creado: ', NEW.numero_prestamo));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (7,'Asesor Comercial','asesor@novacapital.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeawY5GyYqNn5rF5Hy','asesor',1,'2026-02-24 09:02:09','2026-02-24 09:02:09'),(9,'Administrador Sistema','admin@novacapital.com','$2b$12$GEDiT4/9J/eOL7c3mZC2yumCe1BFKKLLX/8fHBRuwc1Djs95UVUl6','admin',1,'2026-02-24 09:09:34','2026-02-24 09:09:34'),(10,'Asesor Juan Pérez','juan.perez@novacapital.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeawY5GyYqNn5rF5Hy','asesor',1,'2026-02-24 09:26:58','2026-02-24 09:26:58'),(11,'Asesora María García','maria.garcia@novacapital.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeawY5GyYqNn5rF5Hy','asesor',1,'2026-02-24 09:26:58','2026-02-24 09:26:58'),(14,'Daniel','danielcalve@gmail.com','$2b$12$UcRHhYPsOTIJYk1QRyoj2uIYeSNhLuKQVAW5PVNk540rzzY1i8JsK','cliente',1,'2026-03-02 10:06:13','2026-03-02 10:06:13');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `v_cartera_vigente`
--

DROP TABLE IF EXISTS `v_cartera_vigente`;
/*!50001 DROP VIEW IF EXISTS `v_cartera_vigente`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_cartera_vigente` AS SELECT 
 1 AS `id`,
 1 AS `numero_prestamo`,
 1 AS `nombres`,
 1 AS `apellidos`,
 1 AS `monto_aprobado`,
 1 AS `tasa_interes`,
 1 AS `plazo_meses`,
 1 AS `cuota_mensual`,
 1 AS `fecha_desembolso`,
 1 AS `saldo_pendiente`,
 1 AS `cuotas_pagadas`,
 1 AS `total_cuotas`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_estadisticas_generales`
--

DROP TABLE IF EXISTS `v_estadisticas_generales`;
/*!50001 DROP VIEW IF EXISTS `v_estadisticas_generales`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_estadisticas_generales` AS SELECT 
 1 AS `total_clientes_activos`,
 1 AS `total_prestamos_activos`,
 1 AS `monto_total_cartera`,
 1 AS `monto_total_cobrado`,
 1 AS `monto_total_mora`,
 1 AS `solicitudes_pendientes`,
 1 AS `solicitudes_hoy`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `v_cartera_vigente`
--

/*!50001 DROP VIEW IF EXISTS `v_cartera_vigente`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_cartera_vigente` AS select `p`.`id` AS `id`,`p`.`numero_prestamo` AS `numero_prestamo`,`c`.`nombres` AS `nombres`,`c`.`apellidos` AS `apellidos`,`p`.`monto_aprobado` AS `monto_aprobado`,`p`.`tasa_interes` AS `tasa_interes`,`p`.`plazo_meses` AS `plazo_meses`,`p`.`cuota_mensual` AS `cuota_mensual`,`p`.`fecha_desembolso` AS `fecha_desembolso`,(select sum((`pagos`.`valor_cuota` - `pagos`.`valor_pagado`)) from `pagos` where ((`pagos`.`prestamo_id` = `p`.`id`) and (`pagos`.`estado` <> 'pagado'))) AS `saldo_pendiente`,(select count(0) from `pagos` where ((`pagos`.`prestamo_id` = `p`.`id`) and (`pagos`.`estado` = 'pagado'))) AS `cuotas_pagadas`,(select count(0) from `pagos` where (`pagos`.`prestamo_id` = `p`.`id`)) AS `total_cuotas` from (`prestamos` `p` join `clientes` `c` on((`p`.`cliente_id` = `c`.`id`))) where (`p`.`estado` = 'desembolsado') */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_estadisticas_generales`
--

/*!50001 DROP VIEW IF EXISTS `v_estadisticas_generales`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_estadisticas_generales` AS select (select count(0) from `clientes` where (`clientes`.`estado` = 'activo')) AS `total_clientes_activos`,(select count(0) from `prestamos` where (`prestamos`.`estado` = 'desembolsado')) AS `total_prestamos_activos`,(select coalesce(sum(`prestamos`.`monto_aprobado`),0) from `prestamos` where (`prestamos`.`estado` = 'desembolsado')) AS `monto_total_cartera`,(select coalesce(sum(`pagos`.`valor_pagado`),0) from `pagos` where (`pagos`.`estado` = 'pagado')) AS `monto_total_cobrado`,(select coalesce(sum((`pagos`.`valor_cuota` - `pagos`.`valor_pagado`)),0) from `pagos` where (`pagos`.`estado` in ('mora','vencido'))) AS `monto_total_mora`,(select count(0) from `prestamos` where (`prestamos`.`estado` = 'solicitado')) AS `solicitudes_pendientes`,(select count(0) from `prestamos` where (cast(`prestamos`.`fecha_solicitud` as date) = curdate())) AS `solicitudes_hoy` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-05 14:17:37
