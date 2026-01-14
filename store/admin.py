from django.contrib import admin
from django.utils.html import mark_safe
from .models import (
    AboutPageContent, LandingPageContent, FeaturedCollection, LookbookImage,
    Category, Product, ProductImage, ProductVariant,
    Order, OrderItem, Coupon, Address, Profile, OfflineSale
)

# ==========================================
# KONFIGURASI TAMPILAN DASAR
# ==========================================
admin.site.site_header = "NOTHING BRAIN | HQ"
admin.site.site_title = "Nothing Brain Admin"
admin.site.index_title = "Management Console"


# ==========================================
# 1. CMS (CONTENT MANAGEMENT)
# ==========================================

@admin.register(LandingPageContent)
class LandingPageContentAdmin(admin.ModelAdmin):
    """Mengatur konten Halaman Depan (Hero Section)"""
    list_display = ('hero_title', 'preview_image')
    
    def has_add_permission(self, request):
        # Mencegah pembuatan lebih dari 1 settingan homepage
        return not LandingPageContent.objects.exists()

    def preview_image(self, obj):
        if obj.hero_image:
            return mark_safe(f'<img src="{obj.hero_image.url}" style="height: 50px; border-radius: 5px;">')
        return "-"
    preview_image.short_description = "Preview Hero"


@admin.register(AboutPageContent)
class AboutPageContentAdmin(admin.ModelAdmin):
    """Mengatur konten Halaman Tentang Kami"""
    list_display = ('title', 'philosophy_title')
    
    fieldsets = (
        ('Header Section', {
            'fields': ('title', 'subtitle')
        }),
        ('Filosofi Section', {
            'fields': ('philosophy_title', 'philosophy_text', 'philosophy_image')
        }),
        ('Komunitas Section', {
            'fields': ('community_title', 'community_text')
        }),
    )

    def has_add_permission(self, request):
        return not AboutPageContent.objects.exists()


@admin.register(FeaturedCollection)
class FeaturedCollectionAdmin(admin.ModelAdmin):
    """Koleksi yang muncul di Grid Homepage"""
    list_display = ('title', 'link', 'preview_image')
    
    def preview_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="height: 60px; border-radius: 5px;">')
        return "-"
    preview_image.short_description = "Cover Image"


@admin.register(LookbookImage)
class LookbookImageAdmin(admin.ModelAdmin):
    """Arsip Foto di bagian bawah Homepage"""
    # PERBAIKAN UTAMA DI SINI:
    # 1. ID ditaruh depan agar jadi link
    list_display = ('id', 'preview_image', 'order')
    
    # 2. Link hanya aktif di ID dan Gambar (bukan di Order)
    list_display_links = ('id', 'preview_image')
    
    # 3. Order jadi bisa diedit karena dia bukan link lagi
    list_editable = ('order',)
    
    ordering = ('order',)

    def preview_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="height: 80px; object-fit: cover;">')
        return "-"
    preview_image.short_description = "Lookbook Preview"


# ==========================================
# 2. PRODUK & KATALOG
# ==========================================

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['preview']
    
    def preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="height: 100px;">')
        return ""

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    min_num = 0
    # Menampilkan field harga agar admin bisa set harga beda per varian
    fields = ['color', 'size', 'stock', 'price']
    classes = ['collapse'] 

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count']
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Jumlah Produk"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name_preview',
        'category',
        'price_display',
        'total_stock_display',
        'available',
        'updated',
    ]
    list_filter = ['available', 'category', 'created']
    list_editable = ['available']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    save_on_top = True

    def name_preview(self, obj):
        img_url = obj.images.first().image.url if obj.images.first() else ""
        if img_url:
            return mark_safe(f'<div style="display:flex; align-items:center; gap:10px;"><img src="{img_url}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover;"> <span>{obj.name}</span></div>')
        return obj.name
    name_preview.short_description = "Produk"

    def price_display(self, obj):
        return f"Rp {obj.price:,.0f}"
    price_display.short_description = "Harga Dasar"

    def total_stock_display(self, obj):
        stock = obj.total_stock
        color = "green" if stock > 10 else "orange" if stock > 0 else "red"
        return mark_safe(f'<span style="color: {color}; font-weight: bold;">{stock} Unit</span>')
    total_stock_display.short_description = "Total Stok"


# ==========================================
# 3. TRANSAKSI & PENJUALAN
# ==========================================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product_info', 'quantity', 'price', 'get_cost']
    readonly_fields = ['product_info', 'price', 'get_cost']
    extra = 0
    can_delete = False

    def product_info(self, obj):
        if obj.variant:
            return f"{obj.product.name} ({obj.variant.color} / {obj.variant.size})"
        return obj.product.name
    product_info.short_description = "Item Dibeli"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_info', 'shipping_info', 'status_badge', 'total_display', 'created']
    list_filter = ['status', 'created', 'shipping_option']
    search_fields = ['id', 'first_name', 'email', 'midtrans_snap_token']
    inlines = [OrderItemInline]
    readonly_fields = ['midtrans_snap_token', 'created', 'updated']
    list_per_page = 20

    def user_info(self, obj):
        return f"{obj.first_name} {obj.last_name} ({obj.email})"
    user_info.short_description = "Pelanggan"

    def shipping_info(self, obj):
        return f"{obj.city} - {obj.shipping_option}"
    shipping_info.short_description = "Pengiriman"

    def total_display(self, obj):
        return f"Rp {obj.get_total_cost():,.0f}"
    total_display.short_description = "Total Bayar"

    def status_badge(self, obj):
        colors = {'pending': 'orange', 'paid': 'green', 'failed': 'red'}
        return mark_safe(f'<span style="background-color: {colors.get(obj.status, "grey")}; color: white; padding: 3px 8px; border-radius: 10px; font-size: 10px; text-transform: uppercase;">{obj.status}</span>')
    status_badge.short_description = "Status"


@admin.register(OfflineSale)
class OfflineSaleAdmin(admin.ModelAdmin):
    list_display = ['variant', 'quantity', 'price_display', 'channel', 'staff', 'created_at']
    list_filter = ['channel', 'staff', 'created_at']
    search_fields = ['variant__product__name', 'note']
    
    def price_display(self, obj):
        return f"Rp {obj.price:,.0f}"
    price_display.short_description = "Total Omset"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'valid_from', 'valid_to', 'active']
    list_filter = ['active', 'valid_to']


# ==========================================
# 4. USER & DATA PELENGKAP
# ==========================================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'image_preview']

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 30px; height: 30px; border-radius: 50%;">')
        return "-"

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'city', 'is_default']