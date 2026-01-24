from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import F
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail

import json
import hashlib

# Import Models & Forms
from .models import * 
from .cart import Cart
from .forms import * # Import Services
from .midtrans_service import create_snap_transaction
from .services.email_service import * 
from .services.notification_service import send_payment_notification_to_admin

# ==============================================================================
# 1. CORE & LANDING PAGE
# ==============================================================================

def landing_page_view(request):
    # Optimasi: prefetch_related agar gambar varian tidak query berulang
    featured_products = Product.objects.filter(available=True).select_related('category').prefetch_related('variants', 'images').order_by('-created')[:4]
    content = LandingPageContent.objects.first()
    
    all_featured_collections = list(FeaturedCollection.objects.all()[:3])
    main_collection = all_featured_collections[0] if all_featured_collections else None
    side_collections = all_featured_collections[1:] if len(all_featured_collections) > 1 else None
    
    lookbook_images = LookbookImage.objects.all()[:5]
    
    context = {
        'featured_products': featured_products,
        'content': content,
        'main_collection': main_collection,
        'side_collections': side_collections,
        'lookbook_images': lookbook_images
    }
    return render(request, 'store/landing_page.html', context)

def about_us_view(request):
    content = AboutPageContent.objects.first()
    return render(request, 'store/about_us.html', {'content': content})


# ==============================================================================
# 2. PRODUK & KATALOG
# ==============================================================================

def product_list(request, category_slug=None): 
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).select_related('category').prefetch_related('variants', 'images')

    # Ambil parameter search & sort dari URL Query (?search=...)
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "")
    
    # Ambil category dari query string jika tidak ada di URL path
    if not category_slug:
        category_slug = request.GET.get("category")

    category = None

    # Filter Category
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Filter Search
    if search:
        products = products.filter(name__icontains=search)

    # Sorting Logic
    if sort == "price_asc":
        products = products.order_by("price")
    elif sort == "price_desc":
        products = products.order_by("-price")
    elif sort == "oldest":
        products = products.order_by("created")
    else:
        products = products.order_by("-created")

    context = {
        "categories": categories,
        "products": products,
        "category": category,
        "search": search,
        "sort": sort,
    }
    return render(request, "store/product_listing.html", context)

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    variants = product.variants.order_by('color', 'size')
    
    variants_data = {}
    for variant in variants:
        if variant.color not in variants_data:
            variants_data[variant.color] = []
        
        # Data untuk JavaScript di frontend
        variants_data[variant.color].append({
            'id': variant.id, 
            'size': variant.size, 
            'stock': variant.stock,
            'price': float(product.price) 
        })
    
    cart_product_form = CartAddProductForm()
    
    context = {
        'product': product, 
        'variants_data_json': json.dumps(variants_data), 
        'cart_product_form': cart_product_form
    }
    return render(request, 'store/product_detail.html', context)

def size_guide_view(request):
    """
    Mengembalikan potongan HTML Size Guide untuk modal pop-up
    """
    return render(request, 'store/partials/size_guide.html')

# ==============================================================================
# 3. HTMX UTILS (UNTUK FITUR INTERAKTIF TANPA RELOAD)
# ==============================================================================

def check_stock(request, product_id):
    variant_id = request.GET.get('variant')
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        stock = variant.stock
        price = variant.price
    else:
        product = get_object_or_404(Product, id=product_id)
        stock = 0
        price = product.price

    return render(request, 'store/partials/product_price_stock.html', {
        'price': price,
        'stock': stock
    })

def update_cart_badge(request):
    cart = Cart(request)
    return render(request, 'store/partials/cart_badge.html', {'cart_len': len(cart)})


# ==============================================================================
# 4. KERANJANG (CART)
# ==============================================================================

def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={
            'quantity': item['quantity'], 
            'override': True, 
            'variant_id': item['variant'].id
        })
    return render(request, 'store/cart.html', {'cart': cart})

@login_required(login_url='store:login')
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))
        
        if variant_id:
            variant_obj = get_object_or_404(ProductVariant, id=variant_id)
            cart.add(product=product, quantity=quantity, variant=variant_obj)
            messages.success(request, f"{product.name} ({variant_obj.size}) berhasil masuk keranjang!")
        else:
            cart.add(product=product, quantity=quantity)
            messages.success(request, f"{product.name} berhasil masuk keranjang!")

        return redirect('store:product_detail', id=product.id, slug=product.slug)
        
    return redirect('store:product_list')

