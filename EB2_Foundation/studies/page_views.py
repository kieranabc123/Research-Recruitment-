# TEMPORARY views so Samantha can build and test the pages.
# Felix's real logic will replace these later.
from django.shortcuts import get_object_or_404, render

from accounts.permissions import role_required

from .models import Application, Study


@role_required("participant")
def study_list(request):
    studies = Study.objects.filter(status=Study.Status.OPEN)
    return render(request, "studies/study_list.html", {"studies": studies})


@role_required("participant")
def study_detail(request, pk):
    study = get_object_or_404(Study, pk=pk, status=Study.Status.OPEN)
    return render(request, "studies/study_detail.html", {"study": study})


@role_required("participant")
def my_applications(request):
    applications = Application.objects.filter(participant=request.user).select_related("study")
    return render(request, "studies/my_applications.html", {"applications": applications})