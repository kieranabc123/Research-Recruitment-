# TEMPORARY views so Samantha can build and test the pages.
# Felix's real logic will replace these later.
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import role_required

from .forms import StudyForm
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


@role_required("researcher", approved=True)
def researcher_studies(request):
    studies = Study.objects.filter(researcher=request.user).annotate(applicant_count=Count("applications"))
    return render(request, "studies/researcher_studies.html", {"studies": studies})


@role_required("researcher", approved=True)
def study_applicants(request, pk):
    study = get_object_or_404(Study, pk=pk, researcher=request.user)
    applications = Application.objects.filter(study=study).select_related("participant")
    return render(request, "studies/study_applicants.html", {"study": study, "applications": applications})


@role_required("researcher", approved=True)
def study_create(request):
    form = StudyForm(request.POST or None)
    if form.is_valid():
        study = form.save(commit=False)
        study.researcher = request.user
        study.save()
        messages.success(request, "Study saved.")
        return redirect("pages:researcher_studies")
    return render(request, "studies/study_form.html", {"form": form, "title": "New study"})


@role_required("researcher", approved=True)
def study_edit(request, pk):
    study = get_object_or_404(Study, pk=pk, researcher=request.user)
    form = StudyForm(request.POST or None, instance=study)
    if form.is_valid():
        form.save()
        messages.success(request, "Study updated.")
        return redirect("pages:researcher_studies")
    return render(request, "studies/study_form.html", {"form": form, "title": "Edit study"})
