-- MySQL dump 10.13  Distrib 5.7.17, for osx10.12 (x86_64)
--
-- Host: localhost    Database: devmep
-- ------------------------------------------------------
-- Server version	5.7.17

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts_account`
--

DROP TABLE IF EXISTS `accounts_account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_account` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_account`
--

LOCK TABLES `accounts_account` WRITE;
/*!40000 ALTER TABLE `accounts_account` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_account` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_account_persons`
--

DROP TABLE IF EXISTS `accounts_account_persons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_account_persons` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `account_id` int(11) NOT NULL,
  `person_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_account_persons_account_id_person_id_263644a0_uniq` (`account_id`,`person_id`),
  KEY `accounts_account_persons_person_id_a9a49baf_fk_people_person_id` (`person_id`),
  CONSTRAINT `accounts_account_per_account_id_fe47fc2e_fk_accounts_` FOREIGN KEY (`account_id`) REFERENCES `accounts_account` (`id`),
  CONSTRAINT `accounts_account_persons_person_id_a9a49baf_fk_people_person_id` FOREIGN KEY (`person_id`) REFERENCES `people_person` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_account_persons`
--

LOCK TABLES `accounts_account_persons` WRITE;
/*!40000 ALTER TABLE `accounts_account_persons` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_account_persons` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_accountaddress`
--

DROP TABLE IF EXISTS `accounts_accountaddress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_accountaddress` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `account_id` int(11) NOT NULL,
  `address_id` int(11) NOT NULL,
  `care_of_person_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_accountaddr_account_id_14f5ac4d_fk_accounts_` (`account_id`),
  KEY `accounts_accountaddr_address_id_4cb75401_fk_accounts_` (`address_id`),
  KEY `accounts_accountaddr_care_of_person_id_f027cfc5_fk_people_pe` (`care_of_person_id`),
  CONSTRAINT `accounts_accountaddr_account_id_14f5ac4d_fk_accounts_` FOREIGN KEY (`account_id`) REFERENCES `accounts_account` (`id`),
  CONSTRAINT `accounts_accountaddr_address_id_4cb75401_fk_accounts_` FOREIGN KEY (`address_id`) REFERENCES `accounts_address` (`id`),
  CONSTRAINT `accounts_accountaddr_care_of_person_id_f027cfc5_fk_people_pe` FOREIGN KEY (`care_of_person_id`) REFERENCES `people_person` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_accountaddress`
--

LOCK TABLES `accounts_accountaddress` WRITE;
/*!40000 ALTER TABLE `accounts_accountaddress` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_accountaddress` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_address`
--

DROP TABLE IF EXISTS `accounts_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_address` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `address_line_1` varchar(255) NOT NULL,
  `address_line_2` varchar(255) NOT NULL,
  `city_town` varchar(255) NOT NULL,
  `postal_code` varchar(25) NOT NULL,
  `latitude` decimal(8,5) DEFAULT NULL,
  `longitude` decimal(8,5) DEFAULT NULL,
  `country_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_address_country_id_7a9a1174_fk_people_country_id` (`country_id`),
  CONSTRAINT `accounts_address_country_id_7a9a1174_fk_people_country_id` FOREIGN KEY (`country_id`) REFERENCES `people_country` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_address`
--

LOCK TABLES `accounts_address` WRITE;
/*!40000 ALTER TABLE `accounts_address` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_address` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_borrow`
--

DROP TABLE IF EXISTS `accounts_borrow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_borrow` (
  `event_ptr_id` int(11) NOT NULL,
  `purchase_id_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`event_ptr_id`),
  KEY `accounts_borrow_purchase_id_id_7a39d50c_fk_accounts_` (`purchase_id_id`),
  CONSTRAINT `accounts_borrow_event_ptr_id_0843af63_fk_accounts_event_id` FOREIGN KEY (`event_ptr_id`) REFERENCES `accounts_event` (`id`),
  CONSTRAINT `accounts_borrow_purchase_id_id_7a39d50c_fk_accounts_` FOREIGN KEY (`purchase_id_id`) REFERENCES `accounts_purchase` (`event_ptr_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_borrow`
--

LOCK TABLES `accounts_borrow` WRITE;
/*!40000 ALTER TABLE `accounts_borrow` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_borrow` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_event`
--

DROP TABLE IF EXISTS `accounts_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_event` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `account_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_event_account_id_52fea54a_fk_accounts_account_id` (`account_id`),
  CONSTRAINT `accounts_event_account_id_52fea54a_fk_accounts_account_id` FOREIGN KEY (`account_id`) REFERENCES `accounts_account` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_event`
--

LOCK TABLES `accounts_event` WRITE;
/*!40000 ALTER TABLE `accounts_event` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_event` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_purchase`
--

DROP TABLE IF EXISTS `accounts_purchase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_purchase` (
  `event_ptr_id` int(11) NOT NULL,
  `price` decimal(8,2) NOT NULL,
  `currency` varchar(3) NOT NULL,
  `item_id` int(11) NOT NULL,
  PRIMARY KEY (`event_ptr_id`),
  KEY `accounts_purchase_item_id_8cc0491a_fk_books_item_id` (`item_id`),
  CONSTRAINT `accounts_purchase_event_ptr_id_cdfcb178_fk_accounts_event_id` FOREIGN KEY (`event_ptr_id`) REFERENCES `accounts_event` (`id`),
  CONSTRAINT `accounts_purchase_item_id_8cc0491a_fk_books_item_id` FOREIGN KEY (`item_id`) REFERENCES `books_item` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_purchase`
--

LOCK TABLES `accounts_purchase` WRITE;
/*!40000 ALTER TABLE `accounts_purchase` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_purchase` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_reimbursement`
--

DROP TABLE IF EXISTS `accounts_reimbursement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_reimbursement` (
  `event_ptr_id` int(11) NOT NULL,
  `price` decimal(8,2) NOT NULL,
  `currency` varchar(3) NOT NULL,
  PRIMARY KEY (`event_ptr_id`),
  CONSTRAINT `accounts_reimburseme_event_ptr_id_7d91c7b1_fk_accounts_` FOREIGN KEY (`event_ptr_id`) REFERENCES `accounts_event` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_reimbursement`
--

LOCK TABLES `accounts_reimbursement` WRITE;
/*!40000 ALTER TABLE `accounts_reimbursement` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_reimbursement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_subscribe`
--

DROP TABLE IF EXISTS `accounts_subscribe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_subscribe` (
  `event_ptr_id` int(11) NOT NULL,
  `duration` smallint(5) unsigned NOT NULL,
  `volumes` int(10) unsigned NOT NULL,
  `sub_type` varchar(255) NOT NULL,
  `price_paid` decimal(10,2) NOT NULL,
  `deposit` decimal(10,2) DEFAULT NULL,
  `currency` varchar(3) NOT NULL,
  `modification` varchar(50) NOT NULL,
  PRIMARY KEY (`event_ptr_id`),
  CONSTRAINT `accounts_subscribe_event_ptr_id_e82525ad_fk_accounts_event_id` FOREIGN KEY (`event_ptr_id`) REFERENCES `accounts_event` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_subscribe`
--

LOCK TABLES `accounts_subscribe` WRITE;
/*!40000 ALTER TABLE `accounts_subscribe` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_subscribe` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `codename` varchar(100) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry','add_logentry',1),(2,'Can change log entry','change_logentry',1),(3,'Can delete log entry','delete_logentry',1),(4,'Can add user','add_user',2),(5,'Can change user','change_user',2),(6,'Can delete user','delete_user',2),(7,'Can add group','add_group',3),(8,'Can change group','change_group',3),(9,'Can delete group','delete_group',3),(10,'Can add permission','add_permission',4),(11,'Can change permission','change_permission',4),(12,'Can delete permission','delete_permission',4),(13,'Can add content type','add_contenttype',5),(14,'Can change content type','change_contenttype',5),(15,'Can delete content type','delete_contenttype',5),(16,'Can add session','add_session',6),(17,'Can change session','change_session',6),(18,'Can delete session','delete_session',6),(19,'Can add proxy granting ticket','add_proxygrantingticket',7),(20,'Can change proxy granting ticket','change_proxygrantingticket',7),(21,'Can delete proxy granting ticket','delete_proxygrantingticket',7),(22,'Can add session ticket','add_sessionticket',8),(23,'Can change session ticket','change_sessionticket',8),(24,'Can delete session ticket','delete_sessionticket',8),(25,'Can add account address','add_accountaddress',9),(26,'Can change account address','change_accountaddress',9),(27,'Can delete account address','delete_accountaddress',9),(28,'Can add event','add_event',10),(29,'Can change event','change_event',10),(30,'Can delete event','delete_event',10),(31,'Can add account','add_account',11),(32,'Can change account','change_account',11),(33,'Can delete account','delete_account',11),(34,'Can add address','add_address',12),(35,'Can change address','change_address',12),(36,'Can delete address','delete_address',12),(37,'Can add reimbursement','add_reimbursement',13),(38,'Can change reimbursement','change_reimbursement',13),(39,'Can delete reimbursement','delete_reimbursement',13),(40,'Can add purchase','add_purchase',14),(41,'Can change purchase','change_purchase',14),(42,'Can delete purchase','delete_purchase',14),(43,'Can add borrow','add_borrow',15),(44,'Can change borrow','change_borrow',15),(45,'Can delete borrow','delete_borrow',15),(46,'Can add subscribe','add_subscribe',16),(47,'Can change subscribe','change_subscribe',16),(48,'Can delete subscribe','delete_subscribe',16),(49,'Can add publisher place','add_publisherplace',17),(50,'Can change publisher place','change_publisherplace',17),(51,'Can delete publisher place','delete_publisherplace',17),(52,'Can add item','add_item',18),(53,'Can change item','change_item',18),(54,'Can delete item','delete_item',18),(55,'Can add publisher','add_publisher',19),(56,'Can change publisher','change_publisher',19),(57,'Can delete publisher','delete_publisher',19),(58,'Can add profession','add_profession',20),(59,'Can change profession','change_profession',20),(60,'Can delete profession','delete_profession',20),(61,'Can add country','add_country',21),(62,'Can change country','change_country',21),(63,'Can delete country','delete_country',21),(64,'Can add person','add_person',22),(65,'Can change person','change_person',22),(66,'Can delete person','delete_person',22),(67,'Can add relationship','add_relationship',23),(68,'Can change relationship','change_relationship',23),(69,'Can delete relationship','delete_relationship',23),(70,'Can add relationship type','add_relationshiptype',24),(71,'Can change relationship type','change_relationshiptype',24),(72,'Can delete relationship type','delete_relationshiptype',24),(73,'Can add source type','add_sourcetype',25),(74,'Can change source type','change_sourcetype',25),(75,'Can delete source type','delete_sourcetype',25),(76,'Can add bibliography','add_bibliography',26),(77,'Can change bibliography','change_bibliography',26),(78,'Can delete bibliography','delete_bibliography',26),(79,'Can add footnote','add_footnote',27),(80,'Can change footnote','change_footnote',27),(81,'Can delete footnote','delete_footnote',27),(82,'Can add info url','add_infourl',28),(83,'Can change info url','change_infourl',28),(84,'Can delete info url','delete_infourl',28);
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `books_item`
--

DROP TABLE IF EXISTS `books_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_item` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `mep_id` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  `volume` smallint(5) unsigned DEFAULT NULL,
  `number` smallint(5) unsigned DEFAULT NULL,
  `year` smallint(5) unsigned DEFAULT NULL,
  `season` varchar(255) NOT NULL,
  `edition` varchar(255) NOT NULL,
  `viaf_id` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_item`
--

LOCK TABLES `books_item` WRITE;
/*!40000 ALTER TABLE `books_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `books_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `books_item_authors`
--

DROP TABLE IF EXISTS `books_item_authors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_item_authors` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `person_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `books_item_authors_item_id_person_id_9bddb8ff_uniq` (`item_id`,`person_id`),
  KEY `books_item_authors_person_id_a1750a01_fk_people_person_id` (`person_id`),
  CONSTRAINT `books_item_authors_item_id_844e857b_fk_books_item_id` FOREIGN KEY (`item_id`) REFERENCES `books_item` (`id`),
  CONSTRAINT `books_item_authors_person_id_a1750a01_fk_people_person_id` FOREIGN KEY (`person_id`) REFERENCES `people_person` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_item_authors`
--

LOCK TABLES `books_item_authors` WRITE;
/*!40000 ALTER TABLE `books_item_authors` DISABLE KEYS */;
/*!40000 ALTER TABLE `books_item_authors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `books_item_editors`
--

DROP TABLE IF EXISTS `books_item_editors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_item_editors` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `person_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `books_item_editors_item_id_person_id_1ba28606_uniq` (`item_id`,`person_id`),
  KEY `books_item_editors_person_id_45ff5759_fk_people_person_id` (`person_id`),
  CONSTRAINT `books_item_editors_item_id_0d147669_fk_books_item_id` FOREIGN KEY (`item_id`) REFERENCES `books_item` (`id`),
  CONSTRAINT `books_item_editors_person_id_45ff5759_fk_people_person_id` FOREIGN KEY (`person_id`) REFERENCES `people_person` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_item_editors`
--

LOCK TABLES `books_item_editors` WRITE;
/*!40000 ALTER TABLE `books_item_editors` DISABLE KEYS */;
/*!40000 ALTER TABLE `books_item_editors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `books_item_pub_places`
--

DROP TABLE IF EXISTS `books_item_pub_places`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_item_pub_places` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `publisherplace_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `books_item_pub_places_item_id_publisherplace_id_1fcd775d_uniq` (`item_id`,`publisherplace_id`),
  KEY `books_item_pub_place_publisherplace_id_f7843efd_fk_books_pub` (`publisherplace_id`),
  CONSTRAINT `books_item_pub_place_publisherplace_id_f7843efd_fk_books_pub` FOREIGN KEY (`publisherplace_id`) REFERENCES `books_publisherplace` (`id`),
  CONSTRAINT `books_item_pub_places_item_id_bbe36b94_fk_books_item_id` FOREIGN KEY (`item_id`) REFERENCES `books_item` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_item_pub_places`
--

LOCK TABLES `books_item_pub_places` WRITE;
/*!40000 ALTER TABLE `books_item_pub_places` DISABLE KEYS */;
/*!40000 ALTER TABLE `books_item_pub_places` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `books_item_publishers`
--

DROP TABLE IF EXISTS `books_item_publishers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_item_publishers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `publisher_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `books_item_publishers_item_id_publisher_id_afea0d04_uniq` (`item_id`,`publisher_id`),
  KEY `books_item_publisher_publisher_id_717db081_fk_books_pub` (`publisher_id`),
  CONSTRAINT `books_item_publisher_publisher_id_717db081_fk_books_pub` FOREIGN KEY (`publisher_id`) REFERENCES `books_publisher` (`id`),
  CONSTRAINT `books_item_publishers_item_id_7b1b588f_fk_books_item_id` FOREIGN KEY (`item_id`) REFERENCES `books_item` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_item_publishers`
--

LOCK TABLES `books_item_publishers` WRITE;
/*!40000 ALTER TABLE `books_item_publishers` DISABLE KEYS */;
/*!40000 ALTER TABLE `books_item_publishers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `books_item_translators`
--

DROP TABLE IF EXISTS `books_item_translators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_item_translators` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `person_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `books_item_translators_item_id_person_id_a68fa913_uniq` (`item_id`,`person_id`),
  KEY `books_item_translators_person_id_d78e2c96_fk_people_person_id` (`person_id`),
  CONSTRAINT `books_item_translators_item_id_69a2b8b3_fk_books_item_id` FOREIGN KEY (`item_id`) REFERENCES `books_item` (`id`),
  CONSTRAINT `books_item_translators_person_id_d78e2c96_fk_people_person_id` FOREIGN KEY (`person_id`) REFERENCES `people_person` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_item_translators`
--

LOCK TABLES `books_item_translators` WRITE;
/*!40000 ALTER TABLE `books_item_translators` DISABLE KEYS */;
/*!40000 ALTER TABLE `books_item_translators` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `books_publisher`
--

DROP TABLE IF EXISTS `books_publisher`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_publisher` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_publisher`
--

LOCK TABLES `books_publisher` WRITE;
/*!40000 ALTER TABLE `books_publisher` DISABLE KEYS */;
/*!40000 ALTER TABLE `books_publisher` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `books_publisherplace`
--

DROP TABLE IF EXISTS `books_publisherplace`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_publisherplace` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `notes` longtext NOT NULL,
  `latitude` decimal(8,5) NOT NULL,
  `longitude` decimal(8,5) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_publisherplace`
--

LOCK TABLES `books_publisherplace` WRITE;
/*!40000 ALTER TABLE `books_publisherplace` DISABLE KEYS */;
/*!40000 ALTER TABLE `books_publisherplace` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_cas_ng_proxygrantingticket`
--

DROP TABLE IF EXISTS `django_cas_ng_proxygrantingticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_cas_ng_proxygrantingticket` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_key` varchar(255) DEFAULT NULL,
  `pgtiou` varchar(255) DEFAULT NULL,
  `pgt` varchar(255) DEFAULT NULL,
  `date` datetime(6) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_cas_ng_proxygrant_session_key_user_id_4cd2ea19_uniq` (`session_key`,`user_id`),
  KEY `django_cas_ng_proxyg_user_id_f833edd2_fk_auth_user` (`user_id`),
  CONSTRAINT `django_cas_ng_proxyg_user_id_f833edd2_fk_auth_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_cas_ng_proxygrantingticket`
--

LOCK TABLES `django_cas_ng_proxygrantingticket` WRITE;
/*!40000 ALTER TABLE `django_cas_ng_proxygrantingticket` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_cas_ng_proxygrantingticket` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_cas_ng_sessionticket`
--

DROP TABLE IF EXISTS `django_cas_ng_sessionticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_cas_ng_sessionticket` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_key` varchar(255) NOT NULL,
  `ticket` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_cas_ng_sessionticket`
--

LOCK TABLES `django_cas_ng_sessionticket` WRITE;
/*!40000 ALTER TABLE `django_cas_ng_sessionticket` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_cas_ng_sessionticket` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (11,'accounts','account'),(9,'accounts','accountaddress'),(12,'accounts','address'),(15,'accounts','borrow'),(10,'accounts','event'),(14,'accounts','purchase'),(13,'accounts','reimbursement'),(16,'accounts','subscribe'),(1,'admin','logentry'),(3,'auth','group'),(4,'auth','permission'),(2,'auth','user'),(18,'books','item'),(19,'books','publisher'),(17,'books','publisherplace'),(5,'contenttypes','contenttype'),(7,'django_cas_ng','proxygrantingticket'),(8,'django_cas_ng','sessionticket'),(26,'footnotes','bibliography'),(27,'footnotes','footnote'),(25,'footnotes','sourcetype'),(21,'people','country'),(28,'people','infourl'),(22,'people','person'),(20,'people','profession'),(23,'people','relationship'),(24,'people','relationshiptype'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'people','0001_initial','2017-07-05 16:45:40.140044'),(2,'books','0001_initial','2017-07-05 16:45:40.605094'),(3,'accounts','0001_initial','2017-07-05 16:45:41.356891'),(4,'contenttypes','0001_initial','2017-07-05 16:45:41.395328'),(5,'auth','0001_initial','2017-07-05 16:45:41.735082'),(6,'admin','0001_initial','2017-07-05 16:45:41.810969'),(7,'django_cas_ng','0001_initial','2017-07-05 16:45:41.905202'),(8,'footnotes','0001_initial','2017-07-05 16:45:42.063825'),(9,'sessions','0001_initial','2017-07-05 16:45:42.102835'),(10,'people','0002_add_other_urls_person_m2m','2017-07-10 13:21:57.368531');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `footnotes_bibliography`
--

DROP TABLE IF EXISTS `footnotes_bibliography`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `footnotes_bibliography` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `bibliographic_note` longtext NOT NULL,
  `source_type_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `footnotes_bibliograp_source_type_id_9f345508_fk_footnotes` (`source_type_id`),
  CONSTRAINT `footnotes_bibliograp_source_type_id_9f345508_fk_footnotes` FOREIGN KEY (`source_type_id`) REFERENCES `footnotes_sourcetype` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `footnotes_bibliography`
--

LOCK TABLES `footnotes_bibliography` WRITE;
/*!40000 ALTER TABLE `footnotes_bibliography` DISABLE KEYS */;
/*!40000 ALTER TABLE `footnotes_bibliography` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `footnotes_footnote`
--

DROP TABLE IF EXISTS `footnotes_footnote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `footnotes_footnote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `location` longtext NOT NULL,
  `snippet_text` longtext NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `is_agree` tinyint(1) NOT NULL,
  `bibliography_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `footnotes_footnote_bibliography_id_d331761a_fk_footnotes` (`bibliography_id`),
  KEY `footnotes_footnote_content_type_id_2044e4b6_fk_django_co` (`content_type_id`),
  CONSTRAINT `footnotes_footnote_bibliography_id_d331761a_fk_footnotes` FOREIGN KEY (`bibliography_id`) REFERENCES `footnotes_bibliography` (`id`),
  CONSTRAINT `footnotes_footnote_content_type_id_2044e4b6_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `footnotes_footnote`
--

LOCK TABLES `footnotes_footnote` WRITE;
/*!40000 ALTER TABLE `footnotes_footnote` DISABLE KEYS */;
/*!40000 ALTER TABLE `footnotes_footnote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `footnotes_sourcetype`
--

DROP TABLE IF EXISTS `footnotes_sourcetype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `footnotes_sourcetype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `footnotes_sourcetype`
--

LOCK TABLES `footnotes_sourcetype` WRITE;
/*!40000 ALTER TABLE `footnotes_sourcetype` DISABLE KEYS */;
/*!40000 ALTER TABLE `footnotes_sourcetype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `people_country`
--

DROP TABLE IF EXISTS `people_country`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `people_country` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `code` varchar(3) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people_country`
--

LOCK TABLES `people_country` WRITE;
/*!40000 ALTER TABLE `people_country` DISABLE KEYS */;
/*!40000 ALTER TABLE `people_country` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `people_infourl`
--

DROP TABLE IF EXISTS `people_infourl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `people_infourl` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `url` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people_infourl`
--

LOCK TABLES `people_infourl` WRITE;
/*!40000 ALTER TABLE `people_infourl` DISABLE KEYS */;
/*!40000 ALTER TABLE `people_infourl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `people_person`
--

DROP TABLE IF EXISTS `people_person`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `people_person` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `start_year` int(10) unsigned DEFAULT NULL,
  `end_year` int(10) unsigned DEFAULT NULL,
  `mep_id` varchar(255) NOT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `viaf_id` varchar(200) NOT NULL,
  `sex` varchar(1) NOT NULL,
  `title` varchar(255) NOT NULL,
  `profession_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `people_person_profession_id_88564e21_fk_people_profession_id` (`profession_id`),
  CONSTRAINT `people_person_profession_id_88564e21_fk_people_profession_id` FOREIGN KEY (`profession_id`) REFERENCES `people_profession` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people_person`
--

LOCK TABLES `people_person` WRITE;
/*!40000 ALTER TABLE `people_person` DISABLE KEYS */;
/*!40000 ALTER TABLE `people_person` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `people_person_nationalities`
--

DROP TABLE IF EXISTS `people_person_nationalities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `people_person_nationalities` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `person_id` int(11) NOT NULL,
  `country_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `people_person_nationalities_person_id_country_id_8418faf4_uniq` (`person_id`,`country_id`),
  KEY `people_person_nation_country_id_7e0cd367_fk_people_co` (`country_id`),
  CONSTRAINT `people_person_nation_country_id_7e0cd367_fk_people_co` FOREIGN KEY (`country_id`) REFERENCES `people_country` (`id`),
  CONSTRAINT `people_person_nation_person_id_53fce882_fk_people_pe` FOREIGN KEY (`person_id`) REFERENCES `people_person` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people_person_nationalities`
--

LOCK TABLES `people_person_nationalities` WRITE;
/*!40000 ALTER TABLE `people_person_nationalities` DISABLE KEYS */;
/*!40000 ALTER TABLE `people_person_nationalities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `people_person_other_URLs`
--

DROP TABLE IF EXISTS `people_person_other_URLs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `people_person_other_URLs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `person_id` int(11) NOT NULL,
  `infourl_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `people_person_other_URLs_person_id_infourl_id_7c6e29ba_uniq` (`person_id`,`infourl_id`),
  KEY `people_person_other__infourl_id_4e173334_fk_people_in` (`infourl_id`),
  CONSTRAINT `people_person_other_URLs_person_id_2d212e42_fk_people_person_id` FOREIGN KEY (`person_id`) REFERENCES `people_person` (`id`),
  CONSTRAINT `people_person_other__infourl_id_4e173334_fk_people_in` FOREIGN KEY (`infourl_id`) REFERENCES `people_infourl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people_person_other_URLs`
--

LOCK TABLES `people_person_other_URLs` WRITE;
/*!40000 ALTER TABLE `people_person_other_URLs` DISABLE KEYS */;
/*!40000 ALTER TABLE `people_person_other_URLs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `people_profession`
--

DROP TABLE IF EXISTS `people_profession`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `people_profession` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people_profession`
--

LOCK TABLES `people_profession` WRITE;
/*!40000 ALTER TABLE `people_profession` DISABLE KEYS */;
/*!40000 ALTER TABLE `people_profession` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `people_relationship`
--

DROP TABLE IF EXISTS `people_relationship`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `people_relationship` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_person_id` int(11) NOT NULL,
  `relationship_type_id` int(11) NOT NULL,
  `to_person_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `people_relationship_from_person_id_5f14b94e_fk_people_person_id` (`from_person_id`),
  KEY `people_relationship_relationship_type_id_67bbe297_fk_people_re` (`relationship_type_id`),
  KEY `people_relationship_to_person_id_c459ac2d_fk_people_person_id` (`to_person_id`),
  CONSTRAINT `people_relationship_from_person_id_5f14b94e_fk_people_person_id` FOREIGN KEY (`from_person_id`) REFERENCES `people_person` (`id`),
  CONSTRAINT `people_relationship_relationship_type_id_67bbe297_fk_people_re` FOREIGN KEY (`relationship_type_id`) REFERENCES `people_relationshiptype` (`id`),
  CONSTRAINT `people_relationship_to_person_id_c459ac2d_fk_people_person_id` FOREIGN KEY (`to_person_id`) REFERENCES `people_person` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people_relationship`
--

LOCK TABLES `people_relationship` WRITE;
/*!40000 ALTER TABLE `people_relationship` DISABLE KEYS */;
/*!40000 ALTER TABLE `people_relationship` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `people_relationshiptype`
--

DROP TABLE IF EXISTS `people_relationshiptype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `people_relationshiptype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people_relationshiptype`
--

LOCK TABLES `people_relationshiptype` WRITE;
/*!40000 ALTER TABLE `people_relationshiptype` DISABLE KEYS */;
/*!40000 ALTER TABLE `people_relationshiptype` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-07-10  9:27:32
