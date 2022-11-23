**Stub-backend for rzd-project.**

[![Docker publish](https://github.com/dnovichkov/rzd_backend/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/dnovichkov/rzd_backend/actions/workflows/docker-publish.yml)

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
Docker using:
```
docker -v pull ghcr.io/dnovichkov/dnovichkov/rzd_backend:main
docker run -p 8000:8000 ghcr.io/dnovichkov/dnovichkov/rzd_backend:main
```
