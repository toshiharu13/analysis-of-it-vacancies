import logging
import requests

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


def amount_of_vacancies(language):
    params = {
        'text': {language},
    }
    req = requests.get('https://api.hh.ru/vacancies', params=params)
    return req.json()


def predict_rub_salary(vacancy):
    vacancy_salary = vacancy['salary']
    if vacancy_salary['currency'] != 'RUR':
        return None
    if not vacancy_salary['from'] and not vacancy_salary['to']:
        return None
    if not vacancy_salary['from']:
        return vacancy_salary['to']*0.8
    elif not vacancy_salary['to']:
        return vacancy_salary['from']*1.2
    else:
        return (vacancy_salary['from']+vacancy_salary['to'])/2


if __name__ == "__main__":

    '''for programm_lang in POPULAR_LANGUAGES:
        count_of_langs = amount_of_vacancies(programm_lang)['found']
        POPULAR_LANGUAGES[programm_lang] = count_of_langs
    print(POPULAR_LANGUAGES)'''

    python_vacancies = amount_of_vacancies('Python')['items']
    for vacancy in python_vacancies:
        print(predict_rub_salary(vacancy))


