#!/usr/bin/env python
"""Approve pending reports for testing"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jnmch_project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from reports.models import Report
from django.utils import timezone

# Get pending reports
pending = Report.objects.filter(status="pending")

print(f"Found {pending.count()} pending reports\n")

for report in pending:
    print(f"Approving: {report.test_name}")
    report.status = "downloadable"
    report.verified_at = timezone.now()
    report.save()
    print(f"  Status: {report.status}")

print(f"\nAll {pending.count()} reports approved!")
