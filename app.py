import datetime
import logging
import os
import uuid
from enum import Enum
from typing import Optional, List, Union

import aiofiles
from fastapi import FastAPI, HTTPException, File, UploadFile, Query, Form
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import requests
from defaultenv import env

from json_utils import save_json

DEFECT_NAMES = {
    'destruction of concrete': 'Разрушение бетона',
    'concrete leaching': 'Отсутствие бетонной кладки',
    'cracks': 'Трещина(ы)',
    'other defects': 'Прочие дефекты',
}


class TaskStatus(str, Enum):
    PENDING = 'В работе'
    COMPLETED = 'Завершено'
    FAILED = 'Ошибка'


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
    filename: str
    resulted_image: str = ''
    id: str
    status: TaskStatus
    result: List[Result]


# from pydantic.json import timedelta_isoformat

class Task(BaseModel):
    name: str = 'NEW_TASK'
    date: datetime.datetime = datetime.datetime.now()
    status: TaskStatus = TaskStatus.PENDING
    id: str = None
    results: List[ImageResult] = []

    @validator("date")
    def datetime_to_string(cls, v):
        return v.isoformat()


class TaskResponse(BaseModel):
    task: Task


class TaskListResponse(BaseModel):
    count: int
    tasks: List[Task]


class LoginData(BaseModel):
    user: str = Form(default='some_user', description="Логин пользователя")
    password: str = Form(default='some_password', description="Пароль пользователя")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


tasks = []


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
    resulted_tasks = tasks
    if min and max:
        if min < 0 or max > len(tasks):
            print(f'bad request: {min=}, {max=}')
            return {'count': len(tasks), 'tasks': tasks}
        filtered_tasks = tasks[min: max]
        resulted_tasks = filtered_tasks
    image_service_url = env('IMAGE_SERVICE_URL')
    status_url = image_service_url + 'api/media-processing/images'
    task_data = requests.session().get(status_url).json()
    taks_statuses = {rec.get('id'): rec.get('status') for rec in task_data}
    # print(taks_statuses)
    for task in tasks:
        if not task.results:
            continue
        if task.status == TaskStatus.COMPLETED:
            continue
        was_all_completed = True
        for _file in task.results:
            file_id = _file.id
            if taks_statuses.get(file_id) == 'completed':
                _file.status = TaskStatus.COMPLETED
                detailed_result_url = status_url + '/' + file_id
                metadata = requests.session().get(detailed_result_url).json().get('result', {}).get('metadata')
                _file.resulted_image = detailed_result_url + '/download'
                for rec in metadata:
                    name = rec.get('class')
                    translated_name = DEFECT_NAMES.get(name, name)
                    presence = rec.get('presence')
                    x = rec.get('box', {}).get('x')
                    y = rec.get('box', {}).get('y')
                    width = rec.get('box', {}).get('width')
                    height = rec.get('box', {}).get('height')
                    defect_data = Result(defect=translated_name, presence=presence, box=Box(x=x, y=y, width=width, height=height))
                    _file.result.append(defect_data)
                # _file.result = requests.session().get(detailed_result_url).json().get('result', {}).get('metadata')
            else:
                was_all_completed = False
        if was_all_completed and task.results:
            task.status = TaskStatus.COMPLETED

    if min and max:
        if min < 0 or max > len(tasks):
            print(f'bad request: {min=}, {max=}')
            return {'count': len(tasks), 'tasks': tasks}
        resulted_tasks = tasks[min: max]

    save_json([task.dict() for task in tasks], 'tasks', 'task')

    return TaskListResponse(count=len(resulted_tasks), tasks=resulted_tasks)


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
    date_time: Union[datetime.datetime, datetime.date] = Form(datetime.datetime.now(), description="Дата-время съемки"),
    files: List[UploadFile] = File(...),
):
    if type(date_time) == datetime.date:
        date_time = datetime.datetime.combine(date_time, datetime.datetime.min.time())
    unique_id = str(uuid.uuid4())
    filenames = []
    for in_file in files:
        resulted_name = f'{unique_id}_{in_file.filename}'
        out_file_path = f'images/{resulted_name}'
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            content = await in_file.read()
            filenames.append(resulted_name)
            await out_file.write(content)

    image_service_url = env('IMAGE_SERVICE_URL')
    load_image_url = image_service_url + 'api/media-processing/images'
    results: List[ImageResult] = []
    for filename in filenames:
        out_file_path = f'images/{filename}'

        payload = {}
        files = [
            ('files', (filename,
                       open(out_file_path, 'rb'),
                       'image/jpeg'))
        ]
        headers = {}

        response = requests.request("POST", load_image_url, headers=headers, data=payload, files=files)

        logging.debug(response.status_code)
        resp_json = response.json()
        if not resp_json:
            print(response.content)
        else:
            image_id = resp_json[0].get('id', '')
            image_res = ImageResult(filename=filename, id=image_id, status=TaskStatus.PENDING, result=[])
            print(f'{filename=}, {image_id=}')
            results.append(image_res)
    task = Task(name=name, date=date_time,
                status=TaskStatus.PENDING, id=unique_id, results=results)
    tasks.append(task)
    return TaskResponse(task=task)


@app.delete('/tasks/{task_id}')
async def task_delete(task_id: str):
    """
    Удаляет задачу с указанным идентификатором
    :param task_id:
    :return:
    """
    tasks_by_id = get_tasks_by_id()
    if task_id not in tasks_by_id:
        raise HTTPException(status_code=404, detail=f'Item is not found: {task_id}')
    task = tasks_by_id[task_id]
    tasks.remove(task)
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
