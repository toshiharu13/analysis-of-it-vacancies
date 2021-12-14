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


def prepare_vacancies_to_table(table_vacancies_info):
    final_table = []
    final_table.append(['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'])
    final_table.extend(table_vacancies_info)
    return final_table


def fetch_all_hh_vacancy_pages(language, moscow):
    hh_api_response = fetch_hh_vacancies(language, moscow)
    all_lang_vacancies = []
    all_lang_vacancies += hh_api_response['items']
    pages = hh_api_response['pages']
    time.sleep(1)
    for page in range(1, 2):
        hh_api_response = fetch_hh_vacancies(language, moscow, page)
        all_lang_vacancies += hh_api_response['items']
        time.sleep(2)
    return all_lang_vacancies, hh_api_response['found']


def fetch_all_sj_vacancy_pages(language, sj_api_key):
    api_response = fetch_sj_vacancies(language, sj_api_key)
    lang_vacancies = []
    lang_vacancies += api_response['objects']
    vacancies_count = api_response['total']
    pages = vacancies_count // 20
    time.sleep(1)
    if pages <= 1:
        return lang_vacancies, api_response['found']
    for page in range(1, 2):
        api_response = fetch_sj_vacancies(language, sj_api_key, page)
        lang_vacancies += api_response['objects']
        time.sleep(2)
    return lang_vacancies, vacancies_count


def get_hh_average_salary_and_vacancy_processed(vacancies):
    vacancies_processed = 0
    average_salary = 0
    for vacancy in vacancies:
        salary = predict_rub_salary_for_hh(vacancy)
        if salary:
            vacancies_processed += 1
            average_salary += salary
    average_salary = int(average_salary / vacancies_processed)
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
    average_salary = int(average_salary / vacancies_processed)
    return average_salary, vacancies_processed


def collect_hh_vacancies(programm_lang, vacancies_found, vacancies_processed,
                         average_salary, hh_table_vacancies):
    hh_table_vacancies.append(
        [programm_lang, vacancies_found, vacancies_processed, average_salary])


def collect_sj_vacancies(programm_lang, vacancies_found, vacancies_processed,
                         average_salary, sj_table_vacancies):
    sj_table_vacancies.append(
        [programm_lang, vacancies_found, vacancies_processed, average_salary])

def main():
    popular_languages = {
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
    hh_table_vacancies = []
    sj_table_vacancies = []

    for programm_lang in popular_languages:
        all_hh_vacancies, hh_vacancies_found = fetch_all_hh_vacancy_pages(programm_lang, moscow)
        hh_average_salary, hh_vacancies_processed = get_hh_average_salary_and_vacancy_processed(all_hh_vacancies)

        collect_hh_vacancies(
            programm_lang, hh_vacancies_found, hh_vacancies_processed,
            hh_average_salary,
            hh_table_vacancies)
        logging.info(f'hh {hh_table_vacancies}')

    for programming_lang in popular_languages:
        all_sj_vacancies, sj_vacancies_found = fetch_all_sj_vacancy_pages(programming_lang, sj_api_key)
        sj_average_salary, sj_vacancies_processed = get_sj_average_salary_and_vacancy_processed(all_sj_vacancies)

        collect_sj_vacancies(
            programming_lang, sj_vacancies_found, sj_vacancies_processed,
            sj_average_salary, sj_table_vacancies)
        logging.info(f'sj {sj_table_vacancies}')

    sj_table = AsciiTable(
        prepare_vacancies_to_table(sj_table_vacancies), 'SuperJob Moscow')
    print(sj_table.table)

    hh_table = AsciiTable(
        prepare_vacancies_to_table(hh_table_vacancies), 'HH Moscow')
    print(hh_table.table)


if __name__ == "__main__":
    main()
