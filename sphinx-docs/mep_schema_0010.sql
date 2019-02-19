-- MySQL dump 10.14  Distrib 5.5.57-MariaDB, for osx10.14 (x86_64)
--
-- Host: localhost    Database: testmep
-- ------------------------------------------------------
-- Server version	5.5.62-MariaDB-1~trusty

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
  `card_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_account_card_id_9ea3a165_fk_footnotes_bibliography_id` (`card_id`),
  CONSTRAINT `accounts_account_card_id_9ea3a165_fk_footnotes_bibliography_id` FOREIGN KEY (`card_id`) REFERENCES `footnotes_bibliography` (`id`)
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
-- Table structure for table `accounts_address`
--

DROP TABLE IF EXISTS `accounts_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_address` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `account_id` int(11) DEFAULT NULL,
  `location_id` int(11) NOT NULL,
  `care_of_person_id` int(11) DEFAULT NULL,
  `person_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_address_account_id_aa0fe0e4_fk_accounts_account_id` (`account_id`),
  KEY `accounts_address_care_of_person_id_0753ed78_fk_people_person_id` (`care_of_person_id`),
  KEY `accounts_address_location_id_630d6aa9_fk_people_location_id` (`location_id`),
  KEY `accounts_address_person_id_9a2b6dba_fk_people_person_id` (`person_id`),
  CONSTRAINT `accounts_address_person_id_9a2b6dba_fk_people_person_id` FOREIGN KEY (`person_id`) REFERENCES `people_person` (`id`),
  CONSTRAINT `accounts_address_account_id_aa0fe0e4_fk_accounts_account_id` FOREIGN KEY (`account_id`) REFERENCES `accounts_account` (`id`),
  CONSTRAINT `accounts_address_care_of_person_id_0753ed78_fk_people_person_id` FOREIGN KEY (`care_of_person_id`) REFERENCES `people_person` (`id`),
  CONSTRAINT `accounts_address_location_id_630d6aa9_fk_people_location_id` FOREIGN KEY (`location_id`) REFERENCES `people_location` (`id`)
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
  `item_id` int(11) DEFAULT NULL,
  `end_date_precision` smallint(5) unsigned DEFAULT NULL,
  `start_date_precision` smallint(5) unsigned DEFAULT NULL,
  `item_status` varchar(2) NOT NULL,
  PRIMARY KEY (`event_ptr_id`),
  KEY `accounts_borrow_item_id_defb6274_fk_books_item_id` (`item_id`),
  CONSTRAINT `accounts_borrow_event_ptr_id_0843af63_fk_accounts_event_id` FOREIGN KEY (`event_ptr_id`) REFERENCES `accounts_event` (`id`),
  CONSTRAINT `accounts_borrow_item_id_defb6274_fk_books_item_id` FOREIGN KEY (`item_id`) REFERENCES `books_item` (`id`)
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
  `price` decimal(8,2) DEFAULT NULL,
  `currency` varchar(3) NOT NULL,
  `item_id` int(11) NOT NULL,
  `end_date_precision` smallint(5) unsigned DEFAULT NULL,
  `start_date_precision` smallint(5) unsigned DEFAULT NULL,
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
  `refund` decimal(8,2) DEFAULT NULL,
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
-- Table structure for table `accounts_subscription`
--

