from django.urls import path

from . import page_views as views

app_name = "pages"

urlpatterns = [
    path("studies/", views.study_list, name="study_list"),
    path("studies/<int:pk>/", views.study_detail, name="study_detail"),
]