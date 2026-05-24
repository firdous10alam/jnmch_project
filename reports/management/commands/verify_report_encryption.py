from django.core.management.base import BaseCommand
from reports.models import Report
from reports.file_crypto import decrypt_report_bytes
from cryptography.fernet import InvalidToken
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verify all reports are encrypted and can be decrypted'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix unencrypted reports',
        )

    def handle(self, *args, **options):
        reports = Report.objects.all()
        total = reports.count()
        encrypted_count = 0
        unencrypted_count = 0
        corrupted_count = 0

        self.stdout.write(f"Checking {total} reports...")

        for report in reports:
            try:
                with report.file.open('rb') as f:
                    data = f.read()
                
                try:
                    decrypt_report_bytes(data)
                    encrypted_count += 1
                except InvalidToken:
                    unencrypted_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Unencrypted: {report.report_id} - {report.test_name}"
                        )
                    )
                    
                    if options['fix']:
                        from reports.file_crypto import encrypt_report_bytes
                        from django.core.files.base import ContentFile
                        
                        encrypted = encrypt_report_bytes(data)
                        report.file.save(
                            f"{report.file.name}.enc",
                            ContentFile(encrypted),
                            save=True
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f"Fixed: {report.report_id}")
                        )
                        encrypted_count += 1
                        unencrypted_count -= 1
                        
            except Exception as e:
                corrupted_count += 1
                logger.exception(f"Error checking report {report.report_id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"Corrupted: {report.report_id} - {str(e)}")
                )

        self.stdout.write(self.style.SUCCESS(f"\n=== Encryption Status ==="))
        self.stdout.write(f"Total reports: {total}")
        self.stdout.write(self.style.SUCCESS(f"Encrypted: {encrypted_count}"))
        if unencrypted_count > 0:
            self.stdout.write(self.style.WARNING(f"Unencrypted: {unencrypted_count}"))
        if corrupted_count > 0:
            self.stdout.write(self.style.ERROR(f"Corrupted: {corrupted_count}"))
