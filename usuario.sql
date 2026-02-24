CREATE USER 'novacapital'@'localhost' IDENTIFIED BY 'Novacapital123$';
GRANT ALL PRIVILEGES ON novacapital_db.* TO 'novacapital'@'localhost';
FLUSH PRIVILEGES;
EXIT;