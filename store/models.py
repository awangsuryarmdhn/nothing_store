from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class AboutPageContent(models.Model):
    title = models.CharField("Judul Halaman", max_length=100, default="TENTANG NOTHING_BRAIN")
    subtitle = models.CharField("Subjudul Halaman", max_length=200, default="Kami bukan sekadar merek. Kami adalah sebuah ide.")
    philosophy_title = models.CharField("Judul Filosofi", max_length=100, default="FILOSOFI KAMI")
    philosophy_text = models.TextField("Teks Filosofi", default="Isi teks filosofi di sini.")
    philosophy_image = models.ImageField("Gambar Filosofi", upload_to='about_us/')
    community_title = models.CharField("Judul Komunitas", max_length=100, default="BERGABUNG DENGAN KAMI")
    community_text = models.TextField("Teks Komunitas", default="Isi teks komunitas di sini.")

    class Meta:
        verbose_name = "Konten Halaman Tentang Kami"
        verbose_name_plural = "Konten Halaman Tentang Kami"

    def __str__(self):
        return "Pengaturan Konten Halaman Tentang Kami"


class LandingPageContent(models.Model):
    hero_title = models.CharField("Judul Hero", max_length=100, default="BEYOND THE NOISE")
    hero_subtitle = models.CharField("Subjudul Hero", max_length=200, default="Gaya adalah pemberontakan. Temukan identitas Anda.")
    hero_image = models.ImageField("Gambar Latar Hero", upload_to='landing_page/')

    class Meta:
        verbose_name = "Konten Landing Page"
        verbose_name_plural = "Konten Landing Page"

    def __str__(self):
        return "Pengaturan Konten Landing Page"


class Category(models.Model):
    name = models.CharField("Nama Kategori", max_length=200, db_index=True)
    slug = models.SlugField("Slug", max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'kategori'
        verbose_name_plural = 'kategori'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_list_by_category', args=[self.slug])


class FeaturedCollection(models.Model):
    title = models.CharField("Judul Koleksi", max_length=50)
    image = models.ImageField("Gambar Koleksi", upload_to='featured_collections/')
    link = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Kategori Terkait")

    class Meta:
        verbose_name = "Koleksi Pilihan"
        verbose_name_plural = "Koleksi Pilihan"

    def __str__(self):
        return self.title


class LookbookImage(models.Model):
    image = models.ImageField("Gambar Lookbook", upload_to='lookbook/')
    order = models.PositiveIntegerField("Urutan", default=0, help_text="Gambar dengan urutan lebih kecil akan tampil lebih dulu.")

    class Meta:
        ordering = ['order']
        verbose_name = "Gambar Lookbook"
        verbose_name_plural = "Gambar Lookbook"

    def __str__(self):
        return f"Gambar Lookbook #{self.order}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField("Foto Profil", default='default.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'Profil {self.user.username}'


class Address(models.Model):
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE)
    full_name = models.CharField("Nama Lengakap", max_length=100)
    phone_number = models.CharField("Nomor Telepon", max_length=20)
    address_line = models.CharField("Alamat", max_length=250)
    city = models.CharField("Kota", max_length=100)
    postal_code = models.CharField("Kode Pos", max_length=20)
    is_default = models.BooleanField("Jadikan Alamat Utama", default=False)

    class Meta:
        verbose_name = "Alamat"
        verbose_name_plural = "Alamat"

    def __str__(self):
        return f"Alamat untuk {self.user.username}"


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, verbose_name="Kategori")
    name = models.CharField("Nama Produk", max_length=200, db_index=True)
    slug = models.SlugField("Slug", max_length=200, db_index=True)
    description = models.TextField("Deskripsi", blank=True)
    price = models.DecimalField("Harga Dasar", max_digits=10, decimal_places=0, help_text="Harga dasar produk.")
    available = models.BooleanField("Tersedia", default=True)
    created = models.DateTimeField("Dibuat", auto_now_add=True)
    updated = models.DateTimeField("Diperbarui", auto_now=True)

    class Meta:
        ordering = ('name',)
        indexes = [
            models.Index(fields=['id', 'slug']),
        ]
        verbose_name = 'produk'
        verbose_name_plural = 'produk'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.id, self.slug])

    @property
    def main_image(self):
        return self.images.first()

    @property
    def total_stock(self):
        return self.variants.aggregate(total=Sum('stock'))['total'] or 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField("Gambar", upload_to='products/%Y/%m/%d')

    class Meta:
        verbose_name = "Gambar Produk"
        verbose_name_plural = "Galeri Gambar Produk"

    def __str__(self):
        return f"Gambar untuk {self.product.name}"


class ProductVariant(models.Model):
    SIZE_CHOICES = [('S', 'Small'), ('M', 'Medium'), ('L', 'Large'), ('XL', 'Extra Large')]

    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color = models.CharField("Nama Warna", max_length=50, help_text="Contoh: Hitam, Putih, Merah")
    size = models.CharField("Ukuran", max_length=10, choices=SIZE_CHOICES)
    stock = models.PositiveIntegerField("Stok", default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'color', 'size'],
                name='unique_variant_per_product'
            )
        ]
        verbose_name = 'varian produk'
        verbose_name_plural = 'varian produk'

    def __str__(self):
        return f'{self.product.name} - {self.color} ({self.size})'


class Coupon(models.Model):
    code = models.CharField("Kode Kupon", max_length=50, unique=True)
    valid_from = models.DateTimeField("Berlaku Dari")
    valid_to = models.DateTimeField("Berlaku Hingga")
    discount = models.IntegerField("Diskon (%)", validators=[MinValueValidator(0), MaxValueValidator(100)])
    active = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Kupon"
        verbose_name_plural = "Kupon"

    def __str__(self):
        return self.code


class Order(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'))

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Pengguna")
    first_name = models.CharField("Nama Depan", max_length=50)
    last_name = models.CharField("Nama Belakang", max_length=50)
    email = models.EmailField("Email")
    address = models.CharField("Alamat", max_length=250)
    postal_code = models.CharField("Kode Pos", max_length=20)
    city = models.CharField("Kota", max_length=100)
    shipping_option = models.CharField("Opsi Pengiriman", max_length=50, default="Jasa Kirim Toko")
    shipping_cost = models.DecimalField("Biaya Pengiriman", max_digits=10, decimal_places=0, default=15000)

    created = models.DateTimeField("Dibuat", auto_now_add=True)
    updated = models.DateTimeField("Diperbarui", auto_now=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    midtrans_snap_token = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'pesanan'
        verbose_name_plural = 'pesanan'

    def __str__(self):
        return f'Pesanan {self.id}'

    def get_total_cost(self):
        subtotal = sum(item.get_cost() for item in self.items.all())
        return subtotal + self.shipping_cost


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, related_name='order_items', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField("Harga", max_digits=10, decimal_places=0)
    quantity = models.PositiveIntegerField("Jumlah", default=1)

    class Meta:
        verbose_name = 'item pesanan'
        verbose_name_plural = 'item pesanan'

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity
    

class OfflineSale(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=0)

    channel = models.CharField(
        max_length=50,
        choices=[
            ('offline', 'Offline'),
            ('wa', 'WhatsApp'),
            ('ig', 'Instagram'),
            ('mp', 'Marketplace'),
        ]
    )

    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.variant} - {self.channel}"