DROP TABLE IF EXISTS `accounts_subscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_subscription` (
  `event_ptr_id` int(11) NOT NULL,
  `duration` int(10) unsigned DEFAULT NULL,
  `volumes` decimal(4,2) DEFAULT NULL,
  `price_paid` decimal(10,2) DEFAULT NULL,
  `deposit` decimal(10,2) DEFAULT NULL,
  `currency` varchar(3) NOT NULL,
  `subtype` varchar(50) NOT NULL,
  `category_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`event_ptr_id`),
  KEY `accounts_subscribe_category_id_5c3966d8_fk_accounts_` (`category_id`),
  CONSTRAINT `accounts_subscribe_category_id_5c3966d8_fk_accounts_` FOREIGN KEY (`category_id`) REFERENCES `accounts_subscriptiontype` (`id`),
  CONSTRAINT `accounts_subscribe_event_ptr_id_e82525ad_fk_accounts_event_id` FOREIGN KEY (`event_ptr_id`) REFERENCES `accounts_event` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_subscription`
--

LOCK TABLES `accounts_subscription` WRITE;
/*!40000 ALTER TABLE `accounts_subscription` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_subscription` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_subscriptiontype`
--

DROP TABLE IF EXISTS `accounts_subscriptiontype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts_subscriptiontype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_subscriptiontype`
--

LOCK TABLES `accounts_subscriptiontype` WRITE;
/*!40000 ALTER TABLE `accounts_subscriptiontype` DISABLE KEYS */;
INSERT INTO `accounts_subscriptiontype` VALUES (1,'A',''),(2,'B',''),(3,'A+B',''),(4,'AdL',''),(5,'Student',''),(6,'Professor',''),(7,'Other','');
/*!40000 ALTER TABLE `accounts_subscriptiontype` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
INSERT INTO `auth_group` VALUES (1,'Content Editor'),(3,'Editors'),(2,'Moderators');
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
) ENGINE=InnoDB AUTO_INCREMENT=84 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
INSERT INTO `auth_group_permissions` VALUES (1,1,1),(2,1,2),(3,1,3),(4,1,4),(5,1,5),(6,1,6),(7,1,7),(8,1,8),(9,1,9),(10,1,10),(11,1,11),(12,1,12),(13,1,13),(14,1,14),(15,1,15),(58,1,16),(59,1,17),(60,1,18),(16,1,19),(17,1,20),(18,1,21),(19,1,22),(20,1,23),(21,1,24),(22,1,37),(23,1,38),(24,1,39),(25,1,40),(26,1,41),(27,1,42),(28,1,43),(29,1,44),(30,1,45),(68,1,46),(69,1,47),(64,1,48),(65,1,49),(66,1,50),(67,1,51),(31,1,55),(32,1,56),(33,1,57),(34,1,58),(35,1,59),(36,1,60),(37,1,61),(38,1,62),(39,1,63),(40,1,64),(41,1,65),(42,1,66),(43,1,67),(44,1,68),(45,1,69),(46,1,70),(47,1,71),(48,1,72),(49,1,73),(50,1,74),(51,1,75),(52,1,76),(53,1,77),(54,1,78),(55,1,79),(56,1,80),(57,1,81),(61,1,82),(62,1,83),(63,1,84),(73,2,85),(74,2,86),(75,2,87),(77,2,88),(81,2,89),(82,2,90),(83,2,91),(70,3,85),(71,3,86),(72,3,87),(76,3,88),(78,3,89),(79,3,90),(80,3,91);
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
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=155 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add account',1,'add_account'),(2,'Can change account',1,'change_account'),(3,'Can delete account',1,'delete_account'),(4,'Can add event',2,'add_event'),(5,'Can change event',2,'change_event'),(6,'Can delete event',2,'delete_event'),(7,'Can add borrow',3,'add_borrow'),(8,'Can change borrow',3,'change_borrow'),(9,'Can delete borrow',3,'delete_borrow'),(10,'Can add purchase',4,'add_purchase'),(11,'Can change purchase',4,'change_purchase'),(12,'Can delete purchase',4,'delete_purchase'),(13,'Can add reimbursement',5,'add_reimbursement'),(14,'Can change reimbursement',5,'change_reimbursement'),(15,'Can delete reimbursement',5,'delete_reimbursement'),(16,'Can add subscription type',6,'add_subscriptiontype'),(17,'Can change subscription type',6,'change_subscriptiontype'),(18,'Can delete subscription type',6,'delete_subscriptiontype'),(19,'Can add subscription',7,'add_subscription'),(20,'Can change subscription',7,'change_subscription'),(21,'Can delete subscription',7,'delete_subscription'),(22,'Can add address',8,'add_address'),(23,'Can change address',8,'change_address'),(24,'Can delete address',8,'delete_address'),(25,'Can add log entry',9,'add_logentry'),(26,'Can change log entry',9,'change_logentry'),(27,'Can delete log entry',9,'delete_logentry'),(28,'Can add permission',10,'add_permission'),(29,'Can change permission',10,'change_permission'),(30,'Can delete permission',10,'delete_permission'),(31,'Can add group',11,'add_group'),(32,'Can change group',11,'change_group'),(33,'Can delete group',11,'delete_group'),(34,'Can add user',12,'add_user'),(35,'Can change user',12,'change_user'),(36,'Can delete user',12,'delete_user'),(37,'Can add item',13,'add_item'),(38,'Can change item',13,'change_item'),(39,'Can delete item',13,'delete_item'),(40,'Can add publisher',14,'add_publisher'),(41,'Can change publisher',14,'change_publisher'),(42,'Can delete publisher',14,'delete_publisher'),(43,'Can add publisher place',15,'add_publisherplace'),(44,'Can change publisher place',15,'change_publisherplace'),(45,'Can delete publisher place',15,'delete_publisherplace'),(46,'Can add creator',16,'add_creator'),(47,'Can change creator',16,'change_creator'),(48,'Can delete creator',16,'delete_creator'),(49,'Can add creator type',17,'add_creatortype'),(50,'Can change creator type',17,'change_creatortype'),(51,'Can delete creator type',17,'delete_creatortype'),(52,'Can add content type',18,'add_contenttype'),(53,'Can change content type',18,'change_contenttype'),(54,'Can delete content type',18,'delete_contenttype'),(55,'Can add bibliography',19,'add_bibliography'),(56,'Can change bibliography',19,'change_bibliography'),(57,'Can delete bibliography',19,'delete_bibliography'),(58,'Can add footnote',20,'add_footnote'),(59,'Can change footnote',20,'change_footnote'),(60,'Can delete footnote',20,'delete_footnote'),(61,'Can add source type',21,'add_sourcetype'),(62,'Can change source type',21,'change_sourcetype'),(63,'Can delete source type',21,'delete_sourcetype'),(64,'Can add country',22,'add_country'),(65,'Can change country',22,'change_country'),(66,'Can delete country',22,'delete_country'),(67,'Can add Informational URL',23,'add_infourl'),(68,'Can change Informational URL',23,'change_infourl'),(69,'Can delete Informational URL',23,'delete_infourl'),(70,'Can add person',24,'add_person'),(71,'Can change person',24,'change_person'),(72,'Can delete person',24,'delete_person'),(73,'Can add profession',25,'add_profession'),(74,'Can change profession',25,'change_profession'),(75,'Can delete profession',25,'delete_profession'),(76,'Can add relationship',26,'add_relationship'),(77,'Can change relationship',26,'change_relationship'),(78,'Can delete relationship',26,'delete_relationship'),(79,'Can add relationship type',27,'add_relationshiptype'),(80,'Can change relationship type',27,'change_relationshiptype'),(81,'Can delete relationship type',27,'delete_relationshiptype'),(82,'Can add location',28,'add_location'),(83,'Can change location',28,'change_location'),(84,'Can delete location',28,'delete_location'),(85,'Can add image',30,'add_image'),(86,'Can change image',30,'change_image'),(87,'Can delete image',30,'delete_image'),(88,'Can access Wagtail admin',31,'access_admin'),(89,'Can add document',32,'add_document'),(90,'Can change document',32,'change_document'),(91,'Can delete document',32,'delete_document'),(92,'Can add session',33,'add_session'),(93,'Can change session',33,'change_session'),(94,'Can delete session',33,'delete_session'),(95,'Can add site',34,'add_site'),(96,'Can change site',34,'change_site'),(97,'Can delete site',34,'delete_site'),(98,'Can add redirect',35,'add_redirect'),(99,'Can change redirect',35,'change_redirect'),(100,'Can delete redirect',35,'delete_redirect'),(101,'Can add proxy granting ticket',36,'add_proxygrantingticket'),(102,'Can change proxy granting ticket',36,'change_proxygrantingticket'),(103,'Can delete proxy granting ticket',36,'delete_proxygrantingticket'),(104,'Can add session ticket',37,'add_sessionticket'),(105,'Can change session ticket',37,'change_sessionticket'),(106,'Can delete session ticket',37,'delete_sessionticket'),(107,'Can add user profile',38,'add_userprofile'),(108,'Can change user profile',38,'change_userprofile'),(109,'Can delete user profile',38,'delete_userprofile'),(110,'Can add rendition',39,'add_rendition'),(111,'Can change rendition',39,'change_rendition'),(112,'Can delete rendition',39,'delete_rendition'),(113,'Can add page',29,'add_page'),(114,'Can change page',29,'change_page'),(115,'Can delete page',29,'delete_page'),(116,'Can add group page permission',40,'add_grouppagepermission'),(117,'Can change group page permission',40,'change_grouppagepermission'),(118,'Can delete group page permission',40,'delete_grouppagepermission'),(119,'Can add page revision',41,'add_pagerevision'),(120,'Can change page revision',41,'change_pagerevision'),(121,'Can delete page revision',41,'delete_pagerevision'),(122,'Can add page view restriction',42,'add_pageviewrestriction'),(123,'Can change page view restriction',42,'change_pageviewrestriction'),(124,'Can delete page view restriction',42,'delete_pageviewrestriction'),(125,'Can add site',43,'add_site'),(126,'Can change site',43,'change_site'),(127,'Can delete site',43,'delete_site'),(128,'Can add collection',44,'add_collection'),(129,'Can change collection',44,'change_collection'),(130,'Can delete collection',44,'delete_collection'),(131,'Can add group collection permission',45,'add_groupcollectionpermission'),(132,'Can change group collection permission',45,'change_groupcollectionpermission'),(133,'Can delete group collection permission',45,'delete_groupcollectionpermission'),(134,'Can add collection view restriction',46,'add_collectionviewrestriction'),(135,'Can change collection view restriction',46,'change_collectionviewrestriction'),(136,'Can delete collection view restriction',46,'delete_collectionviewrestriction'),(137,'Can add redirect',47,'add_redirect'),(138,'Can change redirect',47,'change_redirect'),(139,'Can delete redirect',47,'delete_redirect'),(140,'Can add Tag',48,'add_tag'),(141,'Can change Tag',48,'change_tag'),(142,'Can delete Tag',48,'delete_tag'),(143,'Can add Tagged Item',49,'add_taggeditem'),(144,'Can change Tagged Item',49,'change_taggeditem'),(145,'Can delete Tagged Item',49,'delete_taggeditem'),(146,'Can add content page',50,'add_contentpage'),(147,'Can change content page',50,'change_contentpage'),(148,'Can delete content page',50,'delete_contentpage'),(149,'Can add homepage',51,'add_homepage'),(150,'Can change homepage',51,'change_homepage'),(151,'Can delete homepage',51,'delete_homepage'),(152,'Can add landing page',52,'add_landingpage'),(153,'Can change landing page',52,'change_landingpage'),(154,'Can delete landing page',52,'delete_landingpage');
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
  `last_login` datetime DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime NOT NULL,
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
-- Table structure for table `books_creator`
--

DROP TABLE IF EXISTS `books_creator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_creator` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `creator_type_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `person_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `books_creator_creator_type_id_6a9eb7db_fk_books_creatortype_id` (`creator_type_id`),
  KEY `books_creator_item_id_5b7fee25_fk_books_item_id` (`item_id`),
  KEY `books_creator_person_id_16dbca83_fk_people_person_id` (`person_id`),
  CONSTRAINT `books_creator_person_id_16dbca83_fk_people_person_id` FOREIGN KEY (`person_id`) REFERENCES `people_person` (`id`),
  CONSTRAINT `books_creator_creator_type_id_6a9eb7db_fk_books_creatortype_id` FOREIGN KEY (`creator_type_id`) REFERENCES `books_creatortype` (`id`),
  CONSTRAINT `books_creator_item_id_5b7fee25_fk_books_item_id` FOREIGN KEY (`item_id`) REFERENCES `books_item` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_creator`
--

LOCK TABLES `books_creator` WRITE;
/*!40000 ALTER TABLE `books_creator` DISABLE KEYS */;
/*!40000 ALTER TABLE `books_creator` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `books_creatortype`
--

DROP TABLE IF EXISTS `books_creatortype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `books_creatortype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books_creatortype`
--

LOCK TABLES `books_creatortype` WRITE;
/*!40000 ALTER TABLE `books_creatortype` DISABLE KEYS */;
INSERT INTO `books_creatortype` VALUES (1,'Author',''),(2,'Editor',''),(3,'Translator','');
/*!40000 ALTER TABLE `books_creatortype` ENABLE KEYS */;
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
  `mep_id` varchar(255) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `volume` smallint(5) unsigned DEFAULT NULL,
  `number` smallint(5) unsigned DEFAULT NULL,
  `year` smallint(5) unsigned DEFAULT NULL,
  `season` varchar(255) NOT NULL,
  `edition` varchar(255) NOT NULL,
  `uri` varchar(200) NOT NULL,
  `updated_at` datetime,
  PRIMARY KEY (`id`),
  UNIQUE KEY `books_item_mep_id_80ed6238_uniq` (`mep_id`)
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
  CONSTRAINT `books_item_pub_places_item_id_bbe36b94_fk_books_item_id` FOREIGN KEY (`item_id`) REFERENCES `books_item` (`id`),
  CONSTRAINT `books_item_pub_place_publisherplace_id_f7843efd_fk_books_pub` FOREIGN KEY (`publisherplace_id`) REFERENCES `books_publisherplace` (`id`)
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
  `action_time` datetime NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
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
  `date` datetime NOT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'accounts','account'),(8,'accounts','address'),(3,'accounts','borrow'),(2,'accounts','event'),(4,'accounts','purchase'),(5,'accounts','reimbursement'),(7,'accounts','subscription'),(6,'accounts','subscriptiontype'),(9,'admin','logentry'),(11,'auth','group'),(10,'auth','permission'),(12,'auth','user'),(16,'books','creator'),(17,'books','creatortype'),(13,'books','item'),(14,'books','publisher'),(15,'books','publisherplace'),(18,'contenttypes','contenttype'),(36,'django_cas_ng','proxygrantingticket'),(37,'django_cas_ng','sessionticket'),(19,'footnotes','bibliography'),(20,'footnotes','footnote'),(21,'footnotes','sourcetype'),(50,'pages','contentpage'),(51,'pages','homepage'),(52,'pages','landingpage'),(22,'people','country'),(23,'people','infourl'),(28,'people','location'),(24,'people','person'),(25,'people','profession'),(26,'people','relationship'),(27,'people','relationshiptype'),(35,'redirects','redirect'),(33,'sessions','session'),(34,'sites','site'),(48,'taggit','tag'),(49,'taggit','taggeditem'),(31,'wagtailadmin','admin'),(44,'wagtailcore','collection'),(46,'wagtailcore','collectionviewrestriction'),(45,'wagtailcore','groupcollectionpermission'),(40,'wagtailcore','grouppagepermission'),(29,'wagtailcore','page'),(41,'wagtailcore','pagerevision'),(42,'wagtailcore','pageviewrestriction'),(43,'wagtailcore','site'),(32,'wagtaildocs','document'),(30,'wagtailimages','image'),(39,'wagtailimages','rendition'),(47,'wagtailredirects','redirect'),(38,'wagtailusers','userprofile');
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
  `applied` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=158 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2019-02-18 16:34:22'),(2,'footnotes','0001_initial','2019-02-18 16:34:23'),(3,'people','0001_initial','2019-02-18 16:34:23'),(4,'people','0002_add_subtype_choices','2019-02-18 16:34:23'),(5,'people','0003_infer_sex_from_title','2019-02-18 16:34:23'),(6,'contenttypes','0002_remove_content_type_name','2019-02-18 16:34:23'),(7,'auth','0001_initial','2019-02-18 16:34:24'),(8,'auth','0002_alter_permission_name_max_length','2019-02-18 16:34:24'),(9,'auth','0003_alter_user_email_max_length','2019-02-18 16:34:24'),(10,'auth','0004_alter_user_username_opts','2019-02-18 16:34:24'),(11,'auth','0005_alter_user_last_login_null','2019-02-18 16:34:24'),(12,'auth','0006_require_contenttypes_0002','2019-02-18 16:34:24'),(13,'auth','0007_alter_validators_add_error_messages','2019-02-18 16:34:24'),(14,'auth','0008_alter_user_username_max_length','2019-02-18 16:34:24'),(15,'books','0001_initial','2019-02-18 16:34:24'),(16,'accounts','0001_initial','2019-02-18 16:34:25'),(17,'people','0004_rename_address_to_location','2019-02-18 16:34:25'),(18,'accounts','0002_field_adjustments_logbook_import','2019-02-18 16:34:25'),(19,'accounts','0003_new_subscription_type_model_foreignkey','2019-02-18 16:34:25'),(20,'accounts','0004_subtype_choices_to_subscription_type_foreignkey','2019-02-18 16:34:25'),(21,'accounts','0005_remove_subscribe_sub_type','2019-02-18 16:34:25'),(22,'accounts','0006_rename_subscribe_and_modification','2019-02-18 16:34:26'),(23,'accounts','0007_currency_default_to_franc','2019-02-18 16:34:26'),(24,'accounts','0008_flag_duplicate_events','2019-02-18 16:34:26'),(25,'accounts','0009_event_ordering_reimbursement_price_to_refund','2019-02-18 16:34:26'),(26,'accounts','0010_set_reimbursement_end_date_from_start','2019-02-18 16:34:26'),(27,'accounts','0011_subscription_duration_to_days','2019-02-18 16:34:26'),(28,'accounts','0012_recalculate_durations','2019-02-18 16:34:26'),(29,'accounts','0013_rename_accountaddress_to_address','2019-02-18 16:34:26'),(30,'people','0005_people_address_to_account_address','2019-02-18 16:34:26'),(31,'people','0006_update_person_locations','2019-02-18 16:34:26'),(32,'accounts','0014_add_address_rel_to_person','2019-02-18 16:34:27'),(33,'people','0007_location_unique_constraints','2019-02-18 16:34:27'),(34,'books','0002_refactor_item_creators','2019-02-18 16:34:27'),(35,'books','0003_initial_creator_types','2019-02-18 16:34:27'),(36,'accounts','0015_borrow_event_rel_item','2019-02-18 16:34:27'),(37,'accounts','0016_add_borrow_date_precision','2019-02-18 16:34:27'),(38,'accounts','0017_revise_purchase_from_borrow','2019-02-18 16:34:28'),(39,'accounts','0015_fix_subscription_durations','2019-02-18 16:34:28'),(40,'accounts','0018_merge_20180418_1607','2019-02-18 16:34:28'),(41,'accounts','0019_allow_null_precision','2019-02-18 16:34:28'),(42,'accounts','0020_convert_bought_to_item_status','2019-02-18 16:34:28'),(43,'accounts','0021_account_card','2019-02-18 16:34:28'),(44,'accounts','0022_add_partial_date_purchase','2019-02-18 16:34:28'),(45,'accounts','0023_optional_price','2019-02-18 16:34:28'),(46,'admin','0001_initial','2019-02-18 16:34:28'),(47,'admin','0002_logentry_remove_auto_add','2019-02-18 16:34:28'),(48,'people','0008_person_is_organization','2019-02-18 16:34:28'),(49,'books','0004_viaf_to_uri','2019-02-18 16:34:28'),(50,'books','0005_item_mepid_allow_null','2019-02-18 16:34:28'),(51,'books','0006_item_creators','2019-02-18 16:34:28'),(52,'books','0007_item_updated_at','2019-02-18 16:34:29'),(53,'common','0001_content_editor_group','2019-02-18 16:34:29'),(54,'common','0002_update_content_editor_perms_subscriptiontype','2019-02-18 16:34:29'),(55,'common','0003_content_editor_perms_location','2019-02-18 16:34:29'),(56,'common','0004_update_content_editor_perms_creatortype','2019-02-18 16:34:29'),(57,'django_cas_ng','0001_initial','2019-02-18 16:34:30'),(58,'footnotes','0002_footnote_is_agree_default_true','2019-02-18 16:34:30'),(59,'taggit','0001_initial','2019-02-18 16:34:30'),(60,'wagtailimages','0001_initial','2019-02-18 16:34:30'),(61,'wagtailcore','0001_initial','2019-02-18 16:34:31'),(62,'wagtailcore','0002_initial_data','2019-02-18 16:34:31'),(63,'wagtailcore','0003_add_uniqueness_constraint_on_group_page_permission','2019-02-18 16:34:31'),(64,'wagtailcore','0004_page_locked','2019-02-18 16:34:31'),(65,'wagtailcore','0005_add_page_lock_permission_to_moderators','2019-02-18 16:34:31'),(66,'wagtailcore','0006_add_lock_page_permission','2019-02-18 16:34:31'),(67,'wagtailcore','0007_page_latest_revision_created_at','2019-02-18 16:34:31'),(68,'wagtailcore','0008_populate_latest_revision_created_at','2019-02-18 16:34:31'),(69,'wagtailcore','0009_remove_auto_now_add_from_pagerevision_created_at','2019-02-18 16:34:31'),(70,'wagtailcore','0010_change_page_owner_to_null_on_delete','2019-02-18 16:34:31'),(71,'wagtailcore','0011_page_first_published_at','2019-02-18 16:34:31'),(72,'wagtailcore','0012_extend_page_slug_field','2019-02-18 16:34:31'),(73,'wagtailcore','0013_update_golive_expire_help_text','2019-02-18 16:34:31'),(74,'wagtailcore','0014_add_verbose_name','2019-02-18 16:34:31'),(75,'wagtailcore','0015_add_more_verbose_names','2019-02-18 16:34:31'),(76,'wagtailcore','0016_change_page_url_path_to_text_field','2019-02-18 16:34:31'),(77,'wagtailimages','0002_initial_data','2019-02-18 16:34:31'),(78,'wagtailimages','0003_fix_focal_point_fields','2019-02-18 16:34:31'),(79,'wagtailimages','0004_make_focal_point_key_not_nullable','2019-02-18 16:34:31'),(80,'wagtailimages','0005_make_filter_spec_unique','2019-02-18 16:34:31'),(81,'wagtailimages','0006_add_verbose_names','2019-02-18 16:34:31'),(82,'wagtailimages','0007_image_file_size','2019-02-18 16:34:32'),(83,'wagtailimages','0008_image_created_at_index','2019-02-18 16:34:32'),(84,'wagtailimages','0009_capitalizeverbose','2019-02-18 16:34:32'),(85,'wagtailimages','0010_change_on_delete_behaviour','2019-02-18 16:34:32'),(86,'wagtailcore','0017_change_edit_page_permission_description','2019-02-18 16:34:32'),(87,'wagtailcore','0018_pagerevision_submitted_for_moderation_index','2019-02-18 16:34:32'),(88,'wagtailcore','0019_verbose_names_cleanup','2019-02-18 16:34:32'),(89,'wagtailcore','0020_add_index_on_page_first_published_at','2019-02-18 16:34:32'),(90,'wagtailcore','0021_capitalizeverbose','2019-02-18 16:34:33'),(91,'wagtailcore','0022_add_site_name','2019-02-18 16:34:33'),(92,'wagtailcore','0023_alter_page_revision_on_delete_behaviour','2019-02-18 16:34:33'),(93,'wagtailcore','0024_collection','2019-02-18 16:34:33'),(94,'wagtailcore','0025_collection_initial_data','2019-02-18 16:34:33'),(95,'wagtailcore','0026_group_collection_permission','2019-02-18 16:34:33'),(96,'wagtailimages','0011_image_collection','2019-02-18 16:34:33'),(97,'wagtailimages','0012_copy_image_permissions_to_collections','2019-02-18 16:34:33'),(98,'wagtailimages','0013_make_rendition_upload_callable','2019-02-18 16:34:33'),(99,'wagtailimages','0014_add_filter_spec_field','2019-02-18 16:34:34'),(100,'wagtailimages','0015_fill_filter_spec_field','2019-02-18 16:34:34'),(101,'wagtailimages','0016_deprecate_rendition_filter_relation','2019-02-18 16:34:34'),(102,'wagtailimages','0017_reduce_focal_point_key_max_length','2019-02-18 16:34:34'),(103,'wagtailimages','0018_remove_rendition_filter','2019-02-18 16:34:34'),(104,'wagtailimages','0019_delete_filter','2019-02-18 16:34:34'),(105,'wagtailimages','0020_add-verbose-name','2019-02-18 16:34:34'),(106,'wagtailimages','0021_image_file_hash','2019-02-18 16:34:34'),(107,'wagtailcore','0027_fix_collection_path_collation','2019-02-18 16:34:34'),(108,'wagtailcore','0024_alter_page_content_type_on_delete_behaviour','2019-02-18 16:34:34'),(109,'wagtailcore','0028_merge','2019-02-18 16:34:34'),(110,'wagtailcore','0029_unicode_slugfield_dj19','2019-02-18 16:34:34'),(111,'wagtailcore','0030_index_on_pagerevision_created_at','2019-02-18 16:34:34'),(112,'wagtailcore','0031_add_page_view_restriction_types','2019-02-18 16:34:34'),(113,'wagtailcore','0032_add_bulk_delete_page_permission','2019-02-18 16:34:34'),(114,'wagtailcore','0033_remove_golive_expiry_help_text','2019-02-18 16:34:34'),(115,'wagtailcore','0034_page_live_revision','2019-02-18 16:34:35'),(116,'wagtailcore','0035_page_last_published_at','2019-02-18 16:34:35'),(117,'wagtailcore','0036_populate_page_last_published_at','2019-02-18 16:34:35'),(118,'wagtailcore','0037_set_page_owner_editable','2019-02-18 16:34:35'),(119,'wagtailcore','0038_make_first_published_at_editable','2019-02-18 16:34:35'),(120,'wagtailcore','0039_collectionviewrestriction','2019-02-18 16:34:35'),(121,'wagtailcore','0040_page_draft_title','2019-02-18 16:34:35'),(122,'pages','0001_initial','2019-02-18 16:34:36'),(123,'pages','0002_homepage_streamfield','2019-02-18 16:34:36'),(124,'people','0009_person_updated_at','2019-02-18 16:34:36'),(125,'people','0009_allow_negative_years','2019-02-18 16:34:36'),(126,'people','0010_merge_20180621_1810','2019-02-18 16:34:36'),(127,'people','0011_person_verified','2019-02-18 16:34:36'),(128,'sites','0001_initial','2019-02-18 16:34:36'),(129,'redirects','0001_initial','2019-02-18 16:34:36'),(130,'sessions','0001_initial','2019-02-18 16:34:36'),(131,'sites','0002_alter_domain_unique','2019-02-18 16:34:36'),(132,'taggit','0002_auto_20150616_2121','2019-02-18 16:34:36'),(133,'wagtailadmin','0001_create_admin_access_permissions','2019-02-18 16:34:36'),(134,'wagtaildocs','0001_initial','2019-02-18 16:34:36'),(135,'wagtaildocs','0002_initial_data','2019-02-18 16:34:36'),(136,'wagtaildocs','0003_add_verbose_names','2019-02-18 16:34:37'),(137,'wagtaildocs','0004_capitalizeverbose','2019-02-18 16:34:37'),(138,'wagtaildocs','0005_document_collection','2019-02-18 16:34:37'),(139,'wagtaildocs','0006_copy_document_permissions_to_collections','2019-02-18 16:34:37'),(140,'wagtaildocs','0005_alter_uploaded_by_user_on_delete_action','2019-02-18 16:34:37'),(141,'wagtaildocs','0007_merge','2019-02-18 16:34:37'),(142,'wagtaildocs','0008_document_file_size','2019-02-18 16:34:37'),(143,'wagtailredirects','0001_initial','2019-02-18 16:34:37'),(144,'wagtailredirects','0002_add_verbose_names','2019-02-18 16:34:37'),(145,'wagtailredirects','0003_make_site_field_editable','2019-02-18 16:34:37'),(146,'wagtailredirects','0004_set_unique_on_path_and_site','2019-02-18 16:34:37'),(147,'wagtailredirects','0005_capitalizeverbose','2019-02-18 16:34:38'),(148,'wagtailredirects','0006_redirect_increase_max_length','2019-02-18 16:34:38'),(149,'wagtailusers','0001_initial','2019-02-18 16:34:38'),(150,'wagtailusers','0002_add_verbose_name_on_userprofile','2019-02-18 16:34:38'),(151,'wagtailusers','0003_add_verbose_names','2019-02-18 16:34:38'),(152,'wagtailusers','0004_capitalizeverbose','2019-02-18 16:34:38'),(153,'wagtailusers','0005_make_related_name_wagtail_specific','2019-02-18 16:34:38'),(154,'wagtailusers','0006_userprofile_prefered_language','2019-02-18 16:34:38'),(155,'wagtailusers','0007_userprofile_current_time_zone','2019-02-18 16:34:38'),(156,'wagtailusers','0008_userprofile_avatar','2019-02-18 16:34:38'),(157,'wagtailcore','0001_squashed_0016_change_page_url_path_to_text_field','2019-02-18 16:34:38');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_redirect`
