from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import ProfileForm, RegisterForm
from .permissions import role_required


# Register: makes the account and logs the person straight in
def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("accounts:dashboard")

    return render(request, "accounts/register.html", {"form": form})


# Dashboard: participants see their profile and researchers see if they are approved
@login_required
def dashboard(request):
    profile = request.user.profile if request.user.role == "participant" else None
    return render(request, "accounts/dashboard.html", {"profile": profile})


# Edit profile (participants only): once every PROFILE_EDIT_COOLDOWN_MINUTES, until then
# the page only shows their answers and when they can edit again
@role_required("participant")
def profile_edit(request):
    profile = request.user.profile
    if not profile.can_edit_now:
        return render(request, "accounts/profile_form.html", {"profile": profile, "locked": True})

    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.last_edited_at = timezone.now()
        profile.save()
        messages.success(request, "Profile saved.")
        return redirect("accounts:dashboard")

    return render(request, "accounts/profile_form.html", {"form": form, "profile": profile})
