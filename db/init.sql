
CREATE TABLE companies (
  name  text primary key
);

CREATE TABLE staff (
  id            serial primary key,
  name          varchar(50) not null,
  company_name  text references companies(name)
);

CREATE TABLE products (
  employee_id  integer references staff(id),  -- ответственный сотрудник
  name         text not null unique           -- название товара
);
