import logging
# Библиотека для работы с HTTP-запросами. Будем использовать ее для обращения к API HH
import requests

# Пакет для удобной работы с данными в формате json
import json

# Модуль для работы со значением времени
import time

# Модуль для работы с операционной системой. Будем использовать для работы с файлами
import os


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
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
        'per_page': 100  # Кол-во вакансий на 1 странице
    }

    # Посылаем запрос к API
    req = requests.get('https://api.hh.ru/vacancies', params)
    return req.json()


# Считываем первые 1000 вакансий
for page in range(0, 10):
    jsObj = getPage(page)

    # Задаём {путь до текущего документа со скриптом}\docs
    # Имя(число) файла зависит от количества имеющихся в папке
    # Будущему файлу с информацией запроса
    nextFileName = './docs/{}.json'.format(len(os.listdir('./docs')))

    # Создаем файл, записываем в него ответ запроса, после закрываем
    with open(nextFileName, mode='w', encoding='utf8') as f:
        f.write(json.dumps(jsObj, ensure_ascii=False))

    # Проверка на последнюю страницу, если вакансий меньше 2000
    if (jsObj['pages'] - page) <= 1:
        break

    # Необязательная задержка, но чтобы не нагружать сервисы hh, оставим. 5 сек мы может подождать
    time.sleep(5)

logging.info('Старницы поиска собраны')