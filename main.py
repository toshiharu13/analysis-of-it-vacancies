import copy
import logging
import os
import time

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable

POPULAR_LANGUAGES = {
    'Python',
    'Java',
    'Javascript',
    'PHP',
    'C++',
    'C#',
    'C',
    'Go'
}


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


def predict_salary(block_salary_info, field_from, field_to):
    if not block_salary_info[field_from] and not block_salary_info[field_to]:
        return None
    if not block_salary_info[field_from]:
        return block_salary_info[field_to] * 0.8
    elif not block_salary_info[field_to]:
        return block_salary_info[field_from] * 1.2
    else:
        return (block_salary_info[field_from] + block_salary_info[field_to]) / 2


def predict_rub_salary_for_hh(vacancy):
    vacancy_salary = vacancy['salary']
    if not vacancy_salary or vacancy_salary['currency'] != 'RUR':
        return None
    return predict_salary(vacancy_salary, 'from', 'to')


def prepare_salary_to_table(
        programm_lang, vacancies_found, vacancies_processed, average_salary,
        table_data):
    if not table_data:
        table_data.append(
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано',
         'Средняя зарплата'],
        )
    table_data.append([programm_lang, vacancies_found, vacancies_processed, average_salary])



def show_all_vacancy(language):
    response_hh_api = get_amount_of_hh_vacancies(language)
    python_vacancy = []
    python_vacancy += response_hh_api['items']
    pages = response_hh_api['pages']
    time.sleep(1)
    if pages > 100:  # из расчета 20 вакасий на страницу(глубина <= 2000)
        pages = 100
    for page in range(1, 3):
        response_hh_api = get_amount_of_hh_vacancies(language, page)
        python_vacancy += response_hh_api['items']
        time.sleep(2)
    #logging.info(python_vacancy)
    return (python_vacancy, response_hh_api['found'])


if __name__ == "__main__":
    load_dotenv()
    sj_key = os.getenv('SUPERJOB_KEY')
    hh_table_data = []
    sj_table_data = []

    # Обработка данных HH.ru
    for programm_lang in POPULAR_LANGUAGES:
        all_vacancy_and_found = show_all_vacancy(programm_lang)
        all_hh_vacancies = all_vacancy_and_found[0]
        vacancies_processed_hh = 0
        average_salary_hh = 0
        vacancies_found_hh = all_vacancy_and_found[1]
        for hh_vacancy in all_hh_vacancies:
            salary = predict_rub_salary_for_hh(hh_vacancy)
            if salary:
                vacancies_processed_hh += 1
                average_salary_hh += salary
        average_salary_hh = int(average_salary_hh/vacancies_processed_hh)

        prepare_salary_to_table(
            programm_lang, vacancies_found_hh, vacancies_processed_hh,
            average_salary_hh,
            hh_table_data)
        logging.info(f'hh {hh_table_data}')

    # Обработка данных API SuperJob
    for programming_lang in POPULAR_LANGUAGES:
        sj_response = get_amount_sj_vacancies(programming_lang, sj_key)
        all_sj_vacancies = sj_response['objects']
        vacancies_processed = 0
        average_salary = 0
        vacancies_found = sj_response['total']
        for sj_vacancy in all_sj_vacancies:
            salary = predict_salary(sj_vacancy, 'payment_from', 'payment_to')
            if salary:
                vacancies_processed += 1
                average_salary += salary
            time.sleep(1)
        average_salary = int(average_salary / vacancies_processed)

        prepare_salary_to_table(
            programming_lang, vacancies_found, vacancies_processed,
            average_salary, sj_table_data)
        logging.info(f'sj {sj_table_data}')

    # Вывод данных в виде таблиц
    sj_table = AsciiTable(sj_table_data, 'SuperJob Moscow')
    print(sj_table.table)

    hh_table = AsciiTable(hh_table_data, 'HH Moscow')
    print(hh_table.table)
