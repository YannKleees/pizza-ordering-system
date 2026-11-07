-- Example data. Menu from the course database; all people, orders and codes are made up.
-- Demo login for the customer app: username demo, password demo.
USE pizza_ordering_system;
SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO `menu` VALUES (1,'Classic Menu','Pizza'),(2,'Beverages','Drink'),(3,'Sweet Treats','Dessert');

INSERT INTO `menu_item` VALUES (1,'Margherita','Pizza',14.50),(2,'Pepperoni','Pizza',16.02),(5,'BBQ Chicken','Pizza',14.12),(6,'Meat Lovers','Pizza',19.84),(7,'Mediterranean','Pizza',30.83),(8,'Vegan Special','Pizza',15.64),(9,'Four Cheese','Pizza',21.67),(10,'Buffalo Chicken','Pizza',12.06),(11,'Classic Margherita','Pizza',13.73),(12,'Spicy Pepperoni','Pizza',21.36),(13,'BBQ Bacon Ranch','Pizza',20.60),(15,'Prosciutto Arugula','Pizza',20.98),(16,'Caprese','Pizza',14.95),(17,'Garden Fresh','Pizza',16.48),(20,'Deluxe Meat','Pizza',25.64),(21,'BBQ Pulled Pork','Pizza',19.84),(22,'Buffalo Shrimp','Pizza',14.12),(23,'Greek Paradise','Pizza',16.18),(24,'Cheddar Bacon','Pizza',19.84),(25,'Sausage Supreme','Pizza',19.84),(26,'Vegan Delight','Pizza',12.21),(28,'Italian Sausage','Pizza',18.46),(29,'Coca Cola','Drink',2.00),(30,'Sprite','Drink',1.90),(31,'Fanta','Drink',2.00),(32,'Water','Drink',1.00),(33,'Chocolate Cake','Dessert',6.00),(34,'Chocolate Lava Cake','Dessert',5.00),(35,'Tiramisu','Dessert',8.00),(36,'Cheesecake','Dessert',6.00),(37,'Gelato','Dessert',3.00);

INSERT INTO `pizza` VALUES (1,'Margherita','Medium',14.50,1,0,0.40,0.09,0.00),(2,'Pepperoni','Medium',16.02,0,0,0.40,0.09,0.00),(5,'BBQ Chicken','Medium',14.12,0,0,0.40,0.09,0.00),(6,'Meat Lovers','Medium',19.84,0,0,0.40,0.09,0.00),(7,'Mediterranean','Medium',30.83,1,1,0.40,0.09,0.00),(8,'Vegan Special','Medium',15.64,1,1,0.40,0.09,0.00),(9,'Four Cheese','Medium',21.67,1,0,0.40,0.09,0.00),(10,'Buffalo Chicken','Medium',12.06,0,0,0.40,0.09,0.00),(11,'Classic Margherita','Medium',13.73,1,0,0.40,0.09,0.00),(12,'Spicy Pepperoni','Medium',21.36,0,0,0.40,0.09,0.00),(13,'BBQ Bacon Ranch','Medium',20.60,0,0,0.40,0.09,0.00),(15,'Prosciutto Arugula','Medium',20.98,0,0,0.40,0.09,0.00),(16,'Caprese','Medium',14.95,1,1,0.40,0.09,0.00),(17,'Garden Fresh','Medium',16.48,1,1,0.40,0.09,0.00),(20,'Deluxe Meat','Medium',25.64,0,0,0.40,0.09,0.00),(21,'BBQ Pulled Pork','Medium',19.84,0,0,0.40,0.09,0.00),(22,'Buffalo Shrimp','Medium',14.12,0,0,0.40,0.09,0.00),(23,'Greek Paradise','Medium',16.18,1,1,0.40,0.09,0.00),(24,'Cheddar Bacon','Medium',19.84,0,0,0.40,0.09,0.00),(25,'Sausage Supreme','Medium',19.84,0,0,0.40,0.09,0.00),(26,'Vegan Delight','Medium',12.21,1,1,0.40,0.09,0.00),(28,'Italian Sausage','Medium',18.46,0,0,0.40,0.09,0.00);

INSERT INTO `drink` VALUES (1,'Coca Cola',2.00),(3,'Sprite',2.00),(4,'Fanta',2.00),(5,'Water',1.50),(6,'Orange Juice',3.00),(7,'Iced Tea',2.50),(8,'Lemonade',2.75),(9,'Root Beer',2.25),(10,'Sparkling Water',1.75);

INSERT INTO `dessert` VALUES (1,'Chocolate Cake',5.50),(2,'Chocolate Lava Cake',4.50),(3,'Tiramisu',5.00),(4,'Cheesecake',6.00),(5,'Gelato',3.50),(6,'Brownie',3.50),(7,'Apple Pie',4.00),(8,'Banoffee Pie',4.50),(9,'Panna Cotta',5.00),(10,'Lemon Tart',4.25);

