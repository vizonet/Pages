# ----- App Common Functions

import hashlib
from threading import Thread

from django.db import models
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

# ----- Global constants

MAX_STR_LIMIT = 20                                  # ограничение показа части контента в представлении объекта модели
STR_LIMIT_END = '...'                               # символ окончания обрезки лимитированной строки
HASH_CHUNK_SIZE = 524288                            # размер порции данных хэширования файла в байтах => 512 КБ * 1024 Б
EMPTY_LABEL = '-- Выберите --'                      # пустая метка списка choices


class ContentType(models.Model):
    """ Абстрактная модель типов контента. """

    class Meta:
        abstract = True

    # Типы контента в choices
    TEXT = 'T'
    AUDIO = 'A'
    VIDEO = 'V'
    # ...
    # Кортеж choices
    CONTENT_TYPE = (
        (None, EMPTY_LABEL),
        (TEXT, 'Text'),
        (AUDIO, 'Audio'),
        (VIDEO, 'Video'),
        # ...
    )
    # Словарь имен связанных полей контента по типу
    CTYPE_DICT = {
        TEXT: 'text', AUDIO: 'audio', VIDEO: 'video',
    }
    # Словарь строковых представлений связанных объектов контента по типу
    CTYPE_DICT_STR = {
        TEXT: 'Текст', AUDIO: 'Аудио', VIDEO: 'Видео',
    }
    ctype = models.CharField('Тип', max_length=1, default='', choices=CONTENT_TYPE, editable=False)     # автоустановка


class Pagination(PageNumberPagination):
    """ Пагинатор. """
    page_size = 2                                                # per page
    page_size_query_param = 'page_size'
    max_page_size = 1000

    # Переопределение стандартного метода отображения параметров пагинации
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'links': {
                'previous': self.get_previous_link(),
                'next': self.get_next_link(),
            },
            'results': data
        })


# ----- Общий функционал, в т.ч. для расширения стандартных методов моделей

def get_hash(file_path, string='', chunk_size=HASH_CHUNK_SIZE):
    """ Возвращает вычисленную HASH-сумму файла либо строки текста.
        Определяет по входным параметрам способ хэширования. Если заданы оба, то по умолчанию хэшируется файл.
    """
    err_msg = ' на операции хэширования файла!'
    md5hash = hashlib.md5()
    # HASH-сумма файла
    if file_path and chunk_size:
        try:
            # если возможно разделить файл на части
            if file_path.multiple_chunks():
                # деление файла на части для защиты от переполнения памяти большим размером файла
                for data in file_path.chunks(chunk_size):
                    md5hash.update(data)
            else:
                md5hash.update(file_path.read())                 # чтение файла целиком
            md5hash = md5hash.hexdigest()
        except MemoryError:
            print('Ошибка: переполнение памяти' + err_msg)
        except FileNotFoundError:
            print('Ошибка: файл не найден' + err_msg)
    # HASH-сумма строки
    elif string:
        try:
            md5hash = hashlib.md5(string.encode()).hexdigest()  # кодировка по умолчанию - encode('UTF-8')
        except TypeError:
            print('Ошибка хеширования: данные не являются строкой либо кодировка отлична от UTF-8!')
    else:
        md5hash = 'Hash error'
    return md5hash                                              # строка хэш-суммы


def get_str_id(obj):
    """ Возвращает строковый id объекта модели. """
    return '({}) '.format(obj.id)


def save_type_content(obj, content_model, *args, **kwargs):
    """ Переопределение метода save базовой модели контента по типу.
        Проверка уникальности объекта и перестановка на него связей с дубликатов, удаление дубликатов.
    """
    # Вычисление хэша
    if obj.content_field_name == ContentType.CTYPE_DICT[ContentType.TEXT]:
        obj.hash = get_hash('', obj.value)                      # текстовый хэш
    else:
        obj.hash = get_hash(obj.value)                          # файловый хэш

    # Проверка и удаление дубликатов
    hash_query = get_hash_query(obj)                            # выборка объектов с одним хэшем
    if hash_query is not None and hash_query.exists():
        # Ключ имени поля связанного контента по типу
        kw_filter = {'{}__in'.format(obj.content_field_name): hash_query}
        # Выборка объектов контента страницы со связанными объектами с идентичным хэшем
        content_query = content_model.objects.filter(**kw_filter)
        # Выборка из дубликатов первого в истории объекта
        first_obj = hash_query.first()
        # Перепривязка объектов контента на первый объект из дубликатов контента по типу
        kw_upd = {'{}'.format(obj.content_field_name): first_obj}
        content_query.update(**kw_upd)
        # Переназначение текущего объекта оригинальному (когда дубликаты вручную добавлены в БД)
        obj.id = hash_query[0].id                               # id оригинального объекта
        obj.value = hash_query[0].value                         # привязка файла оригинального объекта к текущему
        # Удаление дубликатов при наличии
        if hash_query.count() > 1:
            del_doubles(obj, hash_query[1:])                    # передаём выборку дубликатов кроме первого

    super(type(obj), obj).save(*args, **kwargs)


def get_hash_query(obj):
    """ Возвращает QuerySet дубликатов контента по типу после проверки по хэшу либо None при отсутствии хэша. """
    query = None
    if hasattr(obj, 'hash') and obj.hash:
        query = type(obj).objects.filter(hash=obj.hash).order_by('id')
    return query


def del_doubles(obj, lst):
    """ Удаление дубликатов контента по типу. """
    if obj.content_field_name == ContentType.CTYPE_DICT[ContentType.TEXT]:
        for item in lst:
            item.delete()                                           # удаление дубликатов текста
    else:
        for item in lst:                                            # удаление файловых объектов
            storage, path = item.value.storage, item.value.path     # до удаления записи получаем необходимую информацию
            storage.delete(path)                                    # удаление файла
            item.delete()                                           # удаление объекта модели
    return


# ----- Функции обработки тектста

def str_limit(string):
    """ Возвращает версию строки, ограниченную заданными параметрами с добавлением символа окончания обрезки. """
    return string[:MAX_STR_LIMIT] + (STR_LIMIT_END if len(string) > MAX_STR_LIMIT else '')


def str_content(obj):
    """ Метод для интеграции общих параметров в строковое представление моделей типового контента. """
    return 'Просмотры: {}'.format(obj.counter)


def capitalize(string):
    """ Возвращает капитализацию первого слова текста строки. """
    return string.capitalize()


def capitalize_all(string):
    """ Возвращает капитализацию всех слов текста строки. """
    new_str = ''
    for word in string.split():
        new_str += word.capitalize() + ' '
    return new_str[:-1]                                         # исключая последний пробел


def increase_counter(obj):
    """ Увеличивает счётчик просмотров объекта контента по типу. """
    obj.counter += 1
    obj.save()


# ----- Обработка в потоках

def threads_counter(obj):
    if hasattr(obj, 'counter'):
        thread = Thread(target=increase_counter, args=[obj])
        thread.start()
