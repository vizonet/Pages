""" Serializers Classes. """

from rest_framework import serializers
from app.models import Page  # , Content


class PageSerializer(serializers.HyperlinkedModelSerializer):
    """ Сериализатор модели Page. """
    url = serializers.HyperlinkedIdentityField(view_name="page-detail")
    content = serializers.SlugRelatedField(
        many=True,
        read_only=True,  # False,
        slug_field='id',
        # required=True
    )

    class Meta:
        model = Page
        fields = ('id', 'url', 'title', 'content_list', 'content')  #


class PageDetailSerializer(serializers.ModelSerializer):
    """ Сериализатор модели Page. """

    class Meta:
        depth = 2                                                           # глубина отображения связанных объектов
        model = Page
        fields = ('id', 'url', 'title', 'content_list', 'content')

    url = serializers.HyperlinkedIdentityField(view_name="page-detail")
