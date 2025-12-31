from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order, Profile, Address

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True); first_name = forms.CharField(max_length=30, required=True); last_name = forms.CharField(max_length=30, required=True)
    class Meta: model = User; fields = ['username', 'first_name', 'last_name', 'email']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items(): field.widget.attrs.update({'class': 'input input-bordered w-full'})
    def save(self, commit=True):
        user = super().save(commit=False); user.first_name = self.cleaned_data["first_name"]; user.last_name = self.cleaned_data["last_name"]; user.email = self.cleaned_data["email"]
        if commit: user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}), 'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}), 'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'})}

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']
        widgets = {'image': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full'})}

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone_number', 'address_line', 'city', 'postal_code', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'address_line': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'city': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'postal_code': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }

class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1, label="Jumlah", widget=forms.NumberInput(attrs={'class': 'input input-bordered w-24 text-center'}))
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)
    variant_id = forms.IntegerField(widget=forms.HiddenInput)


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order; fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']
        widgets = {'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Nama Depan'}), 'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Nama Belakang'}), 'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Email'}), 'address': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Alamat Lengkap'}), 'postal_code': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Kode Pos'}), 'city': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Kota'})}

class ReduceStockForm(forms.Form):
    channel = forms.ChoiceField(
        choices=[
            ('offline', 'Offline'),
            ('wa', 'WhatsApp'),
            ('ig', 'Instagram'),
            ('mp', 'Marketplace'),
        ]
    )


