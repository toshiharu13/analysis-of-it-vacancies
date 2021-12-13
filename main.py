import logging
import os
import time

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def fetch_hh_vacancies(language, moscow, page=0, per_page=20):
    params = {
        'text': language,
        'page': page,
        'per_page': per_page,
        'area': moscow
    }
    req = requests.get('https://api.hh.ru/vacancies', params=params)
    req.raise_for_status()
    return req.json()


def fetch_sj_vacancies(language, sj_api_key, page=0, count=20):
    headers = {
        'X-Api-App-Id': sj_api_key
    }
    params = {
        'keyword': language,
        'page': page,
        'count': count,
        'town': 'Москва',

    }
    url = 'https://api.superjob.ru/2.0/vacancies/'
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def predict_salary(field_from, field_to):
    if not field_from and not field_to:
        return None
    if not field_from:
        return field_to * 0.8
    elif not field_to:
        return field_from * 1.2
    else:
        return (field_from + field_to) / 2


def predict_rub_salary_for_hh(vacancy):
    vacancy_salary = vacancy['salary']
    if not vacancy_salary:
        return None
    salary_from = vacancy_salary['from']
    salary_to = vacancy_salary['to']
    if not vacancy_salary or vacancy_salary['currency'] != 'RUR':
        return None
    return predict_salary(salary_from, salary_to)


def prepare_salary_to_table(
        programm_lang, vacancies_found, vacancies_processed, average_salary,
        table_vacancies_info):
    if not table_vacancies_info:
        table_vacancies_info.append(
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано',
         'Средняя зарплата'],
        )
    table_vacancies_info.append(
        [programm_lang, vacancies_found, vacancies_processed, average_salary])



def fetch_all_pages_hh_vacancy(language, moscow):
    hh_api_response = fetch_hh_vacancies(language, moscow)
    all_lang_vacancies = []
    all_lang_vacancies += hh_api_response['items']
    pages = hh_api_response['pages']
    time.sleep(1)
    for page in range(1, pages):
        hh_api_response = fetch_hh_vacancies(language, moscow, page)
        all_lang_vacancies += hh_api_response['items']
        time.sleep(2)
    return all_lang_vacancies, hh_api_response['found']


def fetch_all_pages_sj_vacancy(language, sj_api_key):
    api_response = fetch_sj_vacancies(language, sj_api_key)
    all_lang_vacancies = []
    all_lang_vacancies += api_response['objects']
    count_vacancies = api_response['total']
    pages = count_vacancies // 20
    time.sleep(1)
    if pages <= 1:
        return all_lang_vacancies, api_response['found']
    for page in range(1, pages):
        api_response = fetch_sj_vacancies(language, sj_api_key, page)
        all_lang_vacancies += api_response['objects']
        time.sleep(2)
    return all_lang_vacancies, count_vacancies


def get_average_salary_and_vacancy_processed_hh(all_vacancies):
    vacancies_processed = 0
    average_salary = 0
    for vacancy in all_vacancies:
        salary = predict_rub_salary_for_hh(vacancy)
        if salary:
            vacancies_processed += 1
            average_salary += salary
    average_salary = int(average_salary / vacancies_processed)
    return average_salary, vacancies_processed


def get_average_salary_and_vacancy_processed_sj(all_vacancies):
    vacancies_processed = 0
    average_salary = 0
    for vacancy in all_vacancies:
        salary_from = vacancy['payment_from']
        salary_to = vacancy['payment_to']
        salary = predict_salary(salary_from, salary_to)
        if salary:
            vacancies_processed += 1
            average_salary += salary
        time.sleep(1)
    average_salary = int(average_salary / vacancies_processed)
    return average_salary, vacancies_processed


if __name__ == "__main__":
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
    moscow = 1
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
        filename='logs.log',
        filemode='w',
    )
    load_dotenv()

    sj_api_key = os.getenv('SUPERJOB_KEY')
    hh_table_vacancies_info = []
    sj_table_vacancies_info = []

    for programm_lang in POPULAR_LANGUAGES:
        all_hh_vacancies, hh_vacancies_found = fetch_all_pages_hh_vacancy(programm_lang, moscow)
        hh_average_salary, hh_vacancies_processed = get_average_salary_and_vacancy_processed_hh(all_hh_vacancies)

        prepare_salary_to_table(
            programm_lang, hh_vacancies_found, hh_vacancies_processed,
            hh_average_salary,
            hh_table_vacancies_info)
        logging.info(f'hh {hh_table_vacancies_info}')

    for programming_lang in POPULAR_LANGUAGES:
        all_sj_vacancies, sj_vacancies_found = fetch_all_pages_sj_vacancy(programming_lang,sj_api_key)
        sj_average_salary, sj_vacancies_processed = get_average_salary_and_vacancy_processed_sj(all_sj_vacancies)

        prepare_salary_to_table(
            programming_lang, sj_vacancies_found, sj_vacancies_processed,
            sj_average_salary, sj_table_vacancies_info)
        logging.info(f'sj {sj_table_vacancies_info}')

    sj_table = AsciiTable(sj_table_vacancies_info, 'SuperJob Moscow')
    print(sj_table.table)

    hh_table = AsciiTable(hh_table_vacancies_info, 'HH Moscow')
    print(hh_table.table)
