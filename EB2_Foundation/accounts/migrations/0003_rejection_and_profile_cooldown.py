from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_terms_accepted_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='participantprofile',
            name='last_edited_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='rejected',
            field=models.BooleanField(default=False, help_text='An admin has turned this researcher down.'),
        ),
    ]
