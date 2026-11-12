import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0002_study_dates_category_consent'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudySession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('starts_at', models.DateTimeField()),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='studies.study')),
            ],
            options={
                'ordering': ['starts_at'],
            },
        ),
    ]
