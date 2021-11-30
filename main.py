import copy
import logging
import os
import time

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable

POPULAR_LANGUAGES = [
    ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано',
     'Средняя зарплата'],
    ['Python', 0, 0, 0],
    ['Java', 0, 0, 0],
    ['Javascript', 0, 0, 0],
    ['PHP', 0, 0, 0],
    ['C++', 0, 0, 0],
    ['C#', 0, 0, 0],
    ['C', 0, 0, 0],
    ['Go', 0, 0, 0]
    ]


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
    filename='logs.log',
    filemode='w',
    )


def get_amount_of_hh_vacancies(language, page=0, per_page=20):
    params = {
        'text': language,
        'page': page,
        'per_page': per_page,
        'area': 1
    }
    req = requests.get('https://api.hh.ru/vacancies', params=params)
    req.raise_for_status()
    return req.json()


def get_amount_sj_vacancies(profession, sj_key):
    headers = {
        'X-Api-App-Id': sj_key
    }
    params = {
        'keyword': profession,
        'town': 'Москва',
    }
    url = 'https://api.superjob.ru/2.0/vacancies/'
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_for_hh(vacancy):
    vacancy_salary = vacancy['salary']
    if not vacancy_salary or vacancy_salary['currency'] != 'RUR':
        return None
    if not vacancy_salary['from'] and not vacancy_salary['to']:
        return None
    if not vacancy_salary['from']:
        return vacancy_salary['to']*0.8
    elif not vacancy_salary['to']:
        return vacancy_salary['from']*1.2
    else:
        return (vacancy_salary['from']+vacancy_salary['to'])/2


def predict_rub_salary_for_sj(vacancy):
    if not vacancy['payment_from'] and not vacancy['payment_to']:
        return None
    if not vacancy['payment_from']:
        return vacancy['payment_to']*0.8
    elif not vacancy['payment_to']:
        return vacancy['payment_from']*1.2
    else:
        return (vacancy['payment_from'] + vacancy['payment_to'])/2


def show_all_vacancy(language):
    response_hh_api = get_amount_of_hh_vacancies(language)
    python_vacancy = []
    python_vacancy += response_hh_api['items']
    pages = response_hh_api['pages']
    if pages > 100:  # из расчета 20 вакасий на страницу(глубина <= 2000)
        pages = 100
    for page in range(1, pages):
        response_hh_api = get_amount_of_hh_vacancies(language, page)
        python_vacancy += response_hh_api['items']
        time.sleep(1)
    logging.info(python_vacancy)
    return (python_vacancy, response_hh_api['found'])


if __name__ == "__main__":
    load_dotenv()
    sj_key = os.getenv('SUPERJOB_KEY')
    hh_table_data = copy.deepcopy(POPULAR_LANGUAGES)
    sj_table_data = copy.deepcopy(POPULAR_LANGUAGES)

    # Обработка данных HH.ru
    for programm_lang in hh_table_data:
        if type(programm_lang[1]) == str:
            continue
        all_vacancy_and_found = show_all_vacancy(programm_lang[0])
        all_hh_vacancies = all_vacancy_and_found[0]
        vacancies_processed_hh = 0
        average_salary_hh = 0
        vacancies_found_hh = all_vacancy_and_found[1]
        for hh_vacancy in all_hh_vacancies:
            salary = predict_rub_salary_for_hh(hh_vacancy)
            if salary:
                vacancies_processed_hh += 1
                average_salary_hh += salary
        average_salary_hh = average_salary_hh/vacancies_processed_hh

        programm_lang[1] = vacancies_processed_hh
        programm_lang[2] = int(vacancies_found_hh)
        programm_lang[3] = int(average_salary_hh)
        logging.info(f'hh {hh_table_data}')

    # Обработка данных API SuperJob
    for programming_lang in sj_table_data:
        if type(programming_lang[1]) == str:
            continue
        sj_response = get_amount_sj_vacancies(programming_lang[0], sj_key)
        all_sj_vacancies = sj_response['objects']
        vacancies_processed = 0
        average_salary = 0
        vacancies_found = sj_response['total']
        for sj_vacancy in all_sj_vacancies:
            salary = predict_rub_salary_for_sj(sj_vacancy)
            if salary:
                vacancies_processed += 1
                average_salary += salary
            time.sleep(1)
        average_salary = average_salary / vacancies_processed

        programming_lang[1] = vacancies_processed
        programming_lang[2] = int(vacancies_found)
        programming_lang[3] = int(average_salary)
        logging.info(f'sj {sj_table_data}')

    # Вывод данных в виде таблиц
    sj_table = AsciiTable(sj_table_data, 'SuperJob Moscow')
    print(sj_table.table)

    hh_table = AsciiTable(hh_table_data, 'HH Moscow')
    print(hh_table.table)
