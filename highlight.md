# 3.2.3.1 Struktur Proyek

Struktur proyek aplikasi dirancang menggunakan pola modular dengan memanfaatkan framework Django. Setiap komponen utama sistem dipisahkan ke dalam file dan modul yang memiliki tanggung jawab yang jelas, seperti pengelolaan model (models.py), antarmuka admin (admin.py), pengelolaan form (forms.py), pengaturan URL (urls.py), serta logika bisnis dan pengendali proses aplikasi (views.py). Pendekatan ini bertujuan untuk meningkatkan keterbacaan kode, mempermudah proses pengembangan, serta memudahkan pemeliharaan dan pengembangan sistem di masa mendatang.

Gambaran struktur direktori proyek adalah sebagai berikut:

```text
nothing_store/
├── dashboard/              # Modul Dashboard Admin
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── nothing_brain_project/  # Konfigurasi Utama Proyek
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── store/                  # Modul Utama Toko Online
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── midtrans_service.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── templates/              # Template HTML Global
├── static/                 # File Statis (CSS, JS, Images)
├── manage.py               # Utilitas Command Line Django
└── requirements.txt        # Daftar Dependensi Python
```

Berikut adalah potongan kode untuk konfigurasi dasar pada modul `store`:

**admin.py**
```python
# store/admin.py
admin.site.site_header = "NOTHING BRAIN | HQ"

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
    # ...
```

**models.py**
```python
# store/models.py
from django.db import models

class Category(models.Model):
    name = models.CharField("Nama Kategori", max_length=200, db_index=True)
    slug = models.SlugField("Slug", max_length=200, unique=True)
    # ...

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField("Nama Produk", max_length=200, db_index=True)
    slug = models.SlugField("Slug", max_length=200, db_index=True)
    price = models.DecimalField("Harga Dasar", max_digits=10, decimal_places=0)
    available = models.BooleanField("Tersedia", default=True)
    # ...
```

**urls.py**
```python
# store/urls.py
urlpatterns = [
    path('', views.landing_page_view, name='landing_page'),
    path('produk/', views.product_list, name='product_list'),
    path('produk/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('keranjang/', views.cart_detail, name='cart_detail'),
    path('checkout/', views.order_create, name='order_create'),
    # ...
]
```

<br>

# 3.2.3.2 Implementasi Models

Implementasi model basis data dilakukan menggunakan Django ORM untuk merepresentasikan struktur data sistem sesuai dengan perancangan ERD. Model yang diimplementasikan mencakup entitas pengguna, profil, alamat, kategori produk, produk, varian produk, pesanan, detail pesanan, dan kupon. Relasi antar entitas diatur menggunakan hubungan One-to-One dan One-to-Many guna menjaga integritas data. Selain itu, beberapa properti dan method tambahan seperti perhitungan total stok dan total biaya pesanan digunakan untuk mendukung logika bisnis sistem. Implementasi ini memastikan bahwa data yang disimpan selalu konsisten dan sesuai dengan kebutuhan sistem penjualan.

**models.py**
```python
# store/models.py

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField("Foto Profil", default='default.jpg', upload_to='profile_pics')

class Address(models.Model):
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE)
    address_line = models.CharField("Alamat", max_length=250)
    city = models.CharField("Kota", max_length=100)
    # ...

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color = models.CharField("Nama Warna", max_length=50)
    size = models.CharField("Ukuran", max_length=10)
    stock = models.PositiveIntegerField("Stok", default=0)
    price = models.DecimalField("Harga Varian", max_digits=10, decimal_places=0, null=True, blank=True)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    midtrans_order_id = models.CharField("Midtrans Order ID", max_length=100, blank=True, null=True)
    
    def get_total_cost(self):
        subtotal = self.get_subtotal()
        if self.discount and self.discount > 0:
            discount_amount = subtotal * self.discount / 100
            subtotal = subtotal - discount_amount
        return subtotal + self.shipping_cost

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, related_name='order_items', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField("Jumlah", default=1)
```

<br>

# 3.2.3.3 Implementasi API dan Logika Aplikasi

Logika aplikasi diimplementasikan melalui fungsi-fungsi pada berkas views.py yang berperan sebagai pengendali alur proses sistem. Fungsi-fungsi tersebut menangani proses utama seperti penampilan katalog produk, pengelolaan keranjang belanja, pembuatan pesanan, penerapan kupon, serta pengelolaan akun pengguna. Setiap proses dirancang untuk memvalidasi data masukan, memproses data sesuai aturan bisnis, dan menghasilkan keluaran yang sesuai. Pendekatan ini memungkinkan sistem backend berfungsi sebagai pusat pengelolaan logika aplikasi yang terstruktur.

