import datetime
import uuid

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List, Union
from pydantic import BaseModel


class Task(BaseModel):
    name: str = 'NEW_TASK'
    date: datetime.datetime = datetime.datetime.now()
    status: str = 'PENDING'
    id: uuid.UUID = uuid.uuid4()


app = FastAPI()


tasks = [
    {'name': 'Съемка Александровского моста', 'date': datetime.datetime(2022, 11, 13, 15, 16),
     'status': 'PENDING', 'id': '123'},
    {'name': 'Съемка неизвестного моста', 'date': datetime.datetime(2022, 11, 11, 15, 16),
     'status': 'PENDING', 'id': '218'},
    {'name': 'Съемка Кремлевского моста', 'date': datetime.datetime(2022, 11, 14, 11, 46),
     'status': 'SUCCESS', 'id': '126'},
    {'name': 'Съемка нового моста', 'date': datetime.datetime(2022, 11, 14, 16, 00),
     'status': 'IN_PROGRESS', 'id': '136'},
]


@app.post('/login')
def login():
    return {'status': 'success'}


@app.post('/logout')
def login():
    return {'status': 'success'}


@app.get('/content/')
def main_content():
    content = 'Разрабатываемый интеллектуальный дефектоскоп должен в дальнейшем стать программной частью ' \
              'гидроакустического комплекса на базе многофункционального автономного необитаемого ' \
              'надводно-подводного интеллектуального аппарата «ГЛАЙДЕРОН», ' \
              'разработанного ООО НПК «Сетецентрические Платформы» и САМГТУ'
    return {'students': content}


def task_check(task_id):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail='Task Not Found')


@app.get('/tasks/')
def tasks_list(min: Optional[int] = None, max: Optional[int] = None):

    if min and max:
        filtered_tasks = list(
            filter(lambda task: max >= task['id'] >= min, tasks)
        )

        return {'tasks': filtered_tasks}

    return {'tasks': tasks}


@app.get('/tasks/{task_id}')
def user_detail(task_id: int):
    task_check(task_id)
    return {'task': tasks[task_id]}


@app.post('/tasks')
def task_add(task: Task):
    tasks.append(task)

    return {
        'task': tasks[-1],
        # 'filename': file.filename,

            # "filenames": [file.filename for file in files]
            }
