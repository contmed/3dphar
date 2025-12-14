ATX Library — запуск

Требования
- Python 3.10+
- pip

Установка (venv)
Windows PowerShell:
1) python -m venv .venv
2) .\.venv\Scripts\Activate.ps1
3) pip install -r requirements.txt

macOS/Linux:
1) python3 -m venv .venv
2) source .venv/bin/activate
3) pip install -r requirements.txt

Данные
- Поместите файлы input_A.xlsx, categories.xlsx в корень проекта.

Запуск веб-приложения
Windows:
python app.py

macOS/Linux:
python3 app.py

Открыть в браузере
http://localhost:8000/

Примечания
- Матрица доступна по адресу /atx-matrix.
- Сгенерированные HTML-экспорты (matrix_output_*.html) игнорируются Git.