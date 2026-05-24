# accounts/migrations/0002_update_patient_and_user.py
from django.db import migrations, models
from django.utils import timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Add new fields to Patient
        migrations.AddField(
            model_name='patient',
            name='aadhaar',
            field=models.CharField(
                blank=True, max_length=64, null=True, unique=True
            ),
        ),
        migrations.AddField(
            model_name='patient',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='uhid',
            field=models.CharField(
                blank=True, max_length=128, null=True, unique=True
            ),
        ),
        migrations.AddField(
            model_name='patient',
            name='created_at',
            field=models.DateTimeField(default=timezone.now),
        ),
        
        # Update gender field
        migrations.AlterField(
            model_name='patient',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
                max_length=10,
                null=True,
            ),
        ),
        
        # Add related_name to Patient user field
        migrations.AlterField(
            model_name='patient',
            name='user',
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                primary_key=True,
                related_name='patient_profile',
                serialize=False,
                to='accounts.User',
            ),
        ),
        
        # Add related_name to Doctor
        migrations.AlterField(
            model_name='doctor',
            name='user',
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                primary_key=True,
                related_name='doctor_profile',
                serialize=False,
                to='accounts.User',
            ),
        ),
        
        # Add related_name to LabTechnician
        migrations.AlterField(
            model_name='labtechnician',
            name='user',
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                primary_key=True,
                related_name='labtechnician_profile',
                serialize=False,
                to='accounts.User',
            ),
        ),
    ]
