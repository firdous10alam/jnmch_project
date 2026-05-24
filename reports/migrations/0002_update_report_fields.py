# reports/migrations/0002_update_report_fields.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        # Add new fields to Report
        migrations.AddField(
            model_name='report',
            name='test_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='report',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
        
        # Update file field path
        migrations.AlterField(
            model_name='report',
            name='file',
            field=models.FileField(upload_to='reports/%Y/%m/'),
        ),
        
        # Update choices for status
        migrations.AlterField(
            model_name='report',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('verified', 'Verified'),
                    ('downloadable', 'Downloadable'),
                    ('rejected', 'Rejected'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
        
        # Update relationship  
        migrations.AlterField(
            model_name='report',
            name='patient',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name='reports',
                to='accounts.Patient',
            ),
        ),
    ]
