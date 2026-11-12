from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='application_deadline',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='study',
            name='category',
            field=models.CharField(blank=True, choices=[('social_sciences', 'Social sciences'), ('health', 'Health'), ('psychology', 'Psychology'), ('other', 'Other')], max_length=20),
        ),
        migrations.AddField(
            model_name='study',
            name='consent_text',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='study',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='study',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='application',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('withdrawn', 'Withdrawn')], default='pending', max_length=10),
        ),
    ]
