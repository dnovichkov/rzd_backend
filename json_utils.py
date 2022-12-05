import json
import datetime
import pathlib


def save_json(json_result, file_path: str, filename_prefix: str):
    json_file_name = filename_prefix + "_" + datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S") + "_.json"

    path = pathlib.Path(file_path)
    file_full_path = path / json_file_name
    path.mkdir(parents=True, exist_ok=True)

    with file_full_path.open("w", encoding='utf-8') as file:
        for chunk in json.JSONEncoder(indent=4, ensure_ascii=False).iterencode(json_result):
            file.write(chunk)
