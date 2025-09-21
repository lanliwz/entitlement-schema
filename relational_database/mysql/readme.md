## MacBook install MySql 
```shell
brew update
brew install mysql
brew services start mysql
mysql --version

mysql -h 127.0.0.1 -P 3306 -u root -p
```

## Login as root and then create user
```mysql
CREATE USER 'ent_manager'@'%' IDENTIFIED BY 'ent001!';
GRANT ALL PRIVILEGES ON *.* TO 'ent_manager'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```
## Test connection
```sql
SELECT USER(), CURRENT_USER();
SHOW DATABASES;
```

## Trouble shooting
```shell
echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 21)' >> ~/.zshrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```