INSERT INTO `ingredient` VALUES (1,'Tomato Sauce',1,1,5.00),(2,'Mozzarella',1,0,4.00),(3,'Pepperoni',0,0,1.50),(4,'Bacon',0,0,2.00),(5,'Mushrooms',1,1,0.75),(6,'Onions',1,1,0.50),(7,'Black Olives',1,1,0.60),(8,'Green Peppers',1,1,0.60),(9,'Chicken',0,0,2.80),(10,'Pineapple',1,1,3.00),(11,'Garlic',1,1,1.50),(12,'Spinach',1,1,3.00),(13,'Sausage',0,0,2.50),(14,'Jalapenos',1,1,0.50),(15,'Red Onions',1,1,0.50),(16,'Ham',0,0,2.00),(17,'BBQ Sauce',1,1,0.50),(18,'Pulled Pork',0,0,3.00),(19,'Shrimp',0,0,3.50),(20,'Clams',0,0,3.00),(21,'Buffalo Sauce',1,1,0.50),(22,'Feta Cheese',1,0,1.20),(23,'Kalamata Olives',1,1,0.80),(24,'Cheddar Cheese',1,0,1.00),(25,'Vegan Cheese',1,1,3.00),(26,'Artichokes',1,1,2.00),(27,'Italian Sausage',0,0,2.50),(28,'Red Peppers',1,1,0.60);

INSERT INTO `pizza_ingredient` VALUES (1,1,1,NULL),(1,2,1,NULL),(1,15,1,NULL),(2,1,1,NULL),(2,2,1,NULL),(2,3,1,NULL),(5,2,1,NULL),(5,5,1,NULL),(5,9,1,NULL),(5,17,1,NULL),(5,22,1,NULL),(6,2,1,NULL),(6,3,1,NULL),(6,4,1,NULL),(6,16,1,NULL),(6,18,1,NULL),(6,21,1,NULL),(7,1,1,NULL),(7,2,1,NULL),(7,10,1,NULL),(7,11,1,NULL),(7,19,1,NULL),(7,22,1,NULL),(7,26,1,NULL),(8,1,1,NULL),(8,5,1,NULL),(8,11,1,NULL),(8,25,1,NULL),(9,1,1,NULL),(9,2,1,NULL),(9,22,1,NULL),(9,24,1,NULL),(9,25,1,NULL),(10,2,1,NULL),(10,7,1,NULL),(10,9,1,NULL),(10,21,1,NULL),(11,1,1,NULL),(11,2,1,NULL),(12,1,1,NULL),(12,2,1,NULL),(12,3,1,NULL),(12,6,1,NULL),(12,13,1,NULL),(12,17,1,NULL),(13,1,1,NULL),(13,2,1,NULL),(13,4,1,NULL),(13,16,1,NULL),(13,17,1,NULL),(15,1,1,NULL),(15,2,1,NULL),(15,5,1,NULL),(15,16,1,NULL),(15,26,1,NULL),(16,1,1,NULL),(16,2,1,NULL),(16,23,1,NULL),(17,1,1,NULL),(17,2,1,NULL),(17,7,1,NULL),(17,22,1,NULL),(20,1,1,NULL),(20,2,1,NULL),(20,9,1,NULL),(20,16,1,NULL),(20,18,1,NULL),(21,1,1,NULL),(21,2,1,NULL),(21,15,1,NULL),(21,17,1,NULL),(21,18,1,NULL),(22,2,1,NULL),(22,5,1,NULL),(22,6,1,NULL),(22,19,1,NULL),(22,21,1,NULL),(23,1,1,NULL),(23,2,1,NULL),(23,7,1,NULL),(23,14,1,NULL),(23,21,1,NULL),(24,1,1,NULL),(24,10,1,NULL),(24,11,1,NULL),(24,13,1,NULL),(24,24,1,NULL),(25,1,1,NULL),(25,2,1,NULL),(25,3,1,NULL),(25,13,1,NULL),(26,1,1,NULL),(26,25,1,NULL),(28,1,1,NULL),(28,2,1,NULL),(28,27,1,NULL),(28,28,1,NULL);

INSERT INTO `postalcodearea` VALUES ('10001','New York'),('60601','Chicago'),('6211','Maastricht'),('6212','Maastricht'),('6213','Maastricht'),('6214','Maastricht'),('6215','Maastricht'),('6216','Maastricht'),('6217','Maastricht'),('6218','Maastricht'),('6219','Maastricht'),('6221','Beek'),('6222','Heerlen'),('6223','Heerlen'),('6224','Heerlen'),('6225','Heerlen'),('6226','Heerlen'),('6227','Heerlen'),('6228','Heerlen'),('6229','Heerlen'),('6231','Roermond'),('6232','Roermond'),('6233','Roermond'),('6234','Roermond'),('6235','Roermond'),('6236','Roermond'),('6237','Roermond'),('6238','Roermond'),('6239','Roermond'),('90001','Los Angeles');