--

DROP TABLE IF EXISTS `django_redirect`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_redirect` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `site_id` int(11) NOT NULL,
  `old_path` varchar(200) NOT NULL,
  `new_path` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_redirect_site_id_old_path_ac5dd16b_uniq` (`site_id`,`old_path`),
  KEY `django_redirect_old_path_c6cc94d3` (`old_path`),
  CONSTRAINT `django_redirect_site_id_c3e37341_fk_django_site_id` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_redirect`
--

LOCK TABLES `django_redirect` WRITE;
/*!40000 ALTER TABLE `django_redirect` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_redirect` ENABLE KEYS */;
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
  `expire_date` datetime NOT NULL,
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
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_site_domain_a2e37b91_uniq` (`domain`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_site`
--

LOCK TABLES `django_site` WRITE;
/*!40000 ALTER TABLE `django_site` DISABLE KEYS */;
INSERT INTO `django_site` VALUES (1,'example.com','example.com');
/*!40000 ALTER TABLE `django_site` ENABLE KEYS */;
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
  CONSTRAINT `footnotes_footnote_content_type_id_2044e4b6_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `footnotes_footnote_bibliography_id_d331761a_fk_footnotes` FOREIGN KEY (`bibliography_id`) REFERENCES `footnotes_bibliography` (`id`)
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
-- Table structure for table `pages_contentpage`
--

DROP TABLE IF EXISTS `pages_contentpage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pages_contentpage` (
  `page_ptr_id` int(11) NOT NULL,
  `body` longtext NOT NULL,
  PRIMARY KEY (`page_ptr_id`),
  CONSTRAINT `pages_contentpage_page_ptr_id_a0907d1b_fk_wagtailcore_page_id` FOREIGN KEY (`page_ptr_id`) REFERENCES `wagtailcore_page` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pages_contentpage`