def cart_remove(request, product_id, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    cart.remove(variant)
    
    if request.htmx:
        return render(request, 'store/partials/cart_table.html', {'cart': cart})
        
    messages.info(request, "Item dihapus.")
    return redirect('store:cart_detail')


# ==============================================================================
# 5. CHECKOUT & ORDER
# ==============================================================================

def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            
            # --- SHIPPING LOGIC ---
            city_lower = order.city.lower().strip()
            promo_cities = ['pontianak', 'singkawang', 'semarang']
            
            shipping_option = request.POST.get('shipping_option', 'standard')
            order.shipping_option = shipping_option
            
            if any(pc in city_lower for pc in promo_cities):
                # Gratis Ongkir untuk kota promo
                order.shipping_cost = 0
                order.shipping_option = "Gratis Ongkir (Promo)"
            elif shipping_option == 'self':
                # Bayar Ongkir di Tempat (COD Ongkir)
                order.shipping_cost = 0
                order.shipping_option = "Bayar Ongkir di Tujuan"
            else:
                # Standard Flat Rate
                order.shipping_cost = 15000
                order.shipping_option = "Jasa Kirim Toko"

            # Ambil diskon dari session (jika ada kupon)
            discount_percent = request.session.get('discount_percent', 0)
            order.discount = discount_percent
            
            order.save()
            
            # Clear coupon session setelah order dibuat
            request.session.pop('coupon_id', None)
            request.session.pop('coupon_code', None)
            request.session.pop('discount_percent', None)
            
            for item in cart:
                OrderItem.objects.create(
                    order=order, 
                    product=item['product'], 
                    variant=item['variant'], 
                    price=item['price'], 
                    quantity=item['quantity']
                )
            
            # Generate Midtrans Token
            snap_token, midtrans_order_id = create_snap_transaction(order)
            if snap_token:
                order.midtrans_snap_token = snap_token
                order.midtrans_order_id = midtrans_order_id
                order.save()
                cart.clear()
                request.session['order_id'] = order.id  # Store for confirmation page
                return render(request, 'store/payment.html', {

                    'order': order,
                    'snap_token': snap_token,
                    'client_key': settings.MIDTRANS_CLIENT_KEY
                })
            else:
                messages.error(request, "Gagal koneksi ke Payment Gateway.")
                return redirect('store:order_create')
    else:
        # Pre-fill form
        initial_data = {}
        if request.user.is_authenticated:
            default_addr = Address.objects.filter(user=request.user, is_default=True).first()
            if default_addr:
                initial_data = {
                    'first_name': default_addr.full_name, # Use full name
                    'email': request.user.email,
                    'address': default_addr.address_line,
                    'city': default_addr.city,
                }
            else:
                initial_data = {
                    'email': request.user.email, 
                    'first_name': request.user.get_full_name() or request.user.username, 
                }
        form = OrderCreateForm(initial=initial_data)
        
    saved_addresses = Address.objects.filter(user=request.user) if request.user.is_authenticated else None
    address_form = AddressForm()
    
    return render(request, 'store/checkout.html', {
        'cart': cart, 
        'form': form, 
        'saved_addresses': saved_addresses, 
        'address_form': address_form
    })

def apply_coupon(request):
    """AJAX endpoint untuk validasi dan apply kupon"""
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        cart = Cart(request)
        subtotal = cart.get_total_price()
        
        if not code:
            return JsonResponse({'success': False, 'message': 'Masukkan kode kupon'})
        
        try:
            from django.utils import timezone
            now = timezone.now()
            coupon = Coupon.objects.get(
                code__iexact=code,
                active=True,
                valid_from__lte=now,
                valid_to__gte=now
            )
            
            # Hitung diskon
            discount_percent = coupon.discount
            discount_amount = int(subtotal * discount_percent / 100)
            new_total = subtotal - discount_amount + 15000  # + shipping
            
            # Simpan kupon di session
            request.session['coupon_id'] = coupon.id
            request.session['coupon_code'] = coupon.code
            request.session['discount_percent'] = discount_percent
            
            return JsonResponse({
                'success': True,
                'message': f'Kupon {coupon.code} berhasil diterapkan!',
                'discount_percent': discount_percent,
                'discount_amount': discount_amount,
                'new_total': new_total
            })
            
        except Coupon.DoesNotExist:
            # Hapus kupon dari session jika tidak valid
            request.session.pop('coupon_id', None)
            request.session.pop('coupon_code', None)
            request.session.pop('discount_percent', None)
            return JsonResponse({'success': False, 'message': 'Kode kupon tidak valid atau sudah kadaluarsa'})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


def order_confirmation(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id) if order_id else None
    if 'order_id' in request.session: 
        del request.session['order_id']
    return render(request, 'store/order_confirmation.html', {'order': order})


# ==============================================================================
# 6. PEMBAYARAN (MIDTRANS)
# ==============================================================================

@login_required
def retry_payment_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'paid':
        messages.info(request, "Pesanan ini sudah dibayar.")
        return redirect('store:account_dashboard')
    
    # Cek apakah token sudah ada dan valid (kecuali dipaksa renew)
    renew = request.GET.get('renew') == 'true'
    
    if order.midtrans_snap_token and not renew:
        snap_token = order.midtrans_snap_token
    else:
        snap_token, midtrans_order_id = create_snap_transaction(order)
        if snap_token:
            order.midtrans_snap_token = snap_token
            order.midtrans_order_id = midtrans_order_id
            order.save()
            
    if snap_token:
        request.session['order_id'] = order.id
        return render(request, 'store/payment.html', {
            'order': order,
            'snap_token': snap_token,
            'client_key': settings.MIDTRANS_CLIENT_KEY
        })
    
    messages.error(request, "Gagal memproses pembayaran ulang.")
    return redirect('store:account_dashboard')

@csrf_exempt
def midtrans_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            midtrans_order_id = data.get('order_id')
            transaction_status = data.get('transaction_status')
            fraud_status = data.get('fraud_status')
            signature_key = data.get('signature_key')
            status_code = data.get('status_code')
            gross_amount = data.get('gross_amount')
            
            # 1. Validasi Signature
            server_key = settings.MIDTRANS_SERVER_KEY
            input_string = f"{midtrans_order_id}{status_code}{gross_amount}{server_key}"
            hashed_input = hashlib.sha512(input_string.encode()).hexdigest()

            if hashed_input != signature_key:
                return HttpResponse("Invalid Signature", status=403)

            if midtrans_order_id.startswith('payment_notif_test'):
                return HttpResponse(status=200)

            # 2. Update Order
            original_order_id = int(midtrans_order_id.split('-')[0])
            order = Order.objects.get(id=original_order_id)

            if order.status == 'paid':
                return HttpResponse("Order already paid", status=200)

            # Logic Status Midtrans
            is_paid = False
            if transaction_status == 'capture':
                if fraud_status == 'challenge':
                    return HttpResponse("Challenged", status=200)
                elif fraud_status == 'accept':
                    is_paid = True
            elif transaction_status == 'settlement':
                is_paid = True
            elif transaction_status in ['cancel', 'deny', 'expire']:
                order.status = 'failed'
                order.save()
                return HttpResponse("Order cancelled", status=200)

            if is_paid:
                with transaction.atomic():
                    order.status = 'paid'
                    order.save()
                    
                    # Kurangi Stok
                    for item in order.items.all():
                        item.variant.stock = F('stock') - item.quantity
                        item.variant.save()
                        
                        # Refresh DB untuk memicu alert jika stock < 5
                        item.variant.refresh_from_db()
                        from dashboard.utils.email_service import send_low_stock_email
                        send_low_stock_email(item.variant)
                
                # Kirim Email
                _send_success_emails(order)
                return HttpResponse("Order paid", status=200)

            return HttpResponse("OK", status=200)
        
        except Order.DoesNotExist:
            return HttpResponse("Order Not Found", status=404)
        except Exception as e:
            print(f"Webhook Error: {e}")
            return HttpResponse("Error", status=400)
            
    return HttpResponse(status=400)


@staff_member_required
def sync_order_status(request, order_id):
    """
    Admin endpoint untuk sync status order dari Midtrans API secara manual.
    Berguna jika webhook gagal atau tidak terproses.
    """
    import requests
    import base64
    
    order = get_object_or_404(Order, id=order_id)
    
    if order.status == 'paid':
        messages.info(request, f"Order #{order_id} sudah berstatus PAID.")
        return redirect('dashboard:order_detail', order_id=order.id)
    
    # Check if we have midtrans_order_id
    if not order.midtrans_order_id:
        messages.warning(
            request, 
            f"Order #{order_id} tidak memiliki Midtrans Order ID. "
            f"Silakan update status manual di halaman detail order."
        )
        return redirect('dashboard:order_detail', order_id=order.id)
    
    server_key = settings.MIDTRANS_SERVER_KEY
    
    try:
        # Encode server key for Basic Auth
        auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
        
        # Midtrans API endpoint (sandbox or production)
        base_url = "https://api.midtrans.com" if settings.MIDTRANS_IS_PRODUCTION else "https://api.sandbox.midtrans.com"
        
        # Call Midtrans Status API
        url = f"{base_url}/v2/{order.midtrans_order_id}/status"
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        transaction_status = data.get('transaction_status')
        fraud_status = data.get('fraud_status', 'accept')
        
        # Update status based on Midtrans response
        if transaction_status in ['capture', 'settlement']:
            if transaction_status == 'capture' and fraud_status == 'challenge':
                messages.warning(request, f"Order #{order_id} challenged by fraud detection.")
            else:
                # Mark as paid
                with transaction.atomic():
                    order.status = 'paid'
                    order.save()
                    
                    # Kurangi stok
                    for item in order.items.all():
                        item.variant.stock = F('stock') - item.quantity
                        item.variant.save()
                
                messages.success(request, f"✅ Order #{order_id} berhasil di-sync! Status: PAID")
                
        elif transaction_status in ['pending']:
            messages.info(request, f"Order #{order_id} masih PENDING di Midtrans.")
            
        elif transaction_status in ['cancel', 'deny', 'expire']:
            order.status = 'failed'
            order.save()
            messages.warning(request, f"Order #{order_id} status: {transaction_status.upper()}")
            
        else:
            messages.info(request, f"Order #{order_id} status dari Midtrans: {transaction_status}")
        
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Gagal koneksi ke Midtrans API: {e}")
    except Exception as e:
        messages.error(request, f"Error sync: {e}")
    
    return redirect('dashboard:order_detail', order_id=order.id)


def _send_success_emails(order):
    try:
        send_payment_notification_to_admin(order)
    except Exception as e:
        print(f"Gagal kirim email admin: {e}")

    try:
        subject = f"Invoice Pesanan #{order.id}"
        html_msg = render_to_string('emails/customer_invoice.html', {'order': order})
        plain_msg = strip_tags(html_msg)
        send_mail(subject, plain_msg, settings.EMAIL_HOST_USER, [order.email], html_message=html_msg)
    except Exception as e:
        print(f"Gagal kirim invoice customer: {e}")


# ==============================================================================
# 7. AUTH & AKUN PENGGUNA (PERBAIKAN PATH TEMPLATE DI SINI)
# ==============================================================================

def register(request):
    if request.user.is_authenticated:
        return redirect('store:landing_page')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Selamat datang!")
            return redirect('store:landing_page')
    else:
        form = UserRegisterForm()
    # Mengarah ke folder auth
    return render(request, 'store/auth/register.html', {'form': form})

def custom_logout_view(request):
    logout(request)
    messages.success(request, "Anda telah logout.")
    return redirect('store:landing_page')

@login_required
def account_dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    context = {
        'orders': orders
    }
    # PERBAIKAN: Mengarah ke store/auth/account_dashboard.html
    return render(request, 'store/auth/account_dashboard.html', context)

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # Mengarah ke folder auth
    return render(request, 'store/auth/order_detail.html', {'order': order})

@login_required
def account_details_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profil diperbarui.')
            return redirect('store:account_details')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    # Mengarah ke folder auth
    return render(request, 'store/auth/account_details.html', {
        'u_form': u_form, 
        'p_form': p_form
    })


# ==============================================================================
# 8. MANAJEMEN ALAMAT (CRUD)
# ==============================================================================

@login_required
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user)
    form = AddressForm()
    # Mengarah ke folder auth
    return render(request, 'store/auth/address_list.html', {'addresses': addresses, 'form': form})