INSERT INTO `customer` (`customer_id`,`name`,`last_name`,`username`,`password`,`gender`,`birthdate`,`phone_number`,`address`,`pizzas_ordered`) VALUES
(1,'Demo','Customer','demo','2a97516c354b68848cdbd8f54a226a0a55b21ed138e207ad6c5cbb9c00aa5aea','Other','2001-05-14','0612345678','Grote Gracht 12, 6211 Maastricht',0),
(2,'Lena','Hoffmann','lena','767b181bf831a0206de45e595f88710343bfd2ded1c060bba3566bc590d5d3c8','Female','1999-11-02','0687654321','Wycker Brugstraat 5, 6212 Maastricht',0),
(3,'Tom','Peeters','tom','767b181bf831a0206de45e595f88710343bfd2ded1c060bba3566bc590d5d3c8','Male','2002-03-21','0623456789','Boschstraat 40, 6213 Maastricht',0),
(4,'Sara','Jansen','sara','767b181bf831a0206de45e595f88710343bfd2ded1c060bba3566bc590d5d3c8','Female','1998-07-30','0634567890','Tongerseweg 88, 6214 Maastricht',0),
(5,'Noah','Willems','noah','767b181bf831a0206de45e595f88710343bfd2ded1c060bba3566bc590d5d3c8','Male','2000-12-09','0645678901','Meerssenerweg 17, 6215 Maastricht',0),
(6,'Ana','Costa','ana','767b181bf831a0206de45e595f88710343bfd2ded1c060bba3566bc590d5d3c8','Other','2003-01-25','0656789012','Akerstraat 3, 6216 Maastricht',0);
INSERT INTO `deliverypersonnel` (`delivery_person_id`,`name`,`assigned_postal_code`,`availability`) VALUES
(1,'Milan de Vries','6211',1),
(2,'Eva Smit','6213',1),
(3,'Jonas Bakker','6215',1),
(4,'Lotte Visser','6216',1);
INSERT INTO `discountcode` (`code`,`expiration_date`,`is_used`,`discount_percentage`) VALUES ('SAVE10','2027-12-31',0,10.00),('WELCOME15','2027-12-31',0,15.00),('STUDENT20','2027-06-30',0,20.00);

