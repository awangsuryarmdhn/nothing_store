from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    # Arahkan semua URL root ke file urls.py milik aplikasi 'store'
    path('', include('store.urls')),
]

# Baris ini penting agar file media (gambar produk) dapat diakses
# selama masa pengembangan (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