--

LOCK TABLES `pages_contentpage` WRITE;
/*!40000 ALTER TABLE `pages_contentpage` DISABLE KEYS */;
/*!40000 ALTER TABLE `pages_contentpage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pages_homepage`
--

DROP TABLE IF EXISTS `pages_homepage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pages_homepage` (
  `page_ptr_id` int(11) NOT NULL,
  `body` longtext NOT NULL,
  PRIMARY KEY (`page_ptr_id`),
  CONSTRAINT `pages_homepage_page_ptr_id_5b805d74_fk_wagtailcore_page_id` FOREIGN KEY (`page_ptr_id`) REFERENCES `wagtailcore_page` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pages_homepage`
--

LOCK TABLES `pages_homepage` WRITE;
/*!40000 ALTER TABLE `pages_homepage` DISABLE KEYS */;
/*!40000 ALTER TABLE `pages_homepage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pages_landingpage`
--

DROP TABLE IF EXISTS `pages_landingpage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pages_landingpage` (
  `page_ptr_id` int(11) NOT NULL,
  `tagline` varchar(500) NOT NULL,
  `body` longtext NOT NULL,
  `header_image_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`page_ptr_id`),
  KEY `pages_landingpage_header_image_id_cb984ee4_fk_wagtailim` (`header_image_id`),
  CONSTRAINT `pages_landingpage_header_image_id_cb984ee4_fk_wagtailim` FOREIGN KEY (`header_image_id`) REFERENCES `wagtailimages_image` (`id`),
  CONSTRAINT `pages_landingpage_page_ptr_id_4975fd94_fk_wagtailcore_page_id` FOREIGN KEY (`page_ptr_id`) REFERENCES `wagtailcore_page` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pages_landingpage`
--

LOCK TABLES `pages_landingpage` WRITE;
/*!40000 ALTER TABLE `pages_landingpage` DISABLE KEYS */;
/*!40000 ALTER TABLE `pages_landingpage` ENABLE KEYS */;
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
  `geonames_id` varchar(200) NOT NULL,
  `code` varchar(2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `geonames_id` (`geonames_id`),
  UNIQUE KEY `code` (`code`)
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
  `person_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `people_infourl_person_id_40265ba6_fk_people_person_id` (`person_id`),
  CONSTRAINT `people_infourl_person_id_40265ba6_fk_people_person_id` FOREIGN KEY (`person_id`) REFERENCES `people_person` (`id`)
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
-- Table structure for table `people_location`
--

DROP TABLE IF EXISTS `people_location`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `people_location` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notes` longtext NOT NULL,
  `name` varchar(255) NOT NULL,
  `street_address` varchar(255) NOT NULL,
  `city` varchar(255) NOT NULL,
  `postal_code` varchar(25) NOT NULL,
  `latitude` decimal(8,5) DEFAULT NULL,
  `longitude` decimal(8,5) DEFAULT NULL,
  `country_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `people_location_name_street_address_city_03529da5_uniq` (`name`,`street_address`,`city`,`country_id`),
  KEY `people_address_country_id_17e59e1d_fk_people_country_id` (`country_id`),
  CONSTRAINT `people_address_country_id_17e59e1d_fk_people_country_id` FOREIGN KEY (`country_id`) REFERENCES `people_country` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `people_location`
--

LOCK TABLES `people_location` WRITE;
/*!40000 ALTER TABLE `people_location` DISABLE KEYS */;
/*!40000 ALTER TABLE `people_location` ENABLE KEYS */;
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
  `start_year` smallint(6) DEFAULT NULL,
  `end_year` smallint(6) DEFAULT NULL,
  `mep_id` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `sort_name` varchar(255) NOT NULL,
  `viaf_id` varchar(200) NOT NULL,
  `sex` varchar(1) NOT NULL,
  `title` varchar(255) NOT NULL,
  `profession_id` int(11) DEFAULT NULL,
  `is_organization` tinyint(1) NOT NULL,
  `updated_at` datetime,
  `verified` tinyint(1) NOT NULL,
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
  `notes` longtext NOT NULL,
  `from_person_id` int(11) NOT NULL,
  `relationship_type_id` int(11) NOT NULL,
  `to_person_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `people_relationship_from_person_id_5f14b94e_fk_people_person_id` (`from_person_id`),
  KEY `people_relationship_relationship_type_id_67bbe297_fk_people_re` (`relationship_type_id`),
  KEY `people_relationship_to_person_id_c459ac2d_fk_people_person_id` (`to_person_id`),
  CONSTRAINT `people_relationship_to_person_id_c459ac2d_fk_people_person_id` FOREIGN KEY (`to_person_id`) REFERENCES `people_person` (`id`),
  CONSTRAINT `people_relationship_from_person_id_5f14b94e_fk_people_person_id` FOREIGN KEY (`from_person_id`) REFERENCES `people_person` (`id`),
  CONSTRAINT `people_relationship_relationship_type_id_67bbe297_fk_people_re` FOREIGN KEY (`relationship_type_id`) REFERENCES `people_relationshiptype` (`id`)
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

--
-- Table structure for table `taggit_tag`
--

DROP TABLE IF EXISTS `taggit_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `taggit_tag`
--

LOCK TABLES `taggit_tag` WRITE;
/*!40000 ALTER TABLE `taggit_tag` DISABLE KEYS */;
/*!40000 ALTER TABLE `taggit_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `taggit_taggeditem`
--

DROP TABLE IF EXISTS `taggit_taggeditem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_taggeditem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `object_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `tag_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `taggit_taggeditem_tag_id_f4f5b767_fk_taggit_tag_id` (`tag_id`),
  KEY `taggit_taggeditem_object_id_e2d7d1df` (`object_id`),
  KEY `taggit_taggeditem_content_type_id_object_id_196cc965_idx` (`content_type_id`,`object_id`),
  CONSTRAINT `taggit_taggeditem_tag_id_f4f5b767_fk_taggit_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `taggit_tag` (`id`),
  CONSTRAINT `taggit_taggeditem_content_type_id_9957a03c_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `taggit_taggeditem`
--

LOCK TABLES `taggit_taggeditem` WRITE;
/*!40000 ALTER TABLE `taggit_taggeditem` DISABLE KEYS */;
/*!40000 ALTER TABLE `taggit_taggeditem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_collection`
--

DROP TABLE IF EXISTS `wagtailcore_collection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_collection` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `path` varchar(255) NOT NULL,
  `depth` int(10) unsigned NOT NULL,
  `numchild` int(10) unsigned NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `path` (`path`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_collection`
--

LOCK TABLES `wagtailcore_collection` WRITE;
/*!40000 ALTER TABLE `wagtailcore_collection` DISABLE KEYS */;
INSERT INTO `wagtailcore_collection` VALUES (1,'0001',1,0,'Root');
/*!40000 ALTER TABLE `wagtailcore_collection` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_collectionviewrestriction`
--

DROP TABLE IF EXISTS `wagtailcore_collectionviewrestriction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_collectionviewrestriction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `restriction_type` varchar(20) NOT NULL,
  `password` varchar(255) NOT NULL,
  `collection_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wagtailcore_collecti_collection_id_761908ec_fk_wagtailco` (`collection_id`),
  CONSTRAINT `wagtailcore_collecti_collection_id_761908ec_fk_wagtailco` FOREIGN KEY (`collection_id`) REFERENCES `wagtailcore_collection` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_collectionviewrestriction`
--

LOCK TABLES `wagtailcore_collectionviewrestriction` WRITE;
/*!40000 ALTER TABLE `wagtailcore_collectionviewrestriction` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtailcore_collectionviewrestriction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_collectionviewrestriction_groups`
--

DROP TABLE IF EXISTS `wagtailcore_collectionviewrestriction_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_collectionviewrestriction_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `collectionviewrestriction_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wagtailcore_collectionvi_collectionviewrestrictio_988995ae_uniq` (`collectionviewrestriction_id`,`group_id`),
  KEY `wagtailcore_collecti_group_id_1823f2a3_fk_auth_grou` (`group_id`),
  CONSTRAINT `wagtailcore_collecti_group_id_1823f2a3_fk_auth_grou` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `wagtailcore_collecti_collectionviewrestri_47320efd_fk_wagtailco` FOREIGN KEY (`collectionviewrestriction_id`) REFERENCES `wagtailcore_collectionviewrestriction` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_collectionviewrestriction_groups`
--

LOCK TABLES `wagtailcore_collectionviewrestriction_groups` WRITE;
/*!40000 ALTER TABLE `wagtailcore_collectionviewrestriction_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtailcore_collectionviewrestriction_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_groupcollectionpermission`
--

DROP TABLE IF EXISTS `wagtailcore_groupcollectionpermission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_groupcollectionpermission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `collection_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wagtailcore_groupcollect_group_id_collection_id_p_a21cefe9_uniq` (`group_id`,`collection_id`,`permission_id`),
  KEY `wagtailcore_groupcol_collection_id_5423575a_fk_wagtailco` (`collection_id`),
  KEY `wagtailcore_groupcol_permission_id_1b626275_fk_auth_perm` (`permission_id`),
  CONSTRAINT `wagtailcore_groupcol_permission_id_1b626275_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `wagtailcore_groupcol_collection_id_5423575a_fk_wagtailco` FOREIGN KEY (`collection_id`) REFERENCES `wagtailcore_collection` (`id`),
  CONSTRAINT `wagtailcore_groupcol_group_id_05d61460_fk_auth_grou` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_groupcollectionpermission`
--

LOCK TABLES `wagtailcore_groupcollectionpermission` WRITE;
/*!40000 ALTER TABLE `wagtailcore_groupcollectionpermission` DISABLE KEYS */;
INSERT INTO `wagtailcore_groupcollectionpermission` VALUES (2,1,2,85),(4,1,2,86),(6,1,2,89),(8,1,2,90),(1,1,3,85),(3,1,3,86),(5,1,3,89),(7,1,3,90);
/*!40000 ALTER TABLE `wagtailcore_groupcollectionpermission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_grouppagepermission`
--

DROP TABLE IF EXISTS `wagtailcore_grouppagepermission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_grouppagepermission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `permission_type` varchar(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  `page_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wagtailcore_grouppageper_group_id_page_id_permiss_0898bdf8_uniq` (`group_id`,`page_id`,`permission_type`),
  KEY `wagtailcore_grouppag_page_id_710b114a_fk_wagtailco` (`page_id`),
  CONSTRAINT `wagtailcore_grouppag_page_id_710b114a_fk_wagtailco` FOREIGN KEY (`page_id`) REFERENCES `wagtailcore_page` (`id`),
  CONSTRAINT `wagtailcore_grouppag_group_id_fc07e671_fk_auth_grou` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_grouppagepermission`
--

LOCK TABLES `wagtailcore_grouppagepermission` WRITE;
/*!40000 ALTER TABLE `wagtailcore_grouppagepermission` DISABLE KEYS */;
INSERT INTO `wagtailcore_grouppagepermission` VALUES (1,'add',2,1),(2,'edit',2,1),(6,'lock',2,1),(3,'publish',2,1),(4,'add',3,1),(5,'edit',3,1);
/*!40000 ALTER TABLE `wagtailcore_grouppagepermission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_page`
--

DROP TABLE IF EXISTS `wagtailcore_page`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_page` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `path` varchar(255) NOT NULL,
  `depth` int(10) unsigned NOT NULL,
  `numchild` int(10) unsigned NOT NULL,
  `title` varchar(255) NOT NULL,
  `slug` varchar(255) NOT NULL,
  `live` tinyint(1) NOT NULL,
  `has_unpublished_changes` tinyint(1) NOT NULL,
  `url_path` longtext NOT NULL,
  `seo_title` varchar(255) NOT NULL,
  `show_in_menus` tinyint(1) NOT NULL,
  `search_description` longtext NOT NULL,
  `go_live_at` datetime DEFAULT NULL,
  `expire_at` datetime DEFAULT NULL,
  `expired` tinyint(1) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `locked` tinyint(1) NOT NULL,
  `latest_revision_created_at` datetime DEFAULT NULL,
  `first_published_at` datetime DEFAULT NULL,
  `live_revision_id` int(11) DEFAULT NULL,
  `last_published_at` datetime DEFAULT NULL,
  `draft_title` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `path` (`path`),
  KEY `wagtailcore_page_slug_e7c11b8f` (`slug`),
  KEY `wagtailcore_page_first_published_at_2b5dd637` (`first_published_at`),
  KEY `wagtailcore_page_content_type_id_c28424df_fk_django_co` (`content_type_id`),
  KEY `wagtailcore_page_live_revision_id_930bd822_fk_wagtailco` (`live_revision_id`),
  KEY `wagtailcore_page_owner_id_fbf7c332_fk_auth_user_id` (`owner_id`),
  CONSTRAINT `wagtailcore_page_content_type_id_c28424df_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `wagtailcore_page_live_revision_id_930bd822_fk_wagtailco` FOREIGN KEY (`live_revision_id`) REFERENCES `wagtailcore_pagerevision` (`id`),
  CONSTRAINT `wagtailcore_page_owner_id_fbf7c332_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_page`
--

LOCK TABLES `wagtailcore_page` WRITE;
/*!40000 ALTER TABLE `wagtailcore_page` DISABLE KEYS */;
INSERT INTO `wagtailcore_page` VALUES (1,'0001',1,1,'Root','root',1,0,'/','',0,'',NULL,NULL,0,29,NULL,0,NULL,NULL,NULL,NULL,'Root'),(2,'00010001',2,0,'Welcome to your new Wagtail site!','home',1,0,'/home/','',0,'',NULL,NULL,0,29,NULL,0,NULL,NULL,NULL,NULL,'Welcome to your new Wagtail site!');
/*!40000 ALTER TABLE `wagtailcore_page` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_pagerevision`
--

DROP TABLE IF EXISTS `wagtailcore_pagerevision`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_pagerevision` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `submitted_for_moderation` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `content_json` longtext NOT NULL,
  `approved_go_live_at` datetime DEFAULT NULL,
  `page_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `wagtailcore_pagerevision_submitted_for_moderation_c682e44c` (`submitted_for_moderation`),
  KEY `wagtailcore_pagerevision_page_id_d421cc1d_fk_wagtailcore_page_id` (`page_id`),
  KEY `wagtailcore_pagerevision_user_id_2409d2f4_fk_auth_user_id` (`user_id`),
  KEY `wagtailcore_pagerevision_created_at_66954e3b` (`created_at`),
  CONSTRAINT `wagtailcore_pagerevision_user_id_2409d2f4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `wagtailcore_pagerevision_page_id_d421cc1d_fk_wagtailcore_page_id` FOREIGN KEY (`page_id`) REFERENCES `wagtailcore_page` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_pagerevision`
--

LOCK TABLES `wagtailcore_pagerevision` WRITE;
/*!40000 ALTER TABLE `wagtailcore_pagerevision` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtailcore_pagerevision` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_pageviewrestriction`
--

DROP TABLE IF EXISTS `wagtailcore_pageviewrestriction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_pageviewrestriction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(255) NOT NULL,
  `page_id` int(11) NOT NULL,
  `restriction_type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wagtailcore_pageview_page_id_15a8bea6_fk_wagtailco` (`page_id`),
  CONSTRAINT `wagtailcore_pageview_page_id_15a8bea6_fk_wagtailco` FOREIGN KEY (`page_id`) REFERENCES `wagtailcore_page` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_pageviewrestriction`
--

LOCK TABLES `wagtailcore_pageviewrestriction` WRITE;
/*!40000 ALTER TABLE `wagtailcore_pageviewrestriction` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtailcore_pageviewrestriction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_pageviewrestriction_groups`
--

DROP TABLE IF EXISTS `wagtailcore_pageviewrestriction_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_pageviewrestriction_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pageviewrestriction_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wagtailcore_pageviewrest_pageviewrestriction_id_g_d23f80bb_uniq` (`pageviewrestriction_id`,`group_id`),
  KEY `wagtailcore_pageview_group_id_6460f223_fk_auth_grou` (`group_id`),
  CONSTRAINT `wagtailcore_pageview_pageviewrestriction__f147a99a_fk_wagtailco` FOREIGN KEY (`pageviewrestriction_id`) REFERENCES `wagtailcore_pageviewrestriction` (`id`),
  CONSTRAINT `wagtailcore_pageview_group_id_6460f223_fk_auth_grou` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_pageviewrestriction_groups`
--

LOCK TABLES `wagtailcore_pageviewrestriction_groups` WRITE;
/*!40000 ALTER TABLE `wagtailcore_pageviewrestriction_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtailcore_pageviewrestriction_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailcore_site`
--

DROP TABLE IF EXISTS `wagtailcore_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailcore_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(255) NOT NULL,
  `port` int(11) NOT NULL,
  `is_default_site` tinyint(1) NOT NULL,
  `root_page_id` int(11) NOT NULL,
  `site_name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wagtailcore_site_hostname_port_2c626d70_uniq` (`hostname`,`port`),
  KEY `wagtailcore_site_hostname_96b20b46` (`hostname`),
  KEY `wagtailcore_site_root_page_id_e02fb95c_fk_wagtailcore_page_id` (`root_page_id`),
  CONSTRAINT `wagtailcore_site_root_page_id_e02fb95c_fk_wagtailcore_page_id` FOREIGN KEY (`root_page_id`) REFERENCES `wagtailcore_page` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailcore_site`
--

LOCK TABLES `wagtailcore_site` WRITE;
/*!40000 ALTER TABLE `wagtailcore_site` DISABLE KEYS */;
INSERT INTO `wagtailcore_site` VALUES (1,'localhost',80,1,2,NULL);
/*!40000 ALTER TABLE `wagtailcore_site` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtaildocs_document`
--

DROP TABLE IF EXISTS `wagtaildocs_document`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtaildocs_document` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `file` varchar(100) NOT NULL,
  `created_at` datetime NOT NULL,
  `uploaded_by_user_id` int(11) DEFAULT NULL,
  `collection_id` int(11) NOT NULL,
  `file_size` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `wagtaildocs_document_collection_id_23881625_fk_wagtailco` (`collection_id`),
  KEY `wagtaildocs_document_uploaded_by_user_id_17258b41_fk_auth_user` (`uploaded_by_user_id`),
  CONSTRAINT `wagtaildocs_document_collection_id_23881625_fk_wagtailco` FOREIGN KEY (`collection_id`) REFERENCES `wagtailcore_collection` (`id`),
  CONSTRAINT `wagtaildocs_document_uploaded_by_user_id_17258b41_fk_auth_user` FOREIGN KEY (`uploaded_by_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtaildocs_document`
--

LOCK TABLES `wagtaildocs_document` WRITE;
/*!40000 ALTER TABLE `wagtaildocs_document` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtaildocs_document` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailimages_image`
--

DROP TABLE IF EXISTS `wagtailimages_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailimages_image` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `file` varchar(100) NOT NULL,
  `width` int(11) NOT NULL,
  `height` int(11) NOT NULL,
  `created_at` datetime NOT NULL,
  `focal_point_x` int(10) unsigned DEFAULT NULL,
  `focal_point_y` int(10) unsigned DEFAULT NULL,
  `focal_point_width` int(10) unsigned DEFAULT NULL,
  `focal_point_height` int(10) unsigned DEFAULT NULL,
  `uploaded_by_user_id` int(11) DEFAULT NULL,
  `file_size` int(10) unsigned DEFAULT NULL,
  `collection_id` int(11) NOT NULL,
  `file_hash` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wagtailimages_image_created_at_86fa6cd4` (`created_at`),
  KEY `wagtailimages_image_uploaded_by_user_id_5d73dc75_fk_auth_user_id` (`uploaded_by_user_id`),
  KEY `wagtailimages_image_collection_id_c2f8af7e_fk_wagtailco` (`collection_id`),
  CONSTRAINT `wagtailimages_image_collection_id_c2f8af7e_fk_wagtailco` FOREIGN KEY (`collection_id`) REFERENCES `wagtailcore_collection` (`id`),
  CONSTRAINT `wagtailimages_image_uploaded_by_user_id_5d73dc75_fk_auth_user_id` FOREIGN KEY (`uploaded_by_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailimages_image`
--

LOCK TABLES `wagtailimages_image` WRITE;
/*!40000 ALTER TABLE `wagtailimages_image` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtailimages_image` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailimages_rendition`
--

DROP TABLE IF EXISTS `wagtailimages_rendition`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailimages_rendition` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `file` varchar(100) NOT NULL,
  `width` int(11) NOT NULL,
  `height` int(11) NOT NULL,
  `focal_point_key` varchar(16) NOT NULL,
  `image_id` int(11) NOT NULL,
  `filter_spec` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wagtailimages_rendition_image_id_filter_spec_foc_323c8fe0_uniq` (`image_id`,`filter_spec`,`focal_point_key`),
  KEY `wagtailimages_rendition_filter_spec_1cba3201` (`filter_spec`),
  KEY `wagtailimages_rendition_image_id_3e1fd774` (`image_id`),
  CONSTRAINT `wagtailimages_rendit_image_id_3e1fd774_fk_wagtailim` FOREIGN KEY (`image_id`) REFERENCES `wagtailimages_image` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailimages_rendition`
--

LOCK TABLES `wagtailimages_rendition` WRITE;
/*!40000 ALTER TABLE `wagtailimages_rendition` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtailimages_rendition` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailredirects_redirect`
--

DROP TABLE IF EXISTS `wagtailredirects_redirect`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailredirects_redirect` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `old_path` varchar(255) NOT NULL,
  `is_permanent` tinyint(1) NOT NULL,
  `redirect_link` varchar(255) NOT NULL,
  `redirect_page_id` int(11) DEFAULT NULL,
  `site_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `wagtailredirects_redirect_old_path_site_id_783622d7_uniq` (`old_path`,`site_id`),
  KEY `wagtailredirects_redirect_old_path_bb35247b` (`old_path`),
  KEY `wagtailredirects_red_redirect_page_id_b5728a8f_fk_wagtailco` (`redirect_page_id`),
  KEY `wagtailredirects_red_site_id_780a0e1e_fk_wagtailco` (`site_id`),
  CONSTRAINT `wagtailredirects_red_redirect_page_id_b5728a8f_fk_wagtailco` FOREIGN KEY (`redirect_page_id`) REFERENCES `wagtailcore_page` (`id`),
  CONSTRAINT `wagtailredirects_red_site_id_780a0e1e_fk_wagtailco` FOREIGN KEY (`site_id`) REFERENCES `wagtailcore_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailredirects_redirect`
--

LOCK TABLES `wagtailredirects_redirect` WRITE;
/*!40000 ALTER TABLE `wagtailredirects_redirect` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtailredirects_redirect` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wagtailusers_userprofile`
--

DROP TABLE IF EXISTS `wagtailusers_userprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wagtailusers_userprofile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `submitted_notifications` tinyint(1) NOT NULL,
  `approved_notifications` tinyint(1) NOT NULL,
  `rejected_notifications` tinyint(1) NOT NULL,
  `user_id` int(11) NOT NULL,
  `preferred_language` varchar(10) NOT NULL,
  `current_time_zone` varchar(40) NOT NULL,
  `avatar` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `wagtailusers_userprofile_user_id_59c92331_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wagtailusers_userprofile`
--

LOCK TABLES `wagtailusers_userprofile` WRITE;
/*!40000 ALTER TABLE `wagtailusers_userprofile` DISABLE KEYS */;
/*!40000 ALTER TABLE `wagtailusers_userprofile` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-02-18 11:37:27
