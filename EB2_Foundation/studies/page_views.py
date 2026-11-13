# TEMPORARY views so Samantha can build and test the pages.
# Felix's real logic will replace these later.
from django.shortcuts import render

from accounts.permissions import role_required

from .models import Study


@role_required("participant")
def study_list(request):
    studies = Study.objects.filter(status=Study.Status.OPEN)
    return render(request, "studies/study_list.html", {"studies": studies})
