from django.urls import path

from . import page_views as views

app_name = "pages"

urlpatterns = [
    path("studies/", views.study_list, name="study_list"),
    path("studies/<int:pk>/", views.study_detail, name="study_detail"),
    path("my-applications/", views.my_applications, name="my_applications"),
    path("researcher/studies/", views.researcher_studies, name="researcher_studies"),
    path("researcher/studies/new/", views.study_create, name="study_create"),
    path("researcher/studies/<int:pk>/edit/", views.study_edit, name="study_edit"),
    path("researcher/studies/<int:pk>/applicants/", views.study_applicants, name="study_applicants"),
]
