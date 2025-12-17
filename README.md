# Budget Data Updater

Автоматизированная библиотека для загрузки и обновления данных о доходах и расходах бюджетов субъектов РФ с портала [iminfin.ru](https://www.iminfin.ru).

## Возможности

- Загрузка данных о доходах и расходах региональных бюджетов
- Автоматическое определение новых доступных периодов
- Нормализация названий регионов (ОКАТО, ОКТМО)
- Сохранение в форматах: Parquet, CSV, Excel
- Загрузка в S3-совместимое хранилище
- Автоматическое обновление через GitHub Actions

## Установка

```bash
pip install -r requirements.txt
```

## Использование

### Python API

```python
from budgets import BudgetUpdater

updater = BudgetUpdater(data_dir='data')

# Обновить все данные (автоопределение новых месяцев)
result = updater.update_all(output_dir='data/processed')

# Обновить только доходы за конкретный период
result = updater.update_income(
    date_from='2024-01',
    date_to='2024-06',
    output_dir='data/processed'
)

# Обновить с загрузкой в S3
result = updater.update_all(
    output_dir='data/processed',
    s3_folder='budgets',
    version='v2024.06'
)
```

### Командная строка

```bash
# Обновить все данные
python -m budgets.main --type all --output-dir data/processed

# Обновить доходы за конкретный период
python -m budgets.main --type income --date-from 2024-01 --date-to 2024-06

# Обновить расходы с загрузкой в S3
python -m budgets.main --type expense --s3-folder budgets --version v1.0.0

# Полный список параметров
python -m budgets.main --help
```

### Параметры CLI

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--type` | Тип данных: `all`, `income`, `expense` | `all` |
| `--date-from` | Начальная дата (YYYY-MM) | Автоопределение |
| `--date-to` | Конечная дата (YYYY-MM) | Последний доступный |
| `--input` | Путь к входному parquet файлу | - |
| `--output-dir` | Директория для сохранения | `data/processed` |
| `--s3-folder` | Папка в S3 для загрузки | - |
| `--version` | Версия для S3 | Текущая дата |
| `--data-dir` | Базовая директория данных | `data` |

## Структура данных

### Доходы (budget_income)

| Колонка | Описание |
|---------|----------|
| `year` | Год |
| `month` | Месяц |
| `income_level` | Уровень детализации |
| `income_part` | Статья дохода |
| `plan` | План |
| `adj_plan_consolidated` | Уточненный план (консолидированный) |
| `adj_plan_regional` | Уточненный план (региональный) |
| `adj_plan_growth_rate` | Темп роста плана |
| `execution_consolidated` | Исполнение (консолидированный) |
| `execution_regional` | Исполнение (региональный) |
| `growth_rate_regional` | Темп роста (регион) |
| `growth_rate_federal_district` | Темп роста (ФО) |
| `growth_rate_russia` | Темп роста (Россия) |
| `object_name` | Название региона |
| `okato` | Код ОКАТО |
| `oktmo` | Код ОКТМО |
| `object_level` | Уровень объекта |

### Расходы (budget_expense)

| Колонка | Описание |
|---------|----------|
| `year` | Год |
| `month` | Месяц |
| `expense_level` | Уровень детализации |
| `expense_part` | Статья расхода |
| `plan` | План |
| `adj_plan_consolidated` | Уточненный план (консолидированный) |
| `adj_plan_regional` | Уточненный план (региональный) |
| `adj_plan_growth_rate` | Темп роста плана |
| `execution_consolidated` | Исполнение (консолидированный) |
| `execution_regional` | Исполнение (региональный) |
| `growth_rate_regional` | Темп роста (регион) |
| `growth_rate_federal_district` | Темп роста (ФО) |
| `growth_rate_russia` | Темп роста (Россия) |
| `object_name` | Название региона |
| `okato` | Код ОКАТО |
| `oktmo` | Код ОКТМО |
| `object_level` | Уровень объекта |

## GitHub Actions

Workflow автоматически запускается:
- **По расписанию:** 5-го числа каждого месяца в 10:00 UTC
- **Вручную:** через интерфейс GitHub Actions

### Автоматический запуск

Workflow выполняет:
1. Скачивает существующие данные из последнего релиза
2. Проверяет доступность новых месяцев
3. Загружает новые данные и объединяет с существующими
4. Сохраняет в форматах Parquet, CSV, Excel
5. Загружает в S3 (если настроено)
6. Создает новый GitHub Release с файлами данных

### Ручной запуск

1. Перейдите в **Actions** → **Update Budget Data**
2. Нажмите **Run workflow**
3. Выберите параметры:
   - `data_type`: тип данных (all/income/expense)
   - `date_from`: начальная дата (опционально)
   - `date_to`: конечная дата (опционально)

## Конфигурация

### Переменные окружения для S3

| Переменная | Описание |
|------------|----------|
| `S3_BUCKET` | Название бакета |
| `S3_ACCESS_KEY` | Access Key |
| `S3_SECRET_KEY` | Secret Key |
| `S3_ENDPOINT_URL` | URL эндпоинта (для не-AWS) |
| `S3_REGION` | Регион (по умолчанию: us-east-1) |

### GitHub Secrets

Для работы GitHub Actions настройте следующие секреты в репозитории:
- `S3_BUCKET`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_ENDPOINT_URL`
- `S3_REGION`

Подробная инструкция: [GITHUB_SETUP.md](GITHUB_SETUP.md)

## Структура проекта

```
├── .github/
│   └── workflows/
│       └── update_budgets.yml    # GitHub Actions workflow
├── data/
│   ├── external/                 # Исходные данные
│   ├── processed/                # Обработанные данные
│   └── raw/                      # Сырые данные
├── notebooks/
│   ├── test_budgets_library.ipynb  # Тестовый notebook
│   └── EBT_—_budgets_for_updates.ipynb  # Исходный notebook
├── src/
│   └── budgets/
│       ├── __init__.py           # Экспорты пакета
│       ├── api.py                # API взаимодействие
│       ├── config.py             # Конфигурация
│       ├── expense.py            # Загрузчик расходов
│       ├── income.py             # Загрузчик доходов
│       ├── main.py               # CLI и BudgetUpdater
│       ├── normalizer.py         # Нормализация регионов
│       └── storage.py            # Хранение данных
├── requirements.txt
├── setup.py
└── README.md
```

## Лицензия

MIT
