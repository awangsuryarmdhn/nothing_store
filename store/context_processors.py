from .cart import Cart
from django.conf import settings

def cart(request):
    return {'cart': Cart(request)}

def appwrite_settings(request):
    return {
        'settings': {
            'APPWRITE_PROJECT_ID': settings.APPWRITE_PROJECT_ID,
            'APPWRITE_DATABASE_ID': settings.APPWRITE_DATABASE_ID,
            'APPWRITE_PRODUCT_STOCK_COLLECTION_ID': settings.APPWRITE_PRODUCT_STOCK_COLLECTION_ID,
        }
    }