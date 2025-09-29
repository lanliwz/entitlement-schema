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
```bash
mysql -h 127.0.0.1 -P 3306 -u ent_manager -p
```
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

## sample database
```sql
-- Create bank schema/database
CREATE DATABASE bank;

CREATE TABLE bank.department (
    dept_id     INT AUTO_INCREMENT PRIMARY KEY,
    dept_name   VARCHAR(100) NOT NULL,
    location    VARCHAR(100)
);
-- Employee table
CREATE TABLE bank.employee (
    emp_id      INT AUTO_INCREMENT PRIMARY KEY,
    first_name  VARCHAR(50),
    last_name   VARCHAR(50),
    job_title   VARCHAR(100),
    salary      DECIMAL(12,2),
    hire_date   DATE,
    dept_id     INT,
    FOREIGN KEY (dept_id) REFERENCES bank.department(dept_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Departments
INSERT INTO bank.department (dept_name, location) VALUES
('Finance', 'New York'),
('IT', 'San Francisco'),
('HR', 'Chicago');

-- Employees
INSERT INTO bank.employee (first_name, last_name, job_title, salary, hire_date, dept_id) VALUES
('Alice', 'Wang', 'Financial Analyst', 85000.00, '2020-03-15', 1),
('Bob', 'Smith', 'Finance Manager', 120000.00, '2018-07-10', 1),
('Carol', 'Johnson', 'Software Engineer', 95000.00, '2021-02-01', 2),
('David', 'Lee', 'System Admin', 80000.00, '2019-05-22', 2),
('Eva', 'Martinez', 'HR Specialist', 70000.00, '2022-01-12', 3);

COMMIT;
```

## query with entitlement 
```sql
select a.*,b.* from employee a join department b on a.dept_id=b.dept_id;
```

## OpenAi prompt
### Example 1
```prompt
QUESTION:

select 
    a.emp_id,
    a.first_name,
    a.last_name,
    a.job_title,
    salary,
    a.hire_date,
    b.dept_id,
    b.dept_name 
from employee a join department b 
on a.dept_id=b.dept_id; 

rewrite the query along with following entitlements associated with this user Bob: 
{'columnName': 'salary', 'policyDefinition': 'Full mask salary as numeric value of 0.00', 'ruleType': 'MASK'}
{'columnName': 'dept_name', 'policyDefinition': "Allow access to rows where dept_name = 'IT'", 'ruleType': 'ROW'}

ANSWER:

SELECT 
    a.emp_id,
    a.first_name,
    a.last_name,
    a.job_title,
    CAST(0.00 AS DECIMAL(10,2)) AS salary,  -- masked salary
    a.hire_date,
    b.dept_id,
    b.dept_name
FROM employee a
JOIN department b 
    ON a.dept_id = b.dept_id
WHERE b.dept_name = 'IT';

RESULT:
+--------+------------+-----------+-------------------+--------+------------+---------+-----------+
| emp_id | first_name | last_name | job_title         | salary | hire_date  | dept_id | dept_name |
+--------+------------+-----------+-------------------+--------+------------+---------+-----------+
|      3 | Carol      | Johnson   | Software Engineer |   0.00 | 2021-02-01 |       2 | IT        |
|      4 | David      | Lee       | System Admin      |   0.00 | 2019-05-22 |       2 | IT        |
+--------+------------+-----------+-------------------+--------+------------+---------+-----------+
```

### Example 2
```prompt
QUESTION:

select
    a.emp_id,
    a.first_name,
    a.last_name,
    a.job_title,
    salary,
    a.hire_date,
    b.dept_id,
    b.dept_name
from employee a join department b 
on a.dept_id=b.dept_id; 

rewrite the query along with following entitlements associated with this user Alice: 
{'columnName': 'salary', 'policyDefinition': 'No mask for salary, salary value should be viewed as it is', 'ruleType': 'MASK'}
{'columnName': 'dept_name', 'policyDefinition': "Allow access to rows where dept_name = 'HR'", 'ruleType': 'ROW'}
{'columnName': 'dept_name', 'policyDefinition': "Allow access to rows where dept_name = 'IT'", 'ruleType': 'ROW'}
{'columnName': 'dept_name', 'policyDefinition': "Allow access to rows where dept_name = 'Finance'", 'ruleType': 'ROW'}

ANSWER:

SELECT
    a.emp_id,
    a.first_name,
    a.last_name,
    a.job_title,
    salary,
    a.hire_date,
    b.dept_id,
    b.dept_name
FROM employee a
JOIN department b
  ON a.dept_id = b.dept_id
WHERE b.dept_name IN ('HR', 'IT', 'Finance');

RESULT:
+--------+------------+-----------+-------------------+-----------+------------+---------+-----------+
| emp_id | first_name | last_name | job_title         | salary    | hire_date  | dept_id | dept_name |
+--------+------------+-----------+-------------------+-----------+------------+---------+-----------+
|      1 | Alice      | Wang      | Financial Analyst |  85000.00 | 2020-03-15 |       1 | Finance   |
|      2 | Bob        | Smith     | Finance Manager   | 120000.00 | 2018-07-10 |       1 | Finance   |
|      3 | Carol      | Johnson   | Software Engineer |  95000.00 | 2021-02-01 |       2 | IT        |
|      4 | David      | Lee       | System Admin      |  80000.00 | 2019-05-22 |       2 | IT        |
|      5 | Eva        | Martinez  | HR Specialist     |  70000.00 | 2022-01-12 |       3 | HR        |
+--------+------------+-----------+-------------------+-----------+------------+---------+-----------+
```
