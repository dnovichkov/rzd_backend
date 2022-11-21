**Stub-backend for rzd-project.**

Activate virtual environment.
Command for Windows:
```
python -m venv venv
call venv/scripts/activate.bat
```

Install requirements:
```
pip install -r requirements.txt
```

Run application:
```
uvicorn app:app --reload
```