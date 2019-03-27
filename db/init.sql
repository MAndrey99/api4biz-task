
CREATE TABLE companies (
  id    serial primary key,
  name  text unique
);

CREATE TABLE staff (
  id    serial primary key,
  name  varchar(50) not null
);

-- так как каждый работник может работать в разных компаниях(связь многие ко многим) создаем вспомогательную таблицу
CREATE TABLE CSLinks (
  id     serial primary key,
  com_id integer references companies(id),
  emp_id integer references staff(id)
);

CREATE TABLE products (
  id           serial primary key,
  employee_id  integer,              -- ответственный сотрудник
  name         text not null unique  -- название товара
);
