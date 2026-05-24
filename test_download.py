#!/usr/bin/env python
"""Test download endpoint"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jnmch_project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from reports.models import Report
from reports.file_crypto import decrypt_report_bytes

# Get first report
report = Report.objects.first()

if report:
    print(f"Report: {report.test_name}")
    print(f"Status: {report.status}")
    print(f"File path: {report.file.name}")
    
    # Read encrypted file
    with report.file.open("rb") as f:
        encrypted_bytes = f.read()
    
    print(f"\nEncrypted file size: {len(encrypted_bytes)} bytes")
    print(f"Encrypted first 50 chars: {encrypted_bytes[:50]}")
    
    # Decrypt
    try:
        decrypted_bytes = decrypt_report_bytes(encrypted_bytes)
        print(f"\nDecrypted file size: {len(decrypted_bytes)} bytes")
        print(f"Decrypted first 50 bytes: {decrypted_bytes[:50]}")
        
        # Check if it's a PDF
        if decrypted_bytes.startswith(b'%PDF'):
            print("\nSUCCESS: File is a valid PDF!")
        else:
            print(f"\nWARNING: File doesn't start with PDF header")
            print(f"Starts with: {decrypted_bytes[:20]}")
    except Exception as e:
        print(f"\nERROR during decryption: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No reports found")
