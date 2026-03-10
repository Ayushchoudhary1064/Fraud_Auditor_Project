from django.core.management.base import BaseCommand
from django.db.models import Count
from auditor.models import Claim

class Command(BaseCommand):
    help = 'Remove duplicate claims by claim_id, keeping only the most recent one'

    def handle(self, *args, **kwargs):
        duplicates = Claim.objects.values('claim_id').annotate(count=Count('id')).filter(count__gt=1)
        total_removed = 0

        for dup in duplicates:
            claim_id = dup['claim_id']
            claims = Claim.objects.filter(claim_id=claim_id).order_by('-submitted_at')
            to_delete = claims[1:]  # Keep the newest one
            count = len(to_delete)
            total_removed += count
            for obj in to_delete:
                obj.delete()  # Deleting objects individually

        self.stdout.write(self.style.SUCCESS(f"Removed {total_removed} duplicate claim(s)."))