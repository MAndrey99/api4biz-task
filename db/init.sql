
CREATE TABLE companies (
  id    serial primary key,
  name  text not null unique
);

CREATE TABLE staff (
  id         serial primary key,
  name       varchar(50) not null,
  company_id integer references companies(id)
);

CREATE TABLE products (
  employee_id integer references staff(id),  -- ответственный сотрудник
  name        text not null unique           -- название товара
);
