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


if __name__ == "__main__":

    for programm_lang in POPULAR_LANGUAGES:
        count_of_langs = amount_of_vacancies(programm_lang)['found']
        POPULAR_LANGUAGES[programm_lang] = count_of_langs
    print(POPULAR_LANGUAGES)

