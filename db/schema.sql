-- Schema of the pizza ordering system (MySQL 8 / MariaDB). Structure only; example data is in seed.sql.
CREATE DATABASE IF NOT EXISTS pizza_ordering_system;
USE pizza_ordering_system;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `customer`;
CREATE TABLE `customer` (
  `customer_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `last_name` varchar(100) DEFAULT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `gender` enum('Male','Female','Other') DEFAULT 'Other',
  `birthdate` date DEFAULT NULL,
  `phone_number` varchar(15) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `pizzas_ordered` int DEFAULT '0',
  PRIMARY KEY (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `customerorder`;
CREATE TABLE `customerorder` (
  `order_id` int NOT NULL AUTO_INCREMENT,
  `customer_id` int NOT NULL,
  `order_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `confirmation_number` varchar(100) NOT NULL,
  `status` varchar(50) DEFAULT NULL,
  `delivery_time_estimation` timestamp NULL DEFAULT NULL,
  `delivery_method` enum('Delivery','Pickup') NOT NULL DEFAULT 'Delivery',
  `total_price` decimal(10,2) DEFAULT '0.00',
  PRIMARY KEY (`order_id`),
  KEY `customer_id` (`customer_id`),
  CONSTRAINT `customer_order_fk_customer` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `deliveryassignment`;
CREATE TABLE `deliveryassignment` (
  `assignment_id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `delivery_person_id` int NOT NULL,
  `assigned_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`assignment_id`),
  KEY `order_id` (`order_id`),
  KEY `delivery_person_id` (`delivery_person_id`),
  CONSTRAINT `deliveryassignment_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `customerorder` (`order_id`),
  CONSTRAINT `deliveryassignment_ibfk_2` FOREIGN KEY (`delivery_person_id`) REFERENCES `deliverypersonnel` (`delivery_person_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `deliverypersonnel`;
CREATE TABLE `deliverypersonnel` (
  `delivery_person_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `assigned_postal_code` varchar(10) DEFAULT NULL,
  `availability` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`delivery_person_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `dessert`;
CREATE TABLE `dessert` (
  `dessert_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`dessert_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `discountcode`;
CREATE TABLE `discountcode` (
  `code` varchar(20) NOT NULL,
  `expiration_date` date NOT NULL,
  `is_used` tinyint(1) DEFAULT '0',
  `discount_percentage` decimal(5,2) DEFAULT NULL,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `drink`;
CREATE TABLE `drink` (
  `drink_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`drink_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `earningreport`;
CREATE TABLE `earningreport` (
  `report_id` int NOT NULL AUTO_INCREMENT,
  `month` date NOT NULL,
  `total_earnings` decimal(10,2) NOT NULL,
  PRIMARY KEY (`report_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `ingredient`;
CREATE TABLE `ingredient` (
  `ingredient_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `is_vegetarian` tinyint(1) DEFAULT '0',
  `is_vegan` tinyint(1) DEFAULT '0',
  `cost` decimal(10,2) NOT NULL,
  PRIMARY KEY (`ingredient_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `menu`;
CREATE TABLE `menu` (
  `menu_id` int NOT NULL AUTO_INCREMENT,
  `menu_name` varchar(100) NOT NULL,
  `type` enum('Pizza','Drink','Dessert') DEFAULT NULL,
  PRIMARY KEY (`menu_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `menu_item`;
CREATE TABLE `menu_item` (
  `menu_item_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `type` enum('Pizza','Drink','Dessert') NOT NULL,
  `price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`menu_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `order_item`;
CREATE TABLE `order_item` (
  `order_item_id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `menu_item_id` int NOT NULL,
  `quantity` int NOT NULL,
  `item_type` enum('Pizza','Drink','Dessert') NOT NULL,
  PRIMARY KEY (`order_item_id`),
  KEY `order_id` (`order_id`),
  KEY `menu_item_id` (`menu_item_id`),
  CONSTRAINT `order_item_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `customerorder` (`order_id`) ON DELETE CASCADE,
  CONSTRAINT `order_item_ibfk_2` FOREIGN KEY (`menu_item_id`) REFERENCES `menu_item` (`menu_item_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `pizza`;
CREATE TABLE `pizza` (
  `pizza_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `size` enum('Small','Medium','Large') NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `is_vegetarian` tinyint(1) DEFAULT '0',
  `is_vegan` tinyint(1) DEFAULT '0',
  `profit_margin` decimal(5,2) NOT NULL,
  `vat` decimal(5,2) NOT NULL,
  `base_price` decimal(10,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`pizza_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `pizza_ingredient`;
CREATE TABLE `pizza_ingredient` (
  `pizza_id` int NOT NULL,
  `ingredient_id` int NOT NULL,
  `quantity` int DEFAULT '1',
  `menu_item_id` int DEFAULT NULL,
  PRIMARY KEY (`pizza_id`,`ingredient_id`),
  KEY `ingredient_id` (`ingredient_id`),
  CONSTRAINT `fk_pizza_ingredient_ingredient` FOREIGN KEY (`ingredient_id`) REFERENCES `ingredient` (`ingredient_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pizza_ingredient_pizza` FOREIGN KEY (`pizza_id`) REFERENCES `pizza` (`pizza_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `postalcodearea`;
CREATE TABLE `postalcodearea` (
  `postal_code` varchar(10) NOT NULL,
  `city` varchar(100) NOT NULL,
  PRIMARY KEY (`postal_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `staff`;
CREATE TABLE `staff` (
  `staff_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `role` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`staff_id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
