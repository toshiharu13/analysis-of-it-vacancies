import logging
# Библиотека для работы с HTTP-запросами. Будем использовать ее для обращения к API HH
import requests

# Пакет для удобной работы с данными в формате json
import json

# Модуль для работы со значением времени
import time

# Модуль для работы с операционной системой. Будем использовать для работы с файлами
import os, shutil
import pandas as pd
# Библиотека для работы с СУБД
from sqlalchemy import engine as sql


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
    filename='logs.lod',
    filemode='w',
    )


def getPage(page=0):
    """
    Создаем метод для получения страницы со списком вакансий.
    Аргументы:
        page - Индекс страницы, начинается с 0. Значение по умолчанию 0, т.е. первая страница
    """

    # Справочник для параметров GET-запроса
    params = {
        'text': 'NAME:Backend Python разработчик',
        # Текст фильтра. В имени должно быть слово "Backend Python разработчик"
        'area': 2,  # Поиск ощуществляется по вакансиям города Петребург
        'page': page,  # Индекс страницы поиска на HH
        'per_page': 5  # Кол-во вакансий на 1 странице
    }

    # Посылаем запрос к API
    req = requests.get('https://api.hh.ru/vacancies', params)
    return req.json()


# Считываем первые 1000 вакансий
for page in range(0, 1):
    jsObj = getPage(page)

    # Задаём {путь до текущего документа со скриптом}\docs
    # Имя(число) файла зависит от количества имеющихся в папке
    # Будущему файлу с информацией запроса
    nextFileName = './docs/pagination/{}.json'.format(len(os.listdir('./docs/pagination')))

    # Создаем файл, записываем в него ответ запроса, после закрываем
    with open(nextFileName, mode='w', encoding='utf8') as f:
        f.write(json.dumps(jsObj, ensure_ascii=False))

    # Проверка на последнюю страницу, если вакансий меньше 1000
    if (jsObj['pages'] - page) <= 1:
        break

    # Необязательная задержка, но чтобы не нагружать сервисы hh, оставим .5 сек мы может подождать
    time.sleep(0.5)

logging.info('Старницы поиска собраны')

# Получаем перечень ранее созданных файлов со списком вакансий и проходимся по нему в цикле
for fl in os.listdir('./docs/pagination'):

    # Открываем файл, читаем его содержимое, закрываем файл
    with open('./docs/pagination/{}'.format(fl), encoding='utf8') as f:
        jsonText = f.read()

    # Преобразуем полученный текст в объект справочника
    jsonObj = json.loads(jsonText)

    # Получаем и проходимся по непосредственно списку вакансий
    for v in jsonObj['items']:
        # Обращаемся к API и получаем детальную информацию по конкретной вакансии
        req = requests.get(v['url']).json()
        #data = req.content.decode()
        #req.close()

        # Создаем файл в формате json с идентификатором вакансии в качестве названия
        # Записываем в него ответ запроса и закрываем файл
        fileName = './docs/vacancies/{}.json'.format(v['id'])
        with open(fileName, mode='w', encoding='utf8') as f:
            f.write(json.dumps(req, ensure_ascii=False))
            # f.write(json.dumps(jsObj, ensure_ascii=False))

        time.sleep(0.5)

logging.info('Вакансии собраны')

# Создаем списки для столбцов таблицы vacancies
IDs = []  # Список идентификаторов вакансий
names = []  # Список наименований вакансий
descriptions = []  # Список описаний вакансий
skills_id = []  # Список идентификаторов скилов

# Создаем списки для столбцов таблицы skills
skills_name = []  # Список названий навыков
skills_vac = []  # Список идентификаторов скилов

# Проходимся по всем файлам в папке vacancies
for fl in os.listdir('./docs/vacancies'):

    # Открываем, читаем
    with open('./docs/vacancies/{}'.format(fl), encoding='utf8') as f:
        jsonText = f.read()

    # Текст файла переводим в справочник
    jsonObj = json.loads(jsonText)

    # Заполняем списки для таблиц
    IDs.append(jsonObj['id'])
    names.append(jsonObj['name'])
    descriptions.append(jsonObj['description'])

    # Т.к. навыки хранятся в виде массива, то проходимся по нему циклом
    for skl in jsonObj['key_skills']:
        skills_vac.append(jsonObj['id'])
        skills_name.append(skl['name'])


# Создадим соединение с БД
eng = sql.create_engine(
    'postgresql://testuser:testuser@127.0.0.1:5432/testdb')
conn = eng.connect()

# Создаем пандосовский датафрейм, который затем сохраняем в БД в таблицу vacancies
df = pd.DataFrame({'hh_id': IDs, 'name': names, 'discription': descriptions})
df.to_sql('vacancies', conn, schema='public', if_exists='append', index=False)

# Тоже самое, но для таблицы skills
df = pd.DataFrame({'vacancies_id': skills_vac, 'skills': skills_name})
df.to_sql('skills', conn, schema='public', if_exists='append', index=False)

# Закрываем соединение с БД
conn.close()

logging.info('Вакансии загружены в БД')
# чистим временные файлы
logging.info('чистка файлов')
shutil.rmtree('./docs/pagination')
shutil.rmtree('./docs/vacancies')
os.mkdir('./docs/pagination')
os.mkdir('./docs/vacancies')
logging.info('завешаем работу')
