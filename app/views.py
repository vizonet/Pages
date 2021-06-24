""" View Controllers. """

from django.views.generic.base import TemplateView

from app.models import Page


# ----- Class based views

class HomePageView(TemplateView):
    """ Стартовая страница приложения. """
    template_name = "app/index.html"

    def get_context_data(self, **kwargs):
        # инициализация контекста из базового класса
        context = super().get_context_data(**kwargs)
        # новый фунционал
        random_page = Page.objects.filter().only('id').order_by('?').first()
        random_page_msg = '(' + (('random page <id> = ' + str(random_page.id)) if random_page
                                 else 'no pages in database') + ')'
        url_details = '/page/' + (str(random_page.id) if random_page else '<id>')
        api_list = [
            {   # список всех страниц
                'method': 'GET', 'url': '/pages', 'info': 'Список всех страниц',
                'comment': '', 'json': 'paginated pages list'
            },
            {   # детализация страницы
                'method': 'GET', 'url': url_details, 'info': 'Детальная информация о странице',
                'comment': random_page_msg, 'json': 'page details'
            },
        ]
        context.update({
            'random_page': random_page,
            'api_list': api_list,
            'title': 'Pages',
            'year': '2021',
        })
        return context
