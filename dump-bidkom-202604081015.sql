/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.7.2-MariaDB, for Win64 (AMD64)
--
-- Host: 192.168.137.50    Database: bidkom
-- ------------------------------------------------------
-- Server version	11.8.5-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `debt`
--

DROP TABLE IF EXISTS `debt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `debt` (
  `debt_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `debt_name` varchar(100) NOT NULL,
  `principal` decimal(10,0) NOT NULL,
  `interest_rate` decimal(10,0) NOT NULL,
  `interest_type` enum('flat','reducing') NOT NULL,
  `total_installments` int(11) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `status` enum('active','paid') NOT NULL,
  `interest_rate_basis` varchar(16) NOT NULL DEFAULT 'year',
  `payment_period` varchar(16) NOT NULL DEFAULT 'month',
  PRIMARY KEY (`debt_id`),
  KEY `debt_user_fk` (`user_id`),
  CONSTRAINT `debt_user_fk` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `debt`
--

LOCK TABLES `debt` WRITE;
/*!40000 ALTER TABLE `debt` DISABLE KEYS */;
INSERT INTO `debt` VALUES
(8,6,'ค่าเครื่องสำอาง',12500,0,'reducing',12,'2026-03-28','2026-06-20','active','year','week'),
(11,1,'BT14',5000,0,'reducing',10,'2026-03-28','2026-06-06','active','month','week'),
(12,7,'BT15',2000,0,'reducing',8,'2026-04-09','2026-06-04','active','year','week');
/*!40000 ALTER TABLE `debt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `installment`
--

DROP TABLE IF EXISTS `installment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `installment` (
  `installment_id` int(11) NOT NULL AUTO_INCREMENT,
  `debt_id` int(11) NOT NULL,
  `installment_no` int(11) NOT NULL,
  `due_date` date NOT NULL,
  `principal_amount` decimal(10,2) NOT NULL,
  `interest_amount` decimal(10,2) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `remaining_balance` decimal(10,2) NOT NULL,
  `installment_status` enum('paid','unpaid') NOT NULL,
  PRIMARY KEY (`installment_id`),
  KEY `ix_installments_debt_id` (`debt_id`),
  CONSTRAINT `installment_debt_fk` FOREIGN KEY (`debt_id`) REFERENCES `debt` (`debt_id`)
) ENGINE=InnoDB AUTO_INCREMENT=406 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `installment`
--

LOCK TABLES `installment` WRITE;
/*!40000 ALTER TABLE `installment` DISABLE KEYS */;
INSERT INTO `installment` VALUES
(325,8,1,'2026-04-04',1041.67,0.00,1041.67,11458.33,'unpaid'),
(326,8,2,'2026-04-11',1041.67,0.00,1041.67,10416.66,'unpaid'),
(327,8,3,'2026-04-18',1041.67,0.00,1041.67,9374.99,'unpaid'),
(328,8,4,'2026-04-25',1041.67,0.00,1041.67,8333.32,'unpaid'),
(329,8,5,'2026-05-02',1041.67,0.00,1041.67,7291.65,'unpaid'),
(330,8,6,'2026-05-09',1041.67,0.00,1041.67,6249.98,'unpaid'),
(331,8,7,'2026-05-16',1041.67,0.00,1041.67,5208.31,'unpaid'),
(332,8,8,'2026-05-23',1041.67,0.00,1041.67,4166.64,'unpaid'),
(333,8,9,'2026-05-30',1041.67,0.00,1041.67,3124.97,'unpaid'),
(334,8,10,'2026-06-06',1041.67,0.00,1041.67,2083.30,'unpaid'),
(335,8,11,'2026-06-13',1041.67,0.00,1041.67,1041.63,'unpaid'),
(336,8,12,'2026-06-20',1041.63,0.00,1041.63,0.00,'unpaid'),
(380,11,1,'2026-04-04',500.00,0.00,500.00,4500.00,'unpaid'),
(381,11,2,'2026-04-11',500.00,0.00,500.00,4000.00,'unpaid'),
(382,11,3,'2026-04-18',500.00,0.00,500.00,3500.00,'unpaid'),
(383,11,4,'2026-04-25',500.00,0.00,500.00,3000.00,'unpaid'),
(384,11,5,'2026-05-02',500.00,0.00,500.00,2500.00,'unpaid'),
(385,11,6,'2026-05-09',500.00,0.00,500.00,2000.00,'unpaid'),
(386,11,7,'2026-05-16',500.00,0.00,500.00,1500.00,'unpaid'),
(387,11,8,'2026-05-23',500.00,0.00,500.00,1000.00,'unpaid'),
(388,11,9,'2026-05-30',500.00,0.00,500.00,500.00,'unpaid'),
(389,11,10,'2026-06-06',500.00,0.00,500.00,0.00,'unpaid'),
(398,12,1,'2026-04-16',250.00,0.00,250.00,1750.00,'unpaid'),
(399,12,2,'2026-04-23',250.00,0.00,250.00,1500.00,'unpaid'),
(400,12,3,'2026-04-30',250.00,0.00,250.00,1250.00,'unpaid'),
(401,12,4,'2026-05-07',250.00,0.00,250.00,1000.00,'unpaid'),
(402,12,5,'2026-05-14',250.00,0.00,250.00,750.00,'unpaid'),
(403,12,6,'2026-05-21',250.00,0.00,250.00,500.00,'unpaid'),
(404,12,7,'2026-05-28',250.00,0.00,250.00,250.00,'unpaid'),
(405,12,8,'2026-06-04',250.00,0.00,250.00,0.00,'unpaid');
/*!40000 ALTER TABLE `installment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `debt_total` decimal(65,0) NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES
(1,'aa','aa',500),
(2,'string','string',0),
(3,'string','string',100),
(4,'asdasdasd','asdasdasd',0),
(5,'v','v',0),
(6,'gu','gugu',45000),
(7,'Emrek','1234',5000);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'bidkom'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-04-08 10:15:51
