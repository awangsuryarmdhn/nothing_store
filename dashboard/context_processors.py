from store.models import ProductVariant

def stock_notifications(request):
    low_stock_threshold = 5
    # Get variants with stock below threshold
    low_stock_variants = ProductVariant.objects.filter(stock__lte=low_stock_threshold).select_related('product')
    
    return {
        'low_stock_count': low_stock_variants.count(),
        'low_stock_items': low_stock_variants[:5] # Limit for UI
    }
