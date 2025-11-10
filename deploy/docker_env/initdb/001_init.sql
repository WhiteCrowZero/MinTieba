-- 001_init.sql
-- 使用 docker-entrypoint-initdb.d 机制，在首次初始化数据目录时执行

CREATE DATABASE IF NOT EXISTS `mintieba`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `mintieba`;

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';

-- 示例表，用于健康检查或联通验证
CREATE TABLE IF NOT EXISTS healthcheck (
    id INT PRIMARY KEY AUTO_INCREMENT,
    note VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
