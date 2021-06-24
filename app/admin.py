""" Admin Site. """

from django.contrib import admin
from django.core.paginator import Paginator
from search_admin_autocomplete.admin import SearchAutoCompleteAdmin

from app.models import Page, Content, Text, Audio, Video

# ----- CONSTANTS
SET_DATA_STR = 'Задайте свойства:'
READONLY_STR = 'Автоматические поля (только для чтения):'
SEARCH_FORMAT = ''                                  # формат поиска (__startswith и '^field' - не работают)
# имена полей
ID_NAME = 'id'
TITLE_NAME = 'title' + SEARCH_FORMAT
VALUE_NAME = 'value' + SEARCH_FORMAT

# ----- FIELD LISTS
# Для моделей конечного контента разных типов
EDITABLE_FIELDS = ['value']
READONLY_FIELDS = ['hash', ID_NAME, 'counter']

# Для изменения макета редактирования объекта (аналог html-тега fieldset)
FIELD_SETS = [
    (READONLY_STR, {
        'fields': (READONLY_FIELDS, )                           # кортеж - для inline-block группировки полей
    }),
]


class CommonProps(SearchAutoCompleteAdmin):    # admin.ModelAdmin
    """ Базовый класс идентичных настроек моделей в админ-панели. """
    # Пагинация
    list_per_page = 10                                          # количество записей объектов на странице
    paginator = Paginator


class ContentAdminProps(admin.ModelAdmin):
    """ Базовый класс идентичных настроек моделей типового контента в админ-панели. """
    list_display = READONLY_FIELDS + EDITABLE_FIELDS            # отображаемые поля на странице списка объектов
    readonly_fields = READONLY_FIELDS


class ContentInstance(admin.TabularInline):
    """ Горизонтальное расположение блоков встроенного редактирования моделей. """
    model = Content
    fields = ('title', )


@admin.register(Page)  # декоратор для регистрации моделей и классов ModelAdmin в админ-панели
class PageAdmin(CommonProps):
    EDITABLE = ('title', 'content_list', 'content')
    fieldsets = (
        (SET_DATA_STR, {
            'fields': EDITABLE
        }),
    )
    search_fields = [TITLE_NAME]                                # поиск по полю, format 'foreign_key__related_fieldname'
    list_display = EDITABLE[:-1] + (ID_NAME, )                  # исключая поле many_to_many
    raw_id_fields = ('content', )                               #
    autocomplete_fields = ['content']

# admin.site.register(Page, PageAdmin)                          # способ регистрации моделей в админ-панели


@admin.register(Content)
class ContentAdmin(CommonProps):
    EDITABLE = ('title', 'text', 'audio', 'video')
    READONLY = ('ctype', 'not_empty', ID_NAME)

    search_fields = [TITLE_NAME]
    # autocomplete_fields = ['page']                              # список связанных объектов

    list_filter = ('text', 'audio', 'video')
    list_display = EDITABLE + READONLY
    readonly_fields = READONLY
    fieldsets = (
        (SET_DATA_STR, {
            'fields': EDITABLE
        }),
        (READONLY_STR, {
            'fields': (READONLY, )
        }),
    )


@admin.register(Text)
class TextAdmin(ContentAdminProps, CommonProps):
    inlines = [ContentInstance]                            # встроенное редактирование связанных записей в админ-панели
    fieldsets = FIELD_SETS.insert(0, (SET_DATA_STR, {'fields': (EDITABLE_FIELDS, )}))
    search_fields = [VALUE_NAME]


@admin.register(Audio)
class AudioAdmin(ContentAdminProps, CommonProps):
    inlines = [ContentInstance]
    fieldsets = FIELD_SETS.insert(0, (SET_DATA_STR, {'fields': (EDITABLE_FIELDS + ['bitrate'], )}))
    search_fields = [VALUE_NAME]


@admin.register(Video)
class VideoAdmin(ContentAdminProps, CommonProps):
    inlines = [ContentInstance]
    fieldsets = FIELD_SETS.insert(0, (SET_DATA_STR, {'fields': (EDITABLE_FIELDS + ['subtitles'], )}))
    search_fields = [VALUE_NAME]
