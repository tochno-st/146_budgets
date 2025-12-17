# Инструкция по настройке GitHub

## 1. Создание репозитория

```bash
cd /path/to/146_budgets
git init
git add .
git commit -m "Initial commit: Budget data updater library"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## 2. Настройка GitHub Secrets

Для загрузки данных в S3 необходимо настроить секреты.

### Шаги:

1. Откройте репозиторий на GitHub
2. Перейдите в **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Добавьте следующие секреты:

| Название | Описание | Пример |
|----------|----------|--------|
| `S3_BUCKET` | Название S3 бакета | `tochno-st-catalog` |
| `S3_ACCESS_KEY` | Access Key ID | `AKIAIOSFODNN7EXAMPLE` |
| `S3_SECRET_KEY` | Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `S3_ENDPOINT_URL` | URL S3 эндпоинта (для Yandex/MinIO) | `https://storage.yandexcloud.net` |
| `S3_REGION` | Регион | `ru-central1` |

### Для разных провайдеров:

**AWS S3:**
- `S3_ENDPOINT_URL`: не требуется (оставьте пустым)
- `S3_REGION`: `us-east-1`, `eu-west-1`, etc.

**Yandex Object Storage:**
- `S3_ENDPOINT_URL`: `https://storage.yandexcloud.net`
- `S3_REGION`: `ru-central1`

**MinIO:**
- `S3_ENDPOINT_URL`: `https://your-minio-server.com`
- `S3_REGION`: `us-east-1`

## 3. Включение GitHub Actions

1. Перейдите в **Actions** в репозитории
2. Если Actions отключены, нажмите **Enable GitHub Actions**
3. Workflow `Update Budget Data` появится в списке

## 4. Запуск вручную

1. Перейдите в **Actions** → **Update Budget Data**
2. Нажмите **Run workflow**
3. Заполните параметры:

   | Параметр | Описание |
   |----------|----------|
   | `data_type` | `all` - все данные, `income` - только доходы, `expense` - только расходы |
   | `date_from` | Начальная дата в формате YYYY-MM (например: `2024-01`). Оставьте пустым для автоопределения |
   | `date_to` | Конечная дата в формате YYYY-MM. Оставьте пустым для загрузки до последнего доступного месяца |

4. Нажмите зеленую кнопку **Run workflow**

## 5. Автоматический запуск

Workflow настроен на автоматический запуск **5-го числа каждого месяца в 10:00 UTC**.

Расписание можно изменить в файле `.github/workflows/update_budgets.yml`:

```yaml
on:
  schedule:
    # Cron: минуты часы день_месяца месяц день_недели
    - cron: '0 10 5 * *'  # 5-е число, 10:00 UTC
```

Примеры cron выражений:
- `'0 10 1 * *'` - 1-е число каждого месяца в 10:00 UTC
- `'0 6 * * 1'` - каждый понедельник в 06:00 UTC
- `'0 0 15 * *'` - 15-е число каждого месяца в полночь UTC

## 6. Просмотр результатов

### Релизы

После успешного выполнения workflow создается новый Release:
1. Перейдите в **Releases** на странице репозитория
2. Скачайте файлы данных (parquet, csv, xlsx)

### Артефакты

Данные также сохраняются как артефакты workflow:
1. Перейдите в **Actions** → выберите выполненный workflow
2. В разделе **Artifacts** скачайте `budget-data-vYYYY.MM.DD`

### S3

Если настроены секреты S3, данные загружаются в:
```
s3://tochno-st-catalog/FinKazna/data_budgets_146/vYYYY.MM.DD/budget_income.parquet
s3://tochno-st-catalog/FinKazna/data_budgets_146/vYYYY.MM.DD/budget_income.csv
s3://tochno-st-catalog/FinKazna/data_budgets_146/vYYYY.MM.DD/budget_income.xlsx
s3://tochno-st-catalog/FinKazna/data_budgets_146/vYYYY.MM.DD/budget_expense.parquet
...
```

## 7. Устранение неполадок

### Workflow не запускается автоматически

- Убедитесь, что в репозитории есть активность за последние 60 дней
- Проверьте, что Actions включены в настройках репозитория

### Ошибка загрузки в S3

- Проверьте правильность секретов
- Убедитесь, что бакет существует и доступен
- Проверьте права доступа ключа (нужны права на `PutObject`)

### Нет новых данных

- API может не иметь данных за текущий месяц
- Попробуйте указать конкретный период через `date_from` и `date_to`

### Просмотр логов

1. Перейдите в **Actions**
2. Выберите выполненный workflow
3. Нажмите на job **update-data**
4. Разверните нужный шаг для просмотра логов

## 8. Локальное тестирование

Перед push в GitHub можно протестировать локально:

```bash
# Активировать виртуальное окружение
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить обновление (тест с одним месяцем)
cd src
python -m budgets.main --type income --date-from 2024-01 --date-to 2024-01 --output-dir ../data/processed
```

## 9. Настройка уведомлений

Для получения уведомлений о статусе workflow:

1. Перейдите в **Settings** → **Notifications**
2. Включите **Actions** уведомления
3. Выберите способ: Email, Web, Mobile

