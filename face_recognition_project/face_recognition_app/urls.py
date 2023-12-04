from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('check_face_detection/', check_face_detection, name='check_face_detection'),
    path('face_match/', face_match, name='face_match'),
    path('generate_excel/', generate_excel, name='generate_excel'),
]