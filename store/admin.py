from django.contrib import admin
from .models import *

@admin.register(AboutPageContent)
class AboutPageContentAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not AboutPageContent.objects.exists()
        
@admin.register(LandingPageContent)
class LandingPageContentAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return not LandingPageContent.objects.exists()

@admin.register(FeaturedCollection)
class FeaturedCollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'link')

@admin.register(LookbookImage)
class LookbookImageAdmin(admin.ModelAdmin):
    list_display = ('order', 'image'); list_editable = ('order',); list_display_links = ('image',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage; extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant; extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'slug',
        'category',
        'price',
        'available',
        'created',
        'updated',
    ]

    list_filter = [
        'available',
        'category',
        'created',
        'updated',
    ]

    list_editable = [
        'price',
        'available',
    ]

    search_fields = [
        'name',
        'slug',
    ]

    prepopulated_fields = {
        'slug': ('name',),
    }

    inlines = [
        ProductImageInline,
        ProductVariantInline,
    ]

    change_form_template = 'admin/store/product/change_form.html'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product', 'variant']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # DIPERBARUI: Mengganti 'paid' dengan 'status'
    list_display = ['id', 'user', 'first_name', 'last_name', 'email', 'status', 'created']
    list_filter = ['status', 'created', 'updated']
    inlines = [OrderItemInline]



# BARU: Mendaftarkan model Address dan Profile
admin.site.register(Address)
admin.site.register(Profile)