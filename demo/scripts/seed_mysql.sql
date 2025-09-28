-- Create schema and tables
CREATE SCHEMA IF NOT EXISTS bank;

DROP TABLE IF EXISTS bank.employee;
DROP TABLE IF EXISTS bank.department;

CREATE TABLE bank.department (
    dept_id   INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    location  VARCHAR(100)
);

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
('Alice', 'Wang', 'Financial Analyst',  85000.00, '2020-03-15', 1),
('Bob',   'Smith','Finance Manager',   120000.00, '2018-07-10', 1),
('Carol', 'Johnson','Software Engineer',95000.00, '2021-02-01', 2),
('David', 'Lee',  'System Admin',       80000.00, '2019-05-22', 2),
('Eva',   'Martinez','HR Specialist',   70000.00, '2022-01-12', 3);