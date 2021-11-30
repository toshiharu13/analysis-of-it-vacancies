import logging
import requests
import time
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


POPULAR_LANGUAGES = [
    ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
    ['Python', 0, 0, 0],
    ['Java', 0, 0, 0],
    #['Javascript', 0, 0, 0],
    #['PHP', 0, 0, 0],
    #['C++', 0, 0, 0],
    #['C#', 0, 0, 0],
    #['C', 0, 0, 0],
    #['Go', 0, 0, 0]
    ]


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
    filename='logs.log',
    filemode='w',
    )


def amount_of_vacancies(language, page=0, per_page=20):
    params = {
        'text': language,
        'page': page,
        'per_page': per_page,
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


def predict_rub_salary(vacancy):
    vacancy_salary = vacancy['salary']
    if not vacancy_salary or vacancy_salary['currency'] != 'RUR':
        return 0
    if not vacancy_salary['from'] and not vacancy_salary['to']:
        return 0
    if not vacancy_salary['from']:
        return vacancy_salary['to']*0.8
    elif not vacancy_salary['to']:
        return vacancy_salary['from']*1.2
    else:
        return (vacancy_salary['from']+vacancy_salary['to'])/2


def predict_rub_salary_for_superJob(vacancy):
    if not vacancy['payment_from'] and not vacancy['payment_to']:
        return None
    if not vacancy['payment_from']:
        return vacancy['payment_to']*0.8
    elif not vacancy['payment_to']:
        return vacancy['payment_from']*1.2
    else:
        return (vacancy['payment_from'] + vacancy['payment_to'])/2

def show_all_vacancy(language):
    response_hh_api = amount_of_vacancies(language)
    python_vacancy = []
    python_vacancy += response_hh_api['items']
    pages = response_hh_api['pages']
    if pages > 100:
        pages = 100
    for page in range(1, pages):
        response_hh_api = amount_of_vacancies(language, page)
        python_vacancy += response_hh_api['items']
        logging.info(response_hh_api['page'])
        time.sleep(1.5)
    return (python_vacancy,response_hh_api['found'])


if __name__ == "__main__":
    load_dotenv()
    sj_key = os.getenv('SUPERJOB_KEY')
    '''for programm_lang in POPULAR_LANGUAGES:
        all_vacancy_and_found = show_all_vacancy(programm_lang)
        language_vacancies = all_vacancy_and_found[0]
        vacancies_processed = 0
        average_salary = 0
        vacancies_found = all_vacancy_and_found[1]
        for vacancy in language_vacancies:
            salary = predict_rub_salary(vacancy)
            if salary > 0:
                vacancies_processed += 1
                average_salary += salary
        average_salary = average_salary/vacancies_processed
        POPULAR_LANGUAGES[programm_lang] = {'vacancies_found': vacancies_found,
                                            'vacancies_processed': vacancies_processed,
                                            'average_salary': int(average_salary),
                                            }
    print(POPULAR_LANGUAGES)'''
    # обработка данных API SuperJob
    sj_table_data = POPULAR_LANGUAGES[:]
    for programming_lang in sj_table_data:
        if type(programming_lang[1]) == str:
            continue
        sj_response = get_amount_sj_vacancies(programming_lang[0], sj_key)
        all_sj_vacancies = sj_response['objects']
        vacancies_processed = 0
        average_salary = 0
        vacancies_found = sj_response['total']
        for sj_vacancy in all_sj_vacancies:
            salary = predict_rub_salary_for_superJob(sj_vacancy)
            if salary:
                vacancies_processed += 1
                average_salary += salary
            time.sleep(1)

        programming_lang[1] = vacancies_processed
        programming_lang[2] = int(vacancies_found)
        programming_lang[3] = int(average_salary)

        logging.info(sj_table_data)

    sj_table = AsciiTable(sj_table_data, 'SuperJob Moscow')
    sj_table.justify_columns[4] = 'right'
    print(sj_table.table)



