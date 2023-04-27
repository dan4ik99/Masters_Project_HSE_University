import requests
import json
import pandas as pd
import numpy as np

import os
from pathlib import Path
import nltk
from nltk import sent_tokenize, word_tokenize, regexp_tokenize
from nltk.corpus import stopwords
import pymorphy2
#Представляем слова с помощью чисел. Коды для слов выбираем с частотой, с которой слово встречается в тексте
#С помощью структуры данных Counter определяем частоту слов
from collections import Counter
import re
class Vectorization:
    def __init__(self, description):
        self.description = description

    # Пока не используется. Долго ебался с капчей. Не получалось обратиться к сайту
    # Но при первых обращениях успел сохранить данные в датафрейм. Поэтому к нему обращаюсь.
    def get_data_from_HH():
        row = []
        for i in range(0, 200):
            hh_parser = requests.get('https://api.hh.ru/vacancies?area=1948&page=' + str(i)).json()
            for j in hh_parser['items']:
                name = ' '
                requirement = ' '
                responsibility = ' '
                if 'name' in j:
                    name = j['name']
                if 'snippet' in j:
                    if 'requirement' in j['snippet']:
                        requirement = j['snippet']['requirement']
                    if 'responsibility' in j['snippet']:
                        responsibility = j['snippet']['responsibility']

                description = str(name) + " " + str(requirement) + " " + str(responsibility)
                row.append(description)
        data = pd.DataFrame({'text': row})
        return data



    def preprocessed_data_for_learning(self):
        data = pd.read_excel('vectorized_data.xlsx')
        data['Preprocessed_texts_list'] = data['Preprocessed_texts']. \
        apply(lambda i: i[2:len(i)-2].split("', '"))
        # Считаем частоту слов во всех описаниях резюме/вакансий
        words = Counter()
        for txt in data['Preprocessed_texts_list']:
            words.update(txt)
        return words


    def input_text_preprocessing(self):
        url_stopwords_ru = "https://raw.githubusercontent.com/stopwords-iso/stopwords-ru/master/stopwords-ru.txt"
        description_df = pd.DataFrame({'text':[self.description]})

        def get_text(url, encoding='utf-8', to_lower=True):
            url = str(url)
            if url.startswith('http'):
                r = requests.get(url)
                if not r.ok:
                    r.raise_for_status()
                return r.text.lower() if to_lower else r.text
            elif os.path.exists(url):
                with open(url, encoding=encoding) as f:
                    return f.read().lower() if to_lower else f.read()
            else:
                raise Exception('parameter [url] can be either URL or a filename')

        def normalize_tokens(tokens):
            morph = pymorphy2.MorphAnalyzer()
            return [morph.parse(tok)[0].normal_form for tok in tokens]

        def remove_stopwords(tokens, stopwords=None, min_length=4):
            if not stopwords:
                return tokens
            stopwords = set(stopwords)
            r = re.compile("[а-яА-Я]+")
            tokens = [tok
                      for tok in filter(r.match, tokens)
                      if tok not in stopwords and len(tok) >= min_length]
            return tokens

        def tokenize_n_lemmatize(text, stopwords=None, normalize=True, regexp=r'(?u)\b\w{4,}\b'):
            words = [w for sent in sent_tokenize(text)
                     for w in regexp_tokenize(sent, regexp)]
            if normalize:
                words = normalize_tokens(words)
            if stopwords:
                words = remove_stopwords(words, stopwords)
            return words

        stopwords_ru = get_text(url_stopwords_ru).splitlines()

        description_df['Preprocessed_texts'] = description_df['text']. \
            apply(lambda row: tokenize_n_lemmatize(row, stopwords=stopwords_ru))

        '''
        Создаем словарь, упорядоченный по частоте
        В словаре будем использовать 2 специальных кода:
            - Код заполнитель: 0;
            - Неизвестное слово: 1
        Нумерация слов в словаре начинается с 2.
        Нумрация начинается с самого часто встречающегося слова в тексте
        '''

        # Словарь, отображающий слова в коды
        word_to_index = dict()
        # Словарь, отображающий коды в слова
        index_to_word = dict()

        # Максимальное количество обрабатываемых слов
        max_words = 5000

        words = self.preprocessed_data_for_learning()

        # word_to_index_AND_index_to_word
        for i, word in enumerate(words.most_common(max_words - 2)):
            # max_words - 2: Учитываем наши два специальные символа.
            word_to_index[word[0]] = i + 2
            index_to_word[i + 2] = word[0]

        # index_to_word: Из последовательности кода слов хотим восстановить исходный текст отзыва

        # Функция для преобразования списка слов в список кодов
        def text_to_sequence(txt, word_to_index):
            seq = []
            for word in txt:
                index = word_to_index.get(word, 1)
                # В случае, если такого слова нет, возвращаем 1 - означает неизвестное слово
                # Неизвестные слова не добавляем в выходную последовательность
                if index != 1:
                    seq.append(index)
            return seq

        # Преобразуем все тексты в последовательность кодов слов
        description_df['Sequences'] = description_df. \
            apply(lambda row: text_to_sequence(row['Preprocessed_texts'], word_to_index), axis=1)

        # Векторизация методом BOW
        def vectorize_sequences(sequences, dimension=max_words):
            # sequences - кол-во строк с описанием вакансии/резюме. Кол-во элементов в тексте.
            # dimension - Максимальное кол-во используемых слов.
            results = np.zeros((len(sequences), dimension))
            for i, sequence in enumerate(sequences):
                for index in sequence:
                    results[i, index] += 1.
            return results

        vectors = vectorize_sequences(description_df['Sequences'], max_words).astype('int')
        description_df['bow_vectors'] = list(vectors)
        vector = '_'.join(map(str, description_df.bow_vectors[0]))
        return vector








