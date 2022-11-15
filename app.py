import datetime
import uuid
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Query, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional, List, Union


class Task(BaseModel):
    name: str = 'NEW_TASK'
    date: datetime.datetime = datetime.datetime.now()
    status: str = None
    id: uuid.UUID = None


class LoginData(BaseModel):
    user: str = 'some_user'
    password: str = 'some_password'


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
def login(login: LoginData):
    """
    Возвращает статус логина
    """
    return {'status': 'success', 'user': login.user}


@app.post('/logout')
def logout():
    return {'status': 'success'}


@app.get('/content/')
def main_content():
    """
    Возвращает контент для главной страницы
    """
    content = 'Разрабатываемый интеллектуальный дефектоскоп должен в дальнейшем стать программной частью ' \
              'гидроакустического комплекса на базе многофункционального автономного необитаемого ' \
              'надводно-подводного интеллектуального аппарата «ГЛАЙДЕРОН», ' \
              'разработанного ООО НПК «Сетецентрические Платформы» и САМГТУ'
    return {'content': content}


def task_check(task_id):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail='Task Not Found')


@app.get('/tasks/')
def tasks_list(min: Union[int, None] = Query(None, description="минимальный номер задачи"),
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
def task_detail(task_id: int):
    task_check(task_id)
    return {'task': tasks[task_id]}


@app.post('/tasks')
def task_add(
    name: str = Form(..., description="Наименование задачи"),
    datetime: datetime.datetime = Form(datetime.datetime.now(), description="Дата-время съемки"),
    files: List[UploadFile] = File(...),
):
    task = Task(name=name, datetime=datetime, status='IN_PROGRESS', id=uuid.uuid4())
    tasks.append(task)
    return {
        'task': tasks[-1],
        "filenames": [file.filename for file in files]
    }
