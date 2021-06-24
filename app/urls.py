""" Application urls. """

from django.urls import path, include
from rest_framework import routers

from app import api, views

router = routers.DefaultRouter()
router.register(r'pages', api.PageModelViewSet, 'pages')
router.register(r'page', api.PageModelViewSet, 'page')
router.register(r'page', api.PageModelViewSet, 'page')

urlpatterns = [
    path('', include(router.urls)),
    path('', views.HomePageView.as_view(), name='home'),  # стартовая страница
]
