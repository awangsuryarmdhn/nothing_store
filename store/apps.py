from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        import store.signals
        
        # Auto-fix variant sizes on startup (for Vercel where migrations don't run easily)
        self._fix_variant_sizes()
    
    def _fix_variant_sizes(self):
        """
        Automatically fix variant size values to match SIZE_CHOICES.
        This runs on app startup to ensure data consistency.
        """
        import os
        # Only run in production and avoid running during collectstatic/migrate
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('VERCEL'):
            try:
                from store.models import ProductVariant
                
                SIZE_MAPPING = {
                    'all': 'ALL', 'all size': 'ALL', 'allsize': 'ALL', 
                    'free': 'ALL', 'free size': 'ALL', 'freesize': 'ALL',
                    'one size': 'ALL', 'onesize': 'ALL',
                    's': 'S', 'small': 'S', 'kecil': 'S',
                    'm': 'M', 'medium': 'M', 'sedang': 'M',
                    'l': 'L', 'large': 'L', 'besar': 'L',
                    'xl': 'XL', 'extra large': 'XL', 'extralarge': 'XL',
                }
                
                valid_codes = ['ALL', 'S', 'M', 'L', 'XL']
                
                # Find variants with invalid sizes
                variants_to_fix = ProductVariant.objects.exclude(size__in=valid_codes)
                
                for variant in variants_to_fix:
                    old_size = variant.size
                    size_lower = old_size.lower().strip() if old_size else ''
                    
                    if size_lower in SIZE_MAPPING:
                        variant.size = SIZE_MAPPING[size_lower]
                    else:
                        variant.size = 'ALL'  # Default
                    
                    variant.save(update_fields=['size'])
                    print(f"[AUTO-FIX] Variant {variant.id}: '{old_size}' -> '{variant.size}'")
                    
            except Exception as e:
                # Silently ignore if database not ready (first deploy, etc)
                print(f"[AUTO-FIX] Skipped: {e}")
