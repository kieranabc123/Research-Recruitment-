from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("terms/", TemplateView.as_view(template_name="terms.html"), name="terms"),
    path("accounts/", include("accounts.urls")),
    path("pages/", include("studies.page_urls")),
    path("admin/", admin.site.urls),
]