INSERT INTO `customerorder` (`order_id`,`customer_id`,`order_date`,`confirmation_number`,`status`,`delivery_time_estimation`,`delivery_method`,`total_price`) VALUES
(1,3,'2026-10-10 18:41:00','CONF-01001','Delivered','2026-10-10 19:11:00','Delivery',16.02),
(2,5,'2026-10-04 20:13:00','CONF-01002','Delivered','2026-10-04 20:43:00','Delivery',32.04),
(3,1,'2026-10-16 13:35:00','CONF-01003','Delivered','2026-10-16 14:05:00','Delivery',16.48),
(4,6,'2026-10-04 21:37:00','CONF-01004','Delivered','2026-10-04 22:07:00','Delivery',14.95),
(5,5,'2026-10-09 16:26:00','CONF-01005','Delivered','2026-10-09 16:56:00','Pickup',38.73),
(6,1,'2026-10-13 17:06:00','CONF-01006','Delivered','2026-10-13 17:36:00','Delivery',20.08),
(7,6,'2026-11-04 18:49:00','CONF-01007','Delivered','2026-11-04 19:19:00','Delivery',47.2),
(8,2,'2026-10-12 15:05:00','CONF-01008','Out for Delivery','2026-10-12 15:35:00','Delivery',42.68),
(9,6,'2026-10-29 16:38:00','CONF-01009','Pending','2026-10-29 17:08:00','Delivery',28.24),
(10,2,'2026-10-22 14:59:00','CONF-01010','Pending','2026-10-22 15:29:00','Pickup',21.84),
(11,5,'2026-10-21 17:44:00','CONF-01011','Cancelled','2026-10-21 18:14:00','Delivery',29.98),
(12,1,'2026-10-18 19:44:00','CONF-01012','Delivered','2026-10-18 20:14:00','Delivery',18.46),
(13,6,'2026-10-29 16:45:00','CONF-01013','Delivered','2026-10-29 17:15:00','Delivery',36.9),
(14,2,'2026-10-08 19:03:00','CONF-01014','Delivered','2026-10-08 19:33:00','Delivery',23.67),
(15,4,'2026-11-01 13:10:00','CONF-01015','Delivered','2026-11-01 13:40:00','Pickup',54.28),
(16,2,'2026-10-28 20:17:00','CONF-01016','Delivered','2026-10-28 20:47:00','Delivery',24.48),
(17,1,'2026-10-12 14:14:00','CONF-01017','Delivered','2026-10-12 14:44:00','Delivery',18.46),
(18,5,'2026-10-12 16:18:00','CONF-01018','Delivered','2026-10-12 16:48:00','Delivery',29.0),
(19,5,'2026-10-21 14:44:00','CONF-01019','Delivered','2026-10-21 15:14:00','Delivery',36.24),
(20,4,'2026-10-26 13:30:00','CONF-01020','Out for Delivery','2026-10-26 14:00:00','Pickup',14.21),
(21,1,'2026-10-14 19:10:00','CONF-01021','Pending','2026-10-14 19:40:00','Delivery',21.84),
(22,1,'2026-10-10 20:06:00','CONF-01022','Pending','2026-10-10 20:36:00','Delivery',24.88),
(23,5,'2026-10-25 14:40:00','CONF-01023','Cancelled','2026-10-25 15:10:00','Delivery',32.46),
(24,1,'2026-10-08 19:29:00','CONF-01024','Delivered','2026-10-08 19:59:00','Delivery',25.84);
INSERT INTO `order_item` (`order_item_id`,`order_id`,`menu_item_id`,`quantity`,`item_type`) VALUES
(1,1,2,1,'Pizza'),
(2,2,2,2,'Pizza'),
(3,3,17,1,'Pizza'),
(4,4,16,1,'Pizza'),
(5,5,7,1,'Pizza'),
(6,5,30,1,'Drink'),
(7,5,33,1,'Dessert'),
(8,6,23,1,'Pizza'),
(9,6,30,1,'Drink'),
(10,6,29,1,'Drink'),
(11,7,13,2,'Pizza'),
(12,7,36,1,'Dessert'),
(13,8,24,2,'Pizza'),
(14,8,37,1,'Dessert'),
(15,9,5,2,'Pizza'),
(16,10,21,1,'Pizza'),
(17,10,29,1,'Drink'),
(18,11,15,1,'Pizza'),
(19,11,36,1,'Dessert'),
(20,11,37,1,'Dessert'),
(21,12,28,1,'Pizza'),
(22,13,16,2,'Pizza'),
(23,13,34,1,'Dessert'),
(24,13,29,1,'Drink'),
(25,14,9,1,'Pizza'),
(26,14,31,1,'Drink'),
(27,15,20,2,'Pizza'),
(28,15,37,1,'Dessert'),
(29,16,17,1,'Pizza'),
(30,16,35,1,'Dessert'),
(31,17,28,1,'Pizza'),
(32,18,1,2,'Pizza'),
(33,19,22,2,'Pizza'),
(34,19,29,1,'Drink'),
(35,19,36,1,'Dessert'),
(36,20,26,1,'Pizza'),
(37,20,29,1,'Drink'),
(38,21,6,1,'Pizza'),
(39,21,29,1,'Drink'),
(40,22,15,1,'Pizza'),
(41,22,29,1,'Drink'),
(42,22,30,1,'Drink'),
(43,23,11,2,'Pizza'),
(44,23,34,1,'Dessert'),
(45,24,21,1,'Pizza'),
(46,24,33,1,'Dessert');
INSERT INTO `deliveryassignment` (`assignment_id`,`order_id`,`delivery_person_id`,`assigned_at`) VALUES
(1,1,3,'2026-10-10 18:41:00'),
(2,2,4,'2026-10-04 20:13:00'),
(3,3,2,'2026-10-16 13:35:00'),
(4,4,1,'2026-10-04 21:37:00'),
(5,6,4,'2026-10-13 17:06:00'),
(6,7,3,'2026-11-04 18:49:00'),
(7,8,3,'2026-10-12 15:05:00'),
(8,12,3,'2026-10-18 19:44:00'),
(9,13,3,'2026-10-29 16:45:00'),
(10,14,4,'2026-10-08 19:03:00'),
(11,16,2,'2026-10-28 20:17:00'),
(12,17,4,'2026-10-12 14:14:00'),
(13,18,3,'2026-10-12 16:18:00'),
(14,19,4,'2026-10-21 14:44:00'),
(15,24,2,'2026-10-08 19:29:00');
UPDATE `customer` SET `pizzas_ordered` = 7 WHERE `customer_id` = 1;
UPDATE `customer` SET `pizzas_ordered` = 5 WHERE `customer_id` = 2;
UPDATE `customer` SET `pizzas_ordered` = 1 WHERE `customer_id` = 3;
UPDATE `customer` SET `pizzas_ordered` = 3 WHERE `customer_id` = 4;
UPDATE `customer` SET `pizzas_ordered` = 7 WHERE `customer_id` = 5;
UPDATE `customer` SET `pizzas_ordered` = 7 WHERE `customer_id` = 6;

SET FOREIGN_KEY_CHECKS = 1;
