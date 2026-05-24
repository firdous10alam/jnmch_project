# Generated migration for ReportAccessAudit model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0004_encrypt_existing_report_files'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportAccessAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_type', models.CharField(choices=[('view', 'View'), ('download', 'Download'), ('denied', 'Access Denied')], max_length=20)),
                ('status', models.CharField(choices=[('success', 'Success'), ('denied', 'Denied')], max_length=20)),
                ('reason', models.CharField(blank=True, max_length=255, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('accessed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_logs', to='reports.report')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='report_accesses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-accessed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='reportaccessaudit',
            index=models.Index(fields=['report', '-accessed_at'], name='reports_rep_report_idx'),
        ),
        migrations.AddIndex(
            model_name='reportaccessaudit',
            index=models.Index(fields=['user', '-accessed_at'], name='reports_rep_user_idx'),
        ),
    ]
