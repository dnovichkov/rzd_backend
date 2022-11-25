import datetime
import logging
import os
import uuid
from enum import Enum
from typing import Optional, List, Union

import aiofiles
from fastapi import FastAPI, HTTPException, File, UploadFile, Query, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class Box(BaseModel):
    x: float
    y: float
    height: float
    width: float


class Result(BaseModel):
    defect: str
    presence: float
    box: Box


class ImageResult(BaseModel):
    id: str
    status: TaskStatus
    result: List[Result]


class Task(BaseModel):
    name: str = 'NEW_TASK'
    date: datetime.datetime = datetime.datetime.now()
    status: TaskStatus = TaskStatus.PENDING
    id: str = None
    files: List[str] = []
    results: List[ImageResult] = []


class TaskResponse(BaseModel):
    task: Task


class TaskListResponse(BaseModel):
    count: int
    tasks: List[Task]


class LoginData(BaseModel):
    user: str = Form(default='some_user', description="Логин пользователя")
    password: str = Form(default='some_password', description="Пароль пользователя")


app = FastAPI()

task_res = Result(defect='UglyDefect', presence=0.798, box=Box(x=0.453, y=0.467, height=0.1, width=0.1924024))
image_res = ImageResult(
                 id='jkhk320',
                 status=TaskStatus.COMPLETED,
                 result=[task_res]
                 )

tasks = [
    Task(name='Съемка Александровского моста', date=datetime.datetime(2022, 11, 13, 15, 16),
         status=TaskStatus.PENDING, id='123', files=['frame1033.jpg', 'frame1099.jpg']),
    Task(name='Съемка неизвестного моста', date=datetime.datetime(2022, 11, 11, 15, 16),
         status=TaskStatus.PENDING, id='218', files=['frame1221.jpg']),
    Task(name='Съемка Кремлевского моста', date=datetime.datetime(2022, 11, 14, 11, 46),
         status=TaskStatus.COMPLETED, id='126', files=['frame1379.jpg'],
         results=
         [
             ImageResult(
                 id='jkhk320',
                 status=TaskStatus.COMPLETED,
                 result=[Result(defect='UglyDefect', presence=0.798,
                                box=Box(x=0.453, y=0.467, height=0.1, width=0.1924024))]
             ),
         ]
         ),
    Task(name='Съемка нового моста', date=datetime.datetime(2022, 11, 14, 16, 00),
         status=TaskStatus.FAILED, id='136', files=[]),
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
    tasks_by_id = {task.id: task for task in tasks}
    return tasks_by_id


@app.get('/tasks', response_model=TaskListResponse)
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

        return TaskListResponse(count=len(filtered_tasks), tasks=filtered_tasks)

    return TaskListResponse(count=len(tasks), tasks=tasks)


@app.get('/tasks/{task_id}', response_model=TaskResponse)
async def task_detail(task_id: str):
    tasks_by_id = get_tasks_by_id()
    if task_id not in tasks_by_id:
        raise HTTPException(status_code=404, detail=f'Item is not found: {task_id}')
    task = tasks_by_id[task_id]
    return TaskResponse(task=task)


@app.post('/tasks', response_model=TaskResponse)
async def task_add(
    name: str = Form(..., description="Наименование задачи"),
    date_time: datetime.datetime = Form(datetime.datetime.now(), description="Дата-время съемки"),
    files: List[UploadFile] = File(...),
):
    unique_id = str(uuid.uuid4())
    filenames = []
    for in_file in files:
        resulted_name = f'{unique_id}_{in_file.filename}'
        out_file_path = f'images/{resulted_name}'
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            content = await in_file.read()
            filenames.append(resulted_name)
            await out_file.write(content)
    task = Task(name=name, date=date_time,
                status=TaskStatus.PENDING, id=unique_id, files=filenames)
    tasks.append(task)
    return TaskResponse(task=task)


@app.get('/images/{filename}')
async def get_image(filename: str):
    logging.debug(f'Запросили снимок {filename}')
    base_path = 'images'
    full_path = os.path.normpath(os.path.join(base_path, filename))
    if not full_path.startswith(base_path):
        raise HTTPException(status_code=404, detail=f'Item is not found: {filename}')
    if os.path.isfile(full_path):
        return FileResponse(full_path)
    raise HTTPException(status_code=404, detail=f'Item is not found: {filename}')