@login_required
def address_add_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Alamat ditambahkan.")
    return redirect('store:address_list')

@login_required
def address_delete_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.info(request, "Alamat dihapus.")
    return redirect('store:address_list')

@login_required
def address_set_default_view(request, address_id):
    Address.objects.filter(user=request.user).update(is_default=False)
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, "Alamat utama diubah.")
    return redirect('store:address_list')

@login_required
def address_add_from_checkout_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Alamat berhasil ditambahkan.")
    return redirect('store:order_create')


# ==============================================================================
# 9. ADMIN OFFLINE SALE
# ==============================================================================

@staff_member_required
def offline_sale_view(request):
    if request.method == "POST":
        variant_id = request.POST.get("variant_id")
        quantity = int(request.POST.get("quantity", 0))
        price = int(request.POST.get("price", 0))
        channel = request.POST.get("channel", "offline")
        note = request.POST.get("note", "")

        if quantity <= 0:
            messages.error(request, "Jumlah harus lebih dari 0")
            return redirect("store:offline_sale")

        try:
            with transaction.atomic():
                variant = ProductVariant.objects.select_for_update().get(id=variant_id)

                if variant.stock < quantity:
                    messages.error(request, f"Stok tidak cukup. Sisa: {variant.stock}")
                    return redirect("store:offline_sale")

                variant.stock = F("stock") - quantity
                variant.save()
                variant.refresh_from_db()

                OfflineSale.objects.create(
                    variant=variant,
                    quantity=quantity,
                    price=price or variant.product.price,
                    channel=channel,
                    staff=request.user,
                    note=note,
                )

            messages.success(request, f"Penjualan berhasil. Sisa stok: {variant.stock}")
            return redirect("store:offline_sale")

        except ProductVariant.DoesNotExist:
            messages.error(request, "Varian tidak ditemukan")
            return redirect("store:offline_sale")

    variants = ProductVariant.objects.select_related("product").order_by("product__name", "color", "size")
    recent_sales = OfflineSale.objects.select_related("variant", "staff").order_by("-created_at")[:10]

    return render(request, "store/admin/offline_sale.html", {
        "variants": variants,
        "recent_sales": recent_sales,
    })