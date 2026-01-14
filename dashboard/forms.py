from django import forms
from django.forms import inlineformset_factory
from store.models import Product, ProductVariant, ProductImage, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'slug', 'category', 'description', 'price', 'available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full bg-black/30 border border-brand-gray rounded-lg px-4 py-2 text-white', 'placeholder': 'Nama Produk'}),
            'slug': forms.TextInput(attrs={'class': 'w-full bg-black/30 border border-brand-gray rounded-lg px-4 py-2 text-white', 'placeholder': 'Slug URL'}),
            'category': forms.Select(attrs={'class': 'w-full bg-black/30 border border-brand-gray rounded-lg px-4 py-2 text-white'}),
            'description': forms.Textarea(attrs={'class': 'w-full bg-black/30 border border-brand-gray rounded-lg px-4 py-2 text-white h-32', 'placeholder': 'Deskripsi Produk'}),
            'price': forms.NumberInput(attrs={'class': 'w-full bg-black/30 border border-brand-gray rounded-lg px-4 py-2 text-white', 'placeholder': '0'}),
            'available': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-gray-300 text-brand-accent focus:ring-brand-accent'}),
        }
    


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['color', 'size', 'stock', 'price']
        widgets = {
            'color': forms.TextInput(attrs={'class': 'w-full bg-black/30 border border-brand-gray rounded-lg px-3 py-1 text-white text-sm', 'placeholder': 'Warna'}),
            'size': forms.TextInput(attrs={'class': 'w-full bg-black/30 border border-brand-gray rounded-lg px-3 py-1 text-white text-sm', 'placeholder': 'Ukuran'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full bg-black/30 border border-brand-gray rounded-lg px-3 py-1 text-white text-sm', 'placeholder': '0'}),
            'price': forms.NumberInput(attrs={'class': 'w-full bg-black/30 border border-brand-gray rounded-lg px-3 py-1 text-white text-sm', 'placeholder': 'Opsional (Override)'}),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'text-white text-sm'}),
        }

# Inline Formsets
VariantFormSet = inlineformset_factory(
    Product, ProductVariant, form=ProductVariantForm,
    extra=1, can_delete=True
)

ImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm,
    extra=1, can_delete=True
)
