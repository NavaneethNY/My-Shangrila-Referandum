
DROP DATABASE IF EXISTS cw2_2025;
CREATE DATABASE cw2_2025;
USE cw2_2025;

--
-- Table structure for table `referendum`
--

DROP TABLE IF EXISTS `referendum`;
CREATE TABLE `referendum` (
  `referendum_id` INT NOT NULL AUTO_INCREMENT,
  `referendum_title` VARCHAR(500) NOT NULL,
  `referendum_desc` TEXT,
  `status` ENUM('open', 'closed') DEFAULT 'closed',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`referendum_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE referendum
ADD COLUMN closed_at TIMESTAMP NULL DEFAULT NULL;

--
-- Dumping data for table `referendum`
--

INSERT INTO `referendum` (`referendum_id`, `referendum_title`, `referendum_desc`, `status`) VALUES 
(1, 'Should Shangri-La pursue an expansion of its administrative boundaries to incorporate adjacent counties?', 
 'This referendum seeks to determine public opinion on expanding Shangri-La administrative boundaries.', 
 'open'),
(2, 'Should Shangri-La prohibit cigarette sales?', 
 'This referendum seeks to determine public opinion on prohibiting cigarette sales within Shangri-La.', 
 'open');

--
-- Table structure for table `referendum_options`
--

DROP TABLE IF EXISTS `referendum_options`;
CREATE TABLE `referendum_options` (
  `opt_id` INT NOT NULL AUTO_INCREMENT,
  `referendum_id` INT NOT NULL,
  `option_text` TEXT NOT NULL,
  PRIMARY KEY (`opt_id`),
  KEY `fk_referendum` (`referendum_id`),
  CONSTRAINT `fk_referendum` FOREIGN KEY (`referendum_id`) 
    REFERENCES `referendum` (`referendum_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `referendum_options`
--

INSERT INTO `referendum_options` (`opt_id`, `referendum_id`, `option_text`) VALUES 
(1, 1, 'Expand its boundaries to include all adjacent counties'),
(2, 1, 'Remain status quo'),
(3, 2, 'Yes'),
(4, 2, 'No');

--
-- Table structure for table `scc_code`
--

DROP TABLE IF EXISTS `scc_code`;
CREATE TABLE `scc_code` (
  `scc` VARCHAR(11) NOT NULL,
  `used` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`scc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `scc_code`
--

INSERT INTO `scc_code` (`scc`, `used`) VALUES 
('0IXYCAH8UW', 0),
('12EOU5RGVX', 0),
('1AZN0FXJVM', 0),
('46HJV9KH1F', 0),
('4XRDN9O4AW', 0),
('921664ML8D', 0),
('9IJKHGHJK4', 0),
('A546AKU16A', 0),
('GKJ3K1YBGE', 0),
('IGBQET8OOY', 0),
('IKKSZYJTSH', 0),
('JOV50TOSYR', 0),
('N5J53QK9FO', 0),
('R2ZHBUYO2V', 0),
('S6K3AV3IVR', 0),
('SDUBJ5IOYB', 0),
('V0GB2G690L', 0),
('YFUVLYBQZR', 0),
('Z9HOC1LF4X', 0),
('ZDN06T01V9', 0);

--
-- Table structure for table `voters`
--

DROP TABLE IF EXISTS `voters`;
CREATE TABLE `voters` (
  `voter_email` VARCHAR(100) NOT NULL,
  `fullname` VARCHAR(100) NOT NULL,
  `dob` DATE NOT NULL,
  `passwordhash` VARCHAR(64) NOT NULL,
  `scc` VARCHAR(11) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`voter_email`),
  UNIQUE KEY `unique_scc` (`scc`),
  CONSTRAINT `fk_voters_scc` FOREIGN KEY (`scc`) 
    REFERENCES `scc_code` (`scc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `voter_history`
--

DROP TABLE IF EXISTS `voter_history`;
CREATE TABLE `voter_history` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `voter_email` VARCHAR(100) NOT NULL,
  `referendum_id` INT NOT NULL,
  `voted_option_id` INT NOT NULL,
  `voted_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_vote` (`voter_email`, `referendum_id`),
  KEY `fk_voter` (`voter_email`),
  KEY `fk_referendum_vote` (`referendum_id`),
  KEY `fk_option` (`voted_option_id`),
  CONSTRAINT `fk_voter` FOREIGN KEY (`voter_email`) 
    REFERENCES `voters` (`voter_email`) ON DELETE CASCADE,
  CONSTRAINT `fk_referendum_vote` FOREIGN KEY (`referendum_id`) 
    REFERENCES `referendum` (`referendum_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_option` FOREIGN KEY (`voted_option_id`) 
    REFERENCES `referendum_options` (`opt_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



INSERT INTO voters (voter_email, fullname, dob, passwordhash, scc) VALUES
('alice.wong@example.com', 'Alice Wong', '1995-04-12', 'a3f5d8c9e1b2f4a6c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f', '0IXYCAH8UW'),
('benjamin.lee@example.com', 'Benjamin Lee', '1990-09-30', 'b1c2d3e4f5a6978877665544332211ffeeddccbbaa99887766554433221100', '12EOU5RGVX'),
('charlotte.ng@example.com', 'Charlotte Ng', '1988-01-17', 'c9d8e7f6a5b4c3d2e1f0123456789abcdefabcdef1234567890fedcba9876', '1AZN0FXJVM'),
('daniel.kim@example.com', 'Daniel Kim', '1997-06-05', 'd0123456789abcdefabcdef1234567890fedcba98765432100123456789abc', '46HJV9KH1F'),
('emma.tan@example.com', 'Emma Tan', '2000-03-22', 'eabcdef1234567890fedcba98765432100123456789abcdefabcdef1234567', '4XRDN9O4AW'),
('farid.hassan@example.com', 'Farid Hassan', '1992-11-14', 'f123456789abcdefabcdef1234567890fedcba98765432100123456789abcd', '921664ML8D'),
('grace.lim@example.com', 'Grace Lim', '1985-08-09', '0123456789abcdefabcdef1234567890fedcba98765432100123456789abcde', '9IJKHGHJK4'),
('harry.ong@example.com', 'Harry Ong', '1998-12-01', '11111111112222222222333333333344444444445555555555666666666677', 'Z9HOC1LF4X'),
('isabella.choi@example.com', 'Isabella Choi', '1994-05-18', '22222222223333333333444444444455555555556666666666777777777788', 'YFUVLYBQZR'),
('jason.yeo@example.com', 'Jason Yeo', '1991-02-27', '33333333334444444444555555555566666666667777777777888888888899', 'IGBQET8OOY'),
('kelvin.low@example.com', 'Kelvin Low', '1989-07-07', '444444444455555555556666666666777777777788888888889999999999aa', 'V0GB2G690L'),
('linda.park@example.com', 'Linda Park', '1996-10-11', '55555555556666666666777777777788888888889999999999aaaaaaaaaabb', 'SDUBJ5IOYB'),
('michael.neo@example.com', 'Michael Neo', '1987-01-03', '6666666666777777777788888888889999999999aaaaaaaaaabbbbbbbbbbbb', 'N5J53QK9FO'),
('natalie.goh@example.com', 'Natalie Goh', '1999-04-25', '777777777788888888889999999999aaaaaaaaaabbbbbbbbbbbccccccccccc', 'R2ZHBUYO2V'),
('oscar.tay@example.com', 'Oscar Tay', '1993-09-16', '88888888889999999999aaaaaaaaaabbbbbbbbbbbcccccccccccdddddddddd', 'S6K3AV3IVR');
