""" Models. """

import mutagen  # рассчёт битрейта

from django.conf import settings
from django.core.validators import validate_comma_separated_integer_list
from django.db import models
from django.db.transaction import atomic

# импорт общего вспомогательного функционала
from app.service import ContentType, save_type_content, get_str_id, threads_counter, str_limit, str_content, capitalize, capitalize_all

# ----- Constants
CAPITALIZE_LANG_CODES = ['en-us']  # список языков для капитализации всех слов строки
EMPTY_STR = 'нет контента'


# ----- Abstract Models

class Title(models.Model):
    """ Абстрактная модель заголока страниц и контента. """

    class Meta:
        abstract = True

    title = models.CharField('Заголовок', max_length=256)

    def save(self, *args, **kwargs):
        """ Переопределение метода save базовой модели. """
        # Заглавные буквы всех слов заголовка для языков из списка либо для первого слова
        self.title = capitalize_all(self.title) if settings.LANGUAGE_CODE in CAPITALIZE_LANG_CODES \
            else capitalize(self.title)
        super(Title, self).save(*args, **kwargs)


class Properties(models.Model):
    """ Абстрактная модель объектов контента разного типа с одинаковыми свойствами.
        hash  -- MD5 хэш-код, устанавливает идентичность объекта контента.
    """

    class Meta:
        abstract = True

    # Поля с автоустановкой значений (только для чтения)
    hash = models.CharField('Хэш MD5', max_length=32, editable=False)
    counter = models.PositiveIntegerField('Просмотры', default=0, editable=False)


# ----- Database Models

class Page(Title):
    """ Модель страницы с контентом. """
    content = models.ManyToManyField('Content', verbose_name='Объекты контента')
    # Структура/последовательность расположения контента на странице
    content_list = models.CharField('Дерево контента', max_length=256,
                                    validators=[validate_comma_separated_integer_list])

    def save(self, *args, **kwargs):
        # Инициализация нового списка контента
        lst = self.content_list.split(',')
        content = Content.objects.filter(id__in=lst)
        super(Page, self).save(*args, **kwargs)
        self.content.set(content)

    def __str__(self):
        return get_str_id(self) + 'страница: {}.'.format(str_limit(self.title)) \
               + (' [{}]'.format(str_limit(self.content_list) if self.content_list else EMPTY_STR))


class Content(Title, ContentType):
    """ Модель контента страницы Page. Связана с одним из объектов различных типов контента.
        При установке одновременно всех связей на типовой контент актуален соответствующий установленному типу.
        is_empty    -- маркер отсутствия связи с типовым контентом.
        text, media -- ссылки на объекты контента определённого типа ctype.
    """
    # Связи с контентом по типу
    text = models.ForeignKey('Text', verbose_name='Текст', null=True, blank=True, on_delete=models.SET_NULL)
    audio = models.ForeignKey('Audio', verbose_name='Аудио', null=True, blank=True, on_delete=models.SET_NULL)
    video = models.ForeignKey('Video', verbose_name='Видео', null=True, blank=True, on_delete=models.SET_NULL)
    # Маркер наличия контента по типу
    not_empty = models.BooleanField('Контент', default=False, editable=False)        # автоустановка

    def save(self, *args, **kwargs):
        self.ctype = self.TEXT if self.text else self.AUDIO if self.audio else self.VIDEO if self.video else ''
        if self.text or self.audio or self.video:
            self.not_empty = True                                                    # наличие контента по типу
        super(Content, self).save(*args, **kwargs)

    def __str__(self):
        return get_str_id(self) + '{}, {}.'.format(self.id, self.get_ctype_display(), str_limit(self.title))


# ----- Content Typed Models

class Text(Properties):
    """ Модель текстового контента. """
    value = models.TextField(ContentType.CTYPE_DICT_STR[ContentType.TEXT])

    @property
    def content_field_name(self):
        """ Возвращает имя поля контента. """
        return ContentType.CTYPE_DICT[ContentType.TEXT]

    @atomic
    def inc_counter(self):
        """ Увеличивает счётчик просмотров. """
        threads_counter(self)

    def save(self, *args, **kwargs):
        self.value = capitalize(self.value)
        save_type_content(self, Content, *args, **kwargs)

    def __str__(self):
        return get_str_id(self) + ContentType.CTYPE_DICT_STR[ContentType.TEXT] + '. ' + str_content(self) + '. ' + str_limit(self.value)


class Audio(Properties):
    """ Модель аудиоконтента. """
    value = models.FileField(ContentType.CTYPE_DICT_STR[ContentType.AUDIO], upload_to=settings.MEDIA_ROOT)
    bitrate = models.PositiveIntegerField('Битрейт', editable=False)

    @property
    def content_field_name(self):
        return ContentType.CTYPE_DICT[ContentType.AUDIO]

    @atomic
    def inc_counter(self):
        threads_counter(self)

    def save(self, *args, **kwargs):
        self.bitrate = mutagen.File(self.value).info.bitrate
        save_type_content(self, Content, *args, **kwargs)

    def __str__(self):
        return get_str_id(self) + ContentType.CTYPE_DICT_STR[ContentType.AUDIO] + '. ' + str_content(self)


class Video(Properties):
    """ Модель видеоконтента. """
    value = models.FileField(ContentType.CTYPE_DICT_STR[ContentType.VIDEO], upload_to=settings.MEDIA_ROOT)
    subtitles = models.FileField('Субтитры', upload_to=settings.SUBTITLES)

    @property
    def content_field_name(self):
        return ContentType.CTYPE_DICT[ContentType.VIDEO]

    @atomic
    def inc_counter(self):
        threads_counter(self)

    def save(self, *args, **kwargs):
        save_type_content(self, Content, *args, **kwargs)

    def __str__(self):
        return get_str_id(self) + ContentType.CTYPE_DICT_STR[ContentType.VIDEO] + '. ' + str_content(self)
