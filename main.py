import logging
import os
import time
from itertools import count

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
    response = requests.get('https://api.hh.ru/vacancies', params=params)
    response.raise_for_status()
    return response.json()


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
    return (field_from + field_to) / 2


def predict_rub_salary_for_hh(vacancy):
    vacancy_salary = vacancy['salary']
    if not vacancy_salary or vacancy_salary['currency'] != 'RUR':
        return None
    salary_from = vacancy_salary['from']
    salary_to = vacancy_salary['to']

    return predict_salary(salary_from, salary_to)


def build_vacancy_stats_table(table_vacancies, table_title):
    final_table = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    final_table.extend(table_vacancies)
    return AsciiTable(final_table, table_title)


def fetch_all_hh_vacancy_pages(language, moscow):
    all_lang_vacancies = []
    for page in count():
        hh_api_response = fetch_hh_vacancies(language, moscow, page)
        all_lang_vacancies += hh_api_response['items']
        pages = hh_api_response['pages']
        if page == pages - 1:
            return all_lang_vacancies, hh_api_response['found']
        time.sleep(1.5)


def fetch_all_sj_vacancy_pages(language, sj_api_key):
    lang_vacancies = []
    for page in count():
        api_response = fetch_sj_vacancies(language, sj_api_key, page)
        lang_vacancies += api_response['objects']
        vacancies_count = api_response['total']
        if not api_response['more']:
            return lang_vacancies, vacancies_count
        time.sleep(1.5)


def get_hh_average_salary_and_vacancy_processed(vacancies):
    vacancies_processed = 0
    average_salary = 0
    for vacancy in vacancies:
        salary = predict_rub_salary_for_hh(vacancy)
        if salary:
            vacancies_processed += 1
            average_salary += salary
    try:
        average_salary = int(average_salary / vacancies_processed)
    except ZeroDivisionError:
        logging.info('не обработана ни одна вакансия')
        average_salary = 0
    return average_salary, vacancies_processed


def get_sj_average_salary_and_vacancy_processed(vacancies):
    vacancies_processed = 0
    average_salary = 0
    for vacancy in vacancies:
        salary_from = vacancy['payment_from']
        salary_to = vacancy['payment_to']
        salary = predict_salary(salary_from, salary_to)
        if salary:
            vacancies_processed += 1
            average_salary += salary
        time.sleep(1)
    try:
        average_salary = int(average_salary / vacancies_processed)
    except ZeroDivisionError:
        print('не обработана ни одна вакансия')
        average_salary = 0
    return average_salary, vacancies_processed


def get_hh_vacancies_salary(popular_languages, moscow):
    local_hh_table_vacancies = []
    for programm_lang in popular_languages:
        all_hh_vacancies, hh_vacancies_found = fetch_all_hh_vacancy_pages(
            programm_lang, moscow)
        hh_average_salary, hh_vacancies_processed = get_hh_average_salary_and_vacancy_processed(
            all_hh_vacancies)
        local_hh_table_vacancies.append([programm_lang, hh_vacancies_found,
                                   hh_vacancies_processed, hh_average_salary])
    return local_hh_table_vacancies


def get_sj_vacancies_salary(popular_languages, sj_api_key):
    local_sj_table_vacancies = []
    for programming_lang in popular_languages:
        all_sj_vacancies, sj_vacancies_found = fetch_all_sj_vacancy_pages(
            programming_lang, sj_api_key)
        sj_average_salary, sj_vacancies_processed = get_sj_average_salary_and_vacancy_processed(
            all_sj_vacancies)
        local_sj_table_vacancies.append([programming_lang, sj_vacancies_found,
                                   sj_vacancies_processed, sj_average_salary])
    return local_sj_table_vacancies


def main():
    popular_languages = {
        'C#',
        'Python',
        'Java',
        'Javascript',
        'PHP',
        'C++',
        'C',
        'Go'
    }
    moscow = 1
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
        filename='logs.log',
        filemode='w',)
    load_dotenv()

    sj_api_key = os.getenv('SUPERJOB_KEY')
    hh_table_vacancies = []
    sj_table_vacancies = []

    hh_vacancies_for_table = get_hh_vacancies_salary(popular_languages, moscow)
    hh_table_vacancies.append(*hh_vacancies_for_table)
    logging.info(f'hh {hh_table_vacancies}')
    sj_vacancies_for_table = get_sj_vacancies_salary(
        popular_languages, sj_api_key)
    sj_table_vacancies.append(*sj_vacancies_for_table)
    logging.info(f'sj {sj_table_vacancies}')

    sj_table = build_vacancy_stats_table(sj_table_vacancies, 'SJ Moscow')
    hh_table = build_vacancy_stats_table(hh_table_vacancies, 'HH Moscow')

    print(hh_table.table)
    print(sj_table.table)


if __name__ == "__main__":
    main()
