#!/usr/bin/env python
"""Test encryption and decryption"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jnmch_project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from reports.file_crypto import encrypt_report_bytes, decrypt_report_bytes

# Test data
test_data = b"%PDF-1.4\nTest PDF content"

print("=" * 60)
print("ENCRYPTION/DECRYPTION TEST")
print("=" * 60)

# Test encryption
print("\n1. Original data:")
print(f"   Size: {len(test_data)} bytes")
print(f"   Content: {test_data[:50]}")

encrypted = encrypt_report_bytes(test_data)
print("\n2. Encrypted data:")
print(f"   Size: {len(encrypted)} bytes")
print(f"   Content: {encrypted[:50]}")

# Test decryption
decrypted = decrypt_report_bytes(encrypted)
print("\n3. Decrypted data:")
print(f"   Size: {len(decrypted)} bytes")
print(f"   Content: {decrypted[:50]}")

# Verify
if decrypted == test_data:
    print("\n✅ SUCCESS: Encryption/Decryption working correctly!")
else:
    print("\n❌ FAILED: Decrypted data doesn't match original!")

# Test with actual file
print("\n" + "=" * 60)
print("TESTING WITH ACTUAL ENCRYPTED FILE")
print("=" * 60)

from reports.models import Report

try:
    report = Report.objects.first()
    if report:
        print(f"\nReport: {report.test_name}")
        print(f"File: {report.file.name}")
        
        with report.file.open("rb") as f:
            encrypted_bytes = f.read()
        
        print(f"Encrypted size: {len(encrypted_bytes)} bytes")
        print(f"First 50 bytes: {encrypted_bytes[:50]}")
        
        try:
            decrypted_bytes = decrypt_report_bytes(encrypted_bytes)
            print(f"\n✅ Decryption successful!")
            print(f"Decrypted size: {len(decrypted_bytes)} bytes")
            print(f"First 50 bytes: {decrypted_bytes[:50]}")
        except Exception as e:
            print(f"\n❌ Decryption failed: {e}")
    else:
        print("No reports found in database")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