**views.py**
```python
# store/views.py

def product_list(request, category_slug=None): 
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).select_related('category').prefetch_related('variants', 'images')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # ... logic search & sorting ...
    return render(request, "store/product_listing.html", context)

@login_required(login_url='store:login')
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    # ... logic add to cart ...
    cart.add(product=product, quantity=quantity, variant=variant_obj)
    return redirect('store:product_detail', id=product.id, slug=product.slug)

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            # ... process shipping cost logic ...
            order.save()
            # ... create OrderItems ...
            return render(request, 'store/payment.html', {'order': order, ...})
```

<br>

# 3.2.3.4 Implementasi Mekanisme Akurasi Stok

Pengelolaan stok dalam sistem ini menerapkan mekanisme pembaruan stok berbasis transaksi untuk menjaga keakuratan data. Stok produk divalidasi sebelum transaksi diproses dan dikurangi secara permanen hanya setelah pembayaran dinyatakan berhasil. Proses pengurangan stok dilakukan menggunakan transaksi database untuk mencegah inkonsistensi data akibat akses bersamaan. Dengan mekanisme ini, sistem tidak mengandalkan pembaruan stok secara real-time, namun tetap menjamin bahwa jumlah stok yang tersimpan di basis data selalu mencerminkan kondisi sebenarnya.

**models.py**
```python
# store/models.py
class ProductVariant(models.Model):
    # ...
    stock = models.PositiveIntegerField("Stok", default=0)
    # ...
```

**views.py**
```python
# store/views.py
from django.db import transaction
from django.db.models import F

# Pada saat webhook menerima status settlement/capture:
if is_paid:
    with transaction.atomic():
        order.status = 'paid'
        order.save()
        
        # Kurangi Stok
        for item in order.items.all():
            # Menggunakan F expressions untuk atomic update mencegah race condition
            item.variant.stock = F('stock') - item.quantity
            item.variant.save()
```

<br>

# 3.2.3.5 Integrasi Midtrans Payment Gateway

Integrasi payment gateway dilakukan menggunakan layanan Midtrans untuk menangani proses pembayaran secara aman dan terotomatisasi. Sistem mengirimkan data transaksi ke Midtrans untuk menghasilkan token pembayaran yang digunakan oleh pengguna saat melakukan pembayaran. Selanjutnya, sistem menerima notifikasi pembayaran melalui mekanisme webhook untuk memperbarui status pesanan. Pendekatan ini memungkinkan sistem memantau status pembayaran secara akurat dan menentukan kelanjutan proses transaksi secara otomatis.

**midtrans_service.py**
```python
# store/midtrans_service.py
import midtransclient

def create_snap_transaction(order):
    snap = midtransclient.Snap(
        is_production=settings.MIDTRANS_IS_PRODUCTION,
        server_key=settings.MIDTRANS_SERVER_KEY, 
        client_key=settings.MIDTRANS_CLIENT_KEY
    )
    
    transaction_details = {
        'order_id': order.midtrans_order_id,
        'gross_amount': int(order.get_total_cost())
    }
    # ... item details & customer details ...
    
    transaction = snap.create_transaction(params)
    return transaction['token'], order.midtrans_order_id
```

**views.py**
```python
# store/views.py
from .midtrans_service import create_snap_transaction

def order_create(request):
    # ... setelah order disimpan ...
    snap_token, midtrans_order_id = create_snap_transaction(order)
    
    if snap_token:
        order.midtrans_snap_token = snap_token
        order.midtrans_order_id = midtrans_order_id 
        order.save()
```

<br>

# 3.2.3.6 Implementasi Pembaruan Stok Setelah Pembayaran

Pembaruan stok dilakukan setelah sistem menerima konfirmasi pembayaran yang valid dari Midtrans. Pada tahap ini, status pesanan diperbarui menjadi berhasil dan jumlah stok produk dikurangi sesuai dengan jumlah pembelian. Proses ini dijalankan dalam satu transaksi database untuk memastikan konsistensi data. Dengan demikian, meskipun sistem tidak menggunakan mekanisme real-time, data stok yang tersimpan tetap akurat dan terjamin kebenarannya berdasarkan transaksi yang telah diselesaikan.

**views.py**
```python
# store/views.py

@csrf_exempt
def midtrans_webhook(request):
    # ... parsing response midtrans ...
    
    if is_paid:
        with transaction.atomic():
            order.status = 'paid'
            order.save()
            print("Order Saved as PAID.")
            
            # Kurangi Stok
            for item in order.items.all():
                item.variant.stock = F('stock') - item.quantity
                item.variant.save()
                
                # Refresh DB dan kirim notifikasi low stock jika perlu
                item.variant.refresh_from_db()
                from dashboard.utils.email_service import send_low_stock_email
                send_low_stock_email(item.variant)
```
