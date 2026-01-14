import os
import django
import sys

# 1. Setup Django Environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nothing_brain_project.settings')
django.setup()

from store.models import Product, ProductVariant, Category
from django.db.models import Count

def run_fix():
    print("=== MULAI MEMPERBAIKI UKURAN ===")

    # 2. Tentukan target yang harusnya All Size
    # Kita cari berdasarkan nama kategori "Accessories" atau kata kunci nama produk
    target_products = Product.objects.filter(category__name__icontains='Accessories') | \
                      Product.objects.filter(name__icontains='Totebag') | \
                      Product.objects.filter(name__icontains='Slingbag') | \
                      Product.objects.filter(name__icontains='Hat')

    # Hilangkan duplikat hasil query (karena pakai OR |)
    target_products = target_products.distinct()

    if not target_products.exists():
        print("Tidak ada produk target ditemukan.")
        return

    count_fixed = 0

    for product in target_products:
        print(f"\nMemproses: {product.name}...")
        
        # Ambil semua warna yang ada di produk ini
        existing_colors = product.variants.values_list('color', flat=True).distinct()

        for color in existing_colors:
            # Cari semua varian dengan warna tersebut (misal: Hitam S, Hitam M, Hitam L)
            variants_same_color = product.variants.filter(color=color)
            
            # Kita ambil varian PERTAMA untuk dijadikan 'All Size'
            primary_variant = variants_same_color.first()
            
            # Jika ada varian lain (duplikat), kita hapus sisanya agar tidak error "UniqueConstraint"
            duplicates = variants_same_color.exclude(id=primary_variant.id)
            if duplicates.exists():
                print(f"   - Menghapus {duplicates.count()} varian duplikat untuk warna {color}")
                duplicates.delete()

            # Update varian utama jadi All Size
            if primary_variant.size != 'All Size':
                primary_variant.size = 'All Size'
                primary_variant.save()
                print(f"   [OK] Warna {color} diubah menjadi 'All Size'")
                count_fixed += 1
            else:
                print(f"   [SKIP] Warna {color} sudah benar")

    print(f"\n=== SELESAI! Total {count_fixed} varian berhasil diperbaiki. ===")

if __name__ == '__main__':
    run_fix()