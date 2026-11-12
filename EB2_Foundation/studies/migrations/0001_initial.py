import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Study',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('time_commitment_minutes', models.PositiveIntegerField(help_text='How long taking part takes, in minutes.')),
                ('reward', models.CharField(blank=True, help_text='For example: £5 voucher, or no reward.', max_length=200)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('open', 'Open'), ('closed', 'Closed')], default='draft', max_length=10)),
                ('max_participants', models.PositiveIntegerField(blank=True, null=True)),
                ('allowed_age_bands', models.JSONField(blank=True, default=list)),
                ('allowed_education_levels', models.JSONField(blank=True, default=list)),
                ('allowed_health_conditions', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('researcher', models.ForeignKey(limit_choices_to={'role': 'researcher'}, on_delete=django.db.models.deletion.CASCADE, related_name='studies', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'studies',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending', max_length=10)),
                ('applied_at', models.DateTimeField(auto_now_add=True)),
                ('consented_at', models.DateTimeField(blank=True, null=True)),
                ('participant', models.ForeignKey(limit_choices_to={'role': 'participant'}, on_delete=django.db.models.deletion.CASCADE, related_name='applications', to=settings.AUTH_USER_MODEL)),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='studies.study')),
            ],
            options={
                'ordering': ['-applied_at'],
                'constraints': [models.UniqueConstraint(fields=('participant', 'study'), name='one_application_per_study')],
            },
        ),
    ]
