import logging
import requests
import time

POPULAR_LANGUAGES = {'Python': 0, 'Java': 0, 'Javascript': 0,
                     'Ruby': 0, 'PHP': 0, 'C++': 0, 'C#': 0,
                     'C': 0, 'Go': 0, 'Scala': 0,
                     }

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


def show_all_vacancy(language):
    response_hh_api = amount_of_vacancies(language)
    python_vacancy = []
    python_vacancy += response_hh_api['items']
    pages = response_hh_api['pages']
    if pages > 100:
        pages = 100
    for page in range(1, 5):
        response_hh_api = amount_of_vacancies(language, page)
        python_vacancy += response_hh_api['items']
        logging.info(response_hh_api['page'])
        time.sleep(1)
    return (python_vacancy,response_hh_api['found'])


if __name__ == "__main__":
    for programm_lang in POPULAR_LANGUAGES:
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
    print(POPULAR_LANGUAGES)


