# Маппинг для прогнозов по расписанию

# В преспективе это все должно уехать в БД это для шаблона


Данный JSON описывает конфигурацию прогнозов для компаний. Он хранит информацию о подключениях к БД, исходных данных и настройках регулярного прогнозирования.
Данные маппинги должны будут хранится где-то. И считываться в этот репозиторий при работе. Пока это тестовый пример

## Пример реального маппинга

```json
[
  {
    "company_name": "University of Brescia",
    "company_id": 1,
    "db_connections_id": 1,
    "data_to_predict": [
      {
        "data_id": 1,
        "data_name": "Italy Electricity Consumption",
        "source_table": "load_consumption",
        "time_column": "Datetime",
        "target_column": "load_consumption",
        "discreteness": 300,
        "target_db": "horizon",
        "methods_predict": [
          {
            "method": "XGBoost",
            "target_table": "xgb_predict_load_consumption"
          },
          {
            "method": "LSTM",
            "target_table": "predict_load_consumption"
          }
        ]
      }
    ]
  }
]
```

# Пример правильного маппинга

```json
[
  {
    "company_name": "ATS Energy",
    "company_id": 2,
    "db_connections_id": 2,
    "data_to_predict": [
      {
        "data_id": 2,
        "data_name": "Электромотребление Амурской области",
        "source_table": "consumption",
        "time_column": "time",
        "target_column": "electricity_consumption",
        "discreteness": 300,
        "target_db": "self_host",
        "methods_predict": [
          {
            "method": "XGBoost",
            "target_table": "2_2_XGBoost_consumption"
          },
          {
            "method": "LSTM",
            "target_table": "2_2_LSTM_consumption"
          }
        ]
      }
    ]
  }
]
```

## Поля маппинга

### Уровень компании
- `company_name` — название компании, задаётся пользователем при регистрации
- `company_id` — уникальный идентификатор компании, задаётся системой
- `db_connections_id` — ID подключения к базе данных, определяется системой (если компания установила коннекшн), к примеру Postgress, Influx, Timescale

### Уровень набора данных
- `data_id` — уникальный идентификатор набора данных, задаётся системой при регистрации. Для одной таблицы-источника может быть несколько разных наборов
- `data_name` — имя набора данных, задаётся пользователем
- `source_table` — таблица-источник с данными, задаётся пользователем
- `time_column` — колонка с временной меткой, задаётся пользователем
- `target_column` — колонка с целевой переменной, задаётся пользователем
- `discreteness` — дискретность временного ряда в секундах, вычисляется автоматически
- `target_db` — база, в которую сохраняются прогнозы. Опции:
    - `horizon` — системная база.
    - `self_host` - БД компании

### Методы прогнозирования
- `methods_predict` — список методов прогнозирования, которые будут выполняться регулярно
    - `method` — название метода (задаётся пользователем, можно указать несколько)
    - `target_table` — таблица, в которую сохраняются результаты. Имя генерируется автоматически по правилу:  
      `<company_id>_<data_id>_<method>_<source_table>`

## Пример генерации имён таблиц

Для набора с `company_id = 1`, `data_id = 1`, `source_table = load_consumption`:

- `1_1_XGBoost_load_consumption`
- `1_1_LSTM_load_consumption`

