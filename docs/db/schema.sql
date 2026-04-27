CREATE TABLE `usuarios` (
   `id_usuario` bigint unsigned NOT NULL AUTO_INCREMENT,
   `nome` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
   `email` varchar(190) COLLATE utf8mb4_unicode_ci NOT NULL,
   `senha_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
   `plano_id` tinyint unsigned NOT NULL,
   `papel` enum('ADMIN','USUARIO') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'USUARIO',
   `ativo` tinyint(1) NOT NULL DEFAULT '1',
   `email_verificado_em` datetime DEFAULT NULL,
   `ultimo_login_em` datetime DEFAULT NULL,
   `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `atualizado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   `email_verificacao_token_hash` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `email_verificacao_expira_em` datetime DEFAULT NULL,
   `email_verificacao_enviado_em` datetime DEFAULT NULL,
   PRIMARY KEY (`id_usuario`),
   UNIQUE KEY `uk_usuarios_email` (`email`),
   UNIQUE KEY `ux_usuarios_email_verif_hash` (`email_verificacao_token_hash`),
   KEY `fk_usuarios_plano` (`plano_id`),
   CONSTRAINT `fk_usuarios_plano` FOREIGN KEY (`plano_id`) REFERENCES `planos` (`id_plano`) ON DELETE RESTRICT ON UPDATE CASCADE
 ) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

 CREATE TABLE `sessoes` (
   `id_sessoes` bigint unsigned NOT NULL AUTO_INCREMENT,
   `usuario_id` bigint unsigned NOT NULL,
   `token_refresh_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
   `agente_usuario` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `ip_origem` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `expira_em` datetime NOT NULL,
   `revogado_em` datetime DEFAULT NULL,
   `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (`id_sessoes`),
   KEY `idx_sessoes_usuario_id` (`usuario_id`),
   CONSTRAINT `fk_sessoes_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id_usuario`) ON DELETE RESTRICT ON UPDATE CASCADE
 ) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

 CREATE TABLE `avaliacoes` (
   `id_avaliacoes` bigint unsigned NOT NULL AUTO_INCREMENT,
   `usuario_id` bigint unsigned DEFAULT NULL,
   `ip_origem` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `condominio_id` bigint unsigned NOT NULL,
   `modelo_id` bigint unsigned NOT NULL,
   `area_util_m2` decimal(10,2) NOT NULL,
   `valor_condominio_rs` decimal(14,2) DEFAULT NULL,
   `quartos` int NOT NULL,
   `vagas` int NOT NULL,
   `preco_minimo_rs` decimal(14,2) DEFAULT NULL,
   `preco_sugerido_rs` decimal(14,2) DEFAULT NULL,
   `preco_maximo_rs` decimal(14,2) DEFAULT NULL,
   `preco_m2_minimo` decimal(14,6) DEFAULT NULL,
   `preco_m2_sugerido` decimal(14,6) DEFAULT NULL,
   `preco_m2_maximo` decimal(14,6) DEFAULT NULL,
   `preco_total_minimo_rs` decimal(14,2) DEFAULT NULL,
   `preco_total_sugerido_rs` decimal(14,2) DEFAULT NULL,
   `preco_total_maximo_rs` decimal(14,2) DEFAULT NULL,
   `status` enum('SUCESSO','ERRO') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'SUCESSO',
   `mensagem_erro` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `tempo_processamento_ms` int DEFAULT NULL,
   `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `guest_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `is_favorita` tinyint(1) NOT NULL DEFAULT '0',
   `nome_predio_input` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   PRIMARY KEY (`id_avaliacoes`),
   KEY `idx_avaliacoes_usuario_id` (`usuario_id`),
   KEY `idx_avaliacoes_condominio_id` (`condominio_id`),
   KEY `idx_avaliacoes_modelo_id` (`modelo_id`),
   KEY `idx_avaliacoes_criado_em` (`criado_em`),
   KEY `ix_avaliacoes_usuario_dia` (`usuario_id`,`criado_em`),
   KEY `ix_avaliacoes_guest_dia` (`guest_id`,`criado_em`),
   KEY `ix_avaliacoes_favoritas` (`usuario_id`,`is_favorita`),
   CONSTRAINT `fk_avaliacoes_condominio` FOREIGN KEY (`condominio_id`) REFERENCES `condominios` (`id_condominio`) ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `fk_avaliacoes_modelo` FOREIGN KEY (`modelo_id`) REFERENCES `modelos_ml` (`id_modelos_ml`) ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `fk_avaliacoes_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id_usuario`) ON DELETE RESTRICT ON UPDATE CASCADE
 ) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

 CREATE TABLE `condominios` (
   `id_condominio` bigint unsigned NOT NULL AUTO_INCREMENT,
   `nome` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
   `chave_normalizada` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
   `cidade` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
   `uf` char(2) COLLATE utf8mb4_unicode_ci NOT NULL,
   `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `atualizado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   PRIMARY KEY (`id_condominio`),
   UNIQUE KEY `uk_condominios_chave_normalizada` (`chave_normalizada`)
 ) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

 CREATE TABLE `caracteristicas_localizacao` (
   `id_caracteristicas_localizacao` bigint unsigned NOT NULL AUTO_INCREMENT,
   `condominio_id` bigint unsigned NOT NULL,
   `latitude` decimal(10,7) NOT NULL,
   `longitude` decimal(10,7) NOT NULL,
   `nome_metro` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `distancia_metro_km` decimal(8,5) DEFAULT NULL,
   `mercados_500m` int DEFAULT NULL,
   `escolas_1000m` int DEFAULT NULL,
   `parques_800m` int DEFAULT NULL,
   `fonte_dado` enum('google','manual','importacao') COLLATE utf8mb4_unicode_ci NOT NULL,
   `capturado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `expira_em` datetime NOT NULL,
   PRIMARY KEY (`id_caracteristicas_localizacao`),
   KEY `idx_caraclocal_condominio_id` (`condominio_id`),
   CONSTRAINT `fk_caraclocal_condominio` FOREIGN KEY (`condominio_id`) REFERENCES `condominios` (`id_condominio`) ON DELETE RESTRICT ON UPDATE CASCADE
 ) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

 CREATE TABLE `planos` (
   `id_plano` tinyint unsigned NOT NULL,
   `nome` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
   `limite_previsoes_dia` int NOT NULL,
   `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (`id_plano`),
   UNIQUE KEY `uk_planos_nome` (`nome`)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

 CREATE TABLE `modelos_ml` (
   `id_modelos_ml` bigint unsigned NOT NULL AUTO_INCREMENT,
   `nome_modelo` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
   `versao` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
   `caminho_arquivo` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
   `ativo` tinyint(1) NOT NULL DEFAULT '1',
   `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (`id_modelos_ml`),
   UNIQUE KEY `uk_modelos_nome_versao` (`nome_modelo`,`versao`)
 ) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

 CREATE TABLE `avaliacoes_backup_20260425` (
   `id_avaliacoes` bigint unsigned NOT NULL DEFAULT '0',
   `usuario_id` bigint unsigned DEFAULT NULL,
   `ip_origem` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `condominio_id` bigint unsigned NOT NULL,
   `modelo_id` bigint unsigned NOT NULL,
   `area_util_m2` decimal(10,2) NOT NULL,
   `valor_condominio_rs` decimal(14,2) DEFAULT NULL,
   `quartos` int NOT NULL,
   `vagas` int NOT NULL,
   `preco_minimo_rs` decimal(14,2) DEFAULT NULL,
   `preco_sugerido_rs` decimal(14,2) DEFAULT NULL,
   `preco_maximo_rs` decimal(14,2) DEFAULT NULL,
   `preco_m2_minimo` decimal(14,6) DEFAULT NULL,
   `preco_m2_sugerido` decimal(14,6) DEFAULT NULL,
   `preco_m2_maximo` decimal(14,6) DEFAULT NULL,
   `preco_total_minimo_rs` decimal(14,2) DEFAULT NULL,
   `preco_total_sugerido_rs` decimal(14,2) DEFAULT NULL,
   `preco_total_maximo_rs` decimal(14,2) DEFAULT NULL,
   `status` enum('SUCESSO','ERRO') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'SUCESSO',
   `mensagem_erro` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `tempo_processamento_ms` int DEFAULT NULL,
   `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `guest_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `is_favorita` tinyint(1) NOT NULL DEFAULT '0',
   `nome_predio_input` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci