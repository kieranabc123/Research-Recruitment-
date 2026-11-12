# EB2 Foundation

The foundation part of the project: the Django setup, login and roles, researcher
approval, and the database models (users, participant profiles, studies and
applications).

## Set it up in PyCharm

You need Python 3.10 or newer and PyCharm (Community or Professional both work).

1. **Open the project.** In PyCharm choose File > Open and pick the folder that
   has `manage.py` in it. If PyCharm asks you to create a virtual environment from
   `requirements.txt`, say yes and skip to step 3.
2. **Make the virtual environment.** Go to File > Settings (on a Mac:
   PyCharm > Settings), then Project > Python Interpreter > Add Interpreter > Add
   Local Interpreter > Virtualenv Environment > New, and click OK.
3. **Install the packages.** Open the Terminal tab at the bottom of PyCharm
   (Alt+F12). The line should start with `(.venv)`, which means the environment is
   on. Run:
   ```
   pip install -r requirements.txt
   ```
4. **Make your `.env` file.** In the same Terminal run:
   ```
   cp .env.example .env
   ```
   Then make a secret key:
   ```
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
   Open `.env` in PyCharm and paste the key after `SECRET_KEY=`, replacing the
   placeholder text. Everyone makes their own key and `.env` never goes on GitHub.
5. **Make the database and the demo accounts.** In the Terminal run:
   ```
   python manage.py migrate
   python manage.py seed_demo
   ```
6. **Run the site.** Go to Run > Edit Configurations > the + button > Python and fill in:
   Name `runserver`, Script path `manage.py` (pick the file in the project),
   Parameters `runserver`. Click OK, then press the green play button and open
   http://127.0.0.1:8000 in your browser. (In PyCharm Professional you can pick
   "Django server" instead of "Python".) You can also just type
   `python manage.py runserver` in the Terminal.
7. **Run the tests.** In the Terminal run `python manage.py test`.

If a command says `python` is not found, try `python3`. If the Terminal line does
not start with `(.venv)`, check step 2.

## Demo accounts

`seed_demo` makes these. They all use the password `DemoPass!234`. Demo only,
never use it on a site real people can reach.

| Username | Role | Notes |
|---|---|---|
| `demo_admin` | Admin | Opens the admin site at `/admin/` |
| `demo_researcher` | Researcher | Approved |
| `demo_pending_researcher` | Researcher | Not approved yet, use it to test approval |
| `demo_participant` | Participant | Complete profile: 18-24, undergraduate, no health condition |
| `participant1` to `participant5` | Participant | Random profiles |

To make your own admin account, run `python manage.py createsuperuser`.

## Logging in, passwords and sessions

- Everyone ticks the terms box when they register and we save when they did.
  The wording is on the `/terms/` page.
- An email address can only be used for one account.
- "Forgot your password?" is on the log in page. While we develop, the reset
  email prints in the terminal where `runserver` is running, so copy the link from
  there. Once you are logged in, "Change password" is in the menu.
- People are logged out after 30 minutes without doing anything.
- After 5 wrong passwords in a row a username is locked out for 5 minutes, and a
  correct login clears the count. Change `MAX_FAILED_LOGINS` and `LOCKOUT_MINUTES`
  in `settings.py` if that is too strict.
- Participants fill in their bands at `/accounts/profile/`. A "yes" or "no" on
  health needs the consent box ticked, and we save when it was ticked. After a
  save they can't change their profile again for `PROFILE_EDIT_COOLDOWN_MINUTES`
  (10 by default). Until then the page shows their answers and when they can edit
  again.
- Logins, failed logins, logouts, researcher decisions and profile changes are
  written to `logs/activity.log`, never with passwords or profile answers.
  Researcher decisions also show in the admin under the user's History.

## How researcher approval works

1. Someone registers as a researcher. They start with `approved = False`.
2. An admin goes to `/admin/`, opens Users, ticks the researchers and picks
   "Approve selected researchers" or "Reject selected researchers" from the Action
   menu. The researcher gets an email with the decision (printed in the terminal
   while we develop) and sees it on their dashboard.
3. Views with `@role_required("researcher", approved=True)` now let approved
   researchers in.

To protect a view, put the decorator on it:
```python
from accounts.permissions import role_required

@role_required("participant")
def my_page(request): ...

@role_required("researcher", approved=True)
def another_page(request): ...
```
Logged out people go to the login page and the wrong role gets the 403 page.

## What is where

```
config/            settings.py (reads .env, sessions, logging) and urls.py
accounts/          User (role, approved), ParticipantProfile, register, login, passwords
  permissions.py   the @role_required decorator
  signals.py       the activity log
  management/commands/seed_demo.py   the demo accounts
studies/           Study, StudySession and Application models
templates/         base.html (Bootstrap) and the page templates
```

## The models

**User** (`accounts.User`): the normal Django user plus `role` (`participant`,
`researcher` or `admin`), `approved`, `rejected` and `terms_accepted_at`. Participants are approved straight
away and superusers are always admins.

**ParticipantProfile** (`accounts`): one per participant. It is made
automatically when a participant account is saved, however the account was
made. The fields are bands: `age_band`, `education_level`, `health_condition`.
`sensitive_consent` and `sensitive_consent_at` record consent for the health
answer, and `last_edited_at` is what the edit cooldown checks.

**Study** (`studies`): `researcher`, `title`, `description`,
`time_commitment_minutes`, `reward`, `status` (draft, open or closed),
`category`, `max_participants`, `start_date`, `end_date`,
`application_deadline` and `consent_text` (the consent form people read before
applying). It also has three lists of accepted bands: `allowed_age_bands`,
`allowed_education_levels` and `allowed_health_conditions`. An empty list means
anyone can take part.

**StudySession** (`studies`): `study` and `starts_at`, one for each date and time
a study meets. Reminders are sent before each one. Sessions are added on the
study's page in the admin.

**Application** (`studies`): `participant`, `study`, `status` (pending,
accepted, rejected or withdrawn), `applied_at` and `consented_at`. A
participant can only apply once to each study.

## Changing the models

1. Edit `models.py`.
2. Run `python manage.py makemigrations` then `python manage.py migrate`.
3. Commit the new file in the `migrations` folder with your change.

Pull before you migrate.

## Git

Never commit `.env`, `db.sqlite3` or the `logs` folder, the `.gitignore` already
leaves them out (and `.venv` and `.idea` too). In PyCharm use the Git menu to make
a branch, then Commit and Push.
