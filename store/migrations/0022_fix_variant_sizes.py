# Generated data migration to fix variant size values
from django.db import migrations


def fix_variant_sizes(apps, schema_editor):
    """
    Convert old free-text size values to valid SIZE_CHOICES codes.
    """
    ProductVariant = apps.get_model('store', 'ProductVariant')
    
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
    
    valid_codes = ['ALL', 'S', 'M', 'L', 'XL']
    
    for variant in ProductVariant.objects.all():
        old_size = variant.size
        
        # Skip if already valid
        if old_size in valid_codes:
            continue
            
        size_lower = old_size.lower().strip() if old_size else ''
        
        if size_lower in SIZE_MAPPING:
            variant.size = SIZE_MAPPING[size_lower]
        else:
            # Default to ALL if unknown
            variant.size = 'ALL'
        
        variant.save(update_fields=['size'])


def reverse_migration(apps, schema_editor):
    # No reverse needed - data was already inconsistent
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0021_alter_offlinesale_options_order_cashier_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_variant_sizes, reverse_migration),
    ]
