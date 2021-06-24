""" API classes """
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from app.serializers import PageSerializer, PageDetailSerializer  # , ContentDetailSerializer
from app.service import ContentType, Pagination
from app.models import Page  # , Content


class PageModelViewSet(viewsets.ModelViewSet):
    """ АPI модели Page.
        Класс ModelViewSet Наследуется от класса GenericAPIView и включает реализации api-методов: .list(), .retrieve(), .create(), .update(), .partial_update(), .destroy()

    """
    queryset = Page.objects.all()
    # serializer_class = PageSerializer
    pagination_class = Pagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        """ Переопределение страндартного метода.
            Установка сериализатора в зависимости от типа API-запроса.
        """
        if self.action == 'retrieve':
            return PageDetailSerializer
        return PageSerializer

    def retrieve(self, request, *args, **kwargs):
        """ Переопределение страндартного метода.
            Вызов метода модели при обработке API-запроса.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # Увеличение счётчика просмотров
        contents = instance.content.all()
        if contents:
            for obj in contents:
                if obj.not_empty:
                    ctype = obj.ctype
                    # вызов метода модели контента по типу
                    if ctype == ContentType.TEXT:
                        obj.text.inc_counter()
                    elif ctype == ContentType.AUDIO:
                        obj.audio.inc_counter()
                    elif ctype == ContentType.VIDEO:
                        obj.video.inc_counter()

        return Response(serializer.data)
