#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jnmch_project.settings')
django.setup()

from reports.serializers import ReportUploadSerializer
from accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

# Create test data
test_file = SimpleUploadedFile("test.txt", b"test file content", content_type="text/plain")

test_data = {
    'registration_id': 'REG-F8E3000E',
    'test_name': 'Test Report',
    'test_type': 'blood',
    'is_critical': 'true',
    'comments': 'Test comments',
    'file': test_file
}

# Create a fake request
class FakeRequest:
    user = User.objects.get(username='firdaus_11')

# Test the serializer
serializer = ReportUploadSerializer(data=test_data, context={'request': FakeRequest()})
print("Testing serializer with data:")
print(f"  registration_id: {test_data['registration_id']}")
print(f"  test_name: {test_data['test_name']}")
print(f"  test_type: {test_data['test_type']}")
print(f"  is_critical: {test_data['is_critical']}")
print(f"  comments: {test_data['comments']}")
print()

if serializer.is_valid():
    print("✓ Serializer is valid!")
    print("Validated data keys:", list(serializer.validated_data.keys()))
else:
    print("✗ Serializer validation failed!")
    print("Errors:")
    for field, errors in serializer.errors.items():
        print(f"  {field}: {errors}")
