"""
Management command to fix variant size values in the database.
Converts old free-text values to valid SIZE_CHOICES codes.
"""
from django.core.management.base import BaseCommand
from store.models import ProductVariant


class Command(BaseCommand):
    help = 'Fixes variant size values to match SIZE_CHOICES codes'

    # Mapping from possible old values to correct codes
    SIZE_MAPPING = {
        # ALL variations
        'all': 'ALL',
        'all size': 'ALL',
        'allsize': 'ALL',
        'all-size': 'ALL',
        'free': 'ALL',
        'free size': 'ALL',
        'freesize': 'ALL',
        'one size': 'ALL',
        'onesize': 'ALL',
        # S variations
        's': 'S',
        'small': 'S',
        'kecil': 'S',
        # M variations
        'm': 'M',
        'medium': 'M',
        'med': 'M',
        'sedang': 'M',
        # L variations
        'l': 'L',
        'large': 'L',
        'besar': 'L',
        # XL variations
        'xl': 'XL',
        'extra large': 'XL',
        'extralarge': 'XL',
        'extra-large': 'XL',
        'ekstra besar': 'XL',
    }

    def handle(self, *args, **options):
        variants = ProductVariant.objects.all()
        updated_count = 0
        
        for variant in variants:
            old_size = variant.size
            size_lower = old_size.lower().strip() if old_size else ''
            
            # Check if already a valid choice
            valid_codes = ['ALL', 'S', 'M', 'L', 'XL']
            if old_size in valid_codes:
                continue
            
            # Try to map to a valid code
            if size_lower in self.SIZE_MAPPING:
                new_size = self.SIZE_MAPPING[size_lower]
                variant.size = new_size
                variant.save(update_fields=['size'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated variant {variant.id}: "{old_size}" -> "{new_size}"'
                    )
                )
            else:
                # Default to ALL if no mapping found
                variant.size = 'ALL'
                variant.save(update_fields=['size'])
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Unknown size "{old_size}" for variant {variant.id} - defaulted to "ALL"'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nDone! Updated {updated_count} variant(s).')
        )
