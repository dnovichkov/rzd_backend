import datetime
import logging
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Query, Form
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Union
import aiofiles


class Task(BaseModel):
    name: str = 'NEW_TASK'
    date: datetime.datetime = datetime.datetime.now()
    status: str = None
    id: str = None
    files: List[str] = []


class LoginData(BaseModel):
    user: str = Form(default='some_user', description="Логин пользователя")
    password: str = Form(default='some_password', description="Пароль пользователя")


app = FastAPI()


tasks = [
    {'name': 'Съемка Александровского моста', 'date': datetime.datetime(2022, 11, 13, 15, 16),
     'status': 'PENDING', 'id': '123', 'files': ['frame1033.jpg', 'frame1099.jpg']},
    {'name': 'Съемка неизвестного моста', 'date': datetime.datetime(2022, 11, 11, 15, 16),
     'status': 'PENDING', 'id': '218', 'files': ['frame1221.jpg']},
    {'name': 'Съемка Кремлевского моста', 'date': datetime.datetime(2022, 11, 14, 11, 46),
     'status': 'SUCCESS', 'id': '126', 'files': ['frame1379.jpg']},
    {'name': 'Съемка нового моста', 'date': datetime.datetime(2022, 11, 14, 16, 00),
     'status': 'IN_PROGRESS', 'id': '136', 'files': []},
]


@app.post('/login')
async def login(login: LoginData):
    """
    Возвращает статус логина
    """
    return {'status': 'success', 'user': login.user}


@app.post('/logout')
async def logout():
    return {'status': 'success'}


@app.get('/content')
async def main_content():
    """
    Возвращает контент для главной страницы
    """
    content = 'Разрабатываемый интеллектуальный дефектоскоп должен в дальнейшем стать программной частью ' \
              'гидроакустического комплекса на базе многофункционального автономного необитаемого ' \
              'надводно-подводного интеллектуального аппарата «ГЛАЙДЕРОН», ' \
              'разработанного ООО НПК «Сетецентрические Платформы» и САМГТУ'
    return {'content': content}


def get_tasks_by_id():
    tasks_by_id = {task.get('id'): task for task in tasks}
    return tasks_by_id


@app.get('/tasks')
async def tasks_list(min: Union[int, None] = Query(None, description="минимальный номер задачи"),
               max: Optional[int] = Query(None, description="максимальный номер задачи")):
    """
    Возвращает список задач
    """
    if min and max:
        if min < 0 or max > len(tasks):
            print(f'bad request: {min=}, {max=}')
            return {'count': len(tasks), 'tasks': tasks}
        filtered_tasks = tasks[min: max]

        return {'count': len(filtered_tasks), 'tasks': filtered_tasks}

    return {'count': len(tasks), 'tasks': tasks}


@app.get('/tasks/{task_id}')
async def task_detail(task_id: str):
    tasks_by_id = get_tasks_by_id()
    if task_id not in tasks_by_id:
        raise HTTPException(status_code=404, detail=f'Item is not found: {task_id}')
    return {'task': tasks_by_id[task_id]}


@app.post('/tasks')
async def task_add(
    name: str = Form(..., description="Наименование задачи"),
    date_time: datetime.datetime = Form(datetime.datetime.now(), description="Дата-время съемки"),
    files: List[UploadFile] = File(...),
):
    for in_file in files:
        out_file_path = f'images/{in_file.filename}'
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            content = await in_file.read()
            await out_file.write(content)
    task = {'name': name, 'date': date_time, 'status': 'IN_PROGRESS', 'id': str(uuid.uuid4()),
            'files': [file.filename for file in files]}
    tasks.append(task)
    return {
        'task': tasks[-1],
        "filenames": [file.filename for file in files]
    }


@app.get('/images/{filename}')
async def get_image(filename: str):
    logging.debug(f'Запросили снимок {filename}')
    filepath = Path(f'images/{filename}')
    if filepath.is_file():
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail=f'Item is not found: {filename}')
