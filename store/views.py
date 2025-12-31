from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .cart import Cart
from .forms import *
from .midtrans_service import create_snap_transaction
from .services.email_service import *
from .services.notification_service import send_payment_notification_to_admin # DIPERBARUI
import json
import hashlib
from django.db import transaction
from django.db.models import F
from django.contrib.admin.views.decorators import staff_member_required





@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/auth/order_detail.html', {'order': order})

def about_us_view(request):
    content = AboutPageContent.objects.first()
    return render(request, 'store/about_us.html', {'content': content})

def landing_page_view(request):
    featured_products = Product.objects.filter(available=True).order_by('-created')[:4]
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

def product_list(request):
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    # Ambil parameter dari URL (QUERYSTRING)
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "")
    category_slug = request.GET.get("category")

    category = None

    # ===== CATEGORY FILTER (PAKAI SLUG ADMIN) =====
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # ===== SEARCH =====
    if search:
        products = products.filter(name__icontains=search)

    # ===== SORT =====
    if sort == "price_asc":
        products = products.order_by("price")
    elif sort == "price_desc":
        products = products.order_by("-price")
    elif sort == "newest":
        products = products.order_by("-created")
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
        if variant.color not in variants_data: variants_data[variant.color] = []
        variants_data[variant.color].append({'id': variant.id, 'size': variant.size, 'stock': variant.stock})
    cart_product_form = CartAddProductForm()
    return render(request, 'store/product_detail.html', {'product': product, 'variants_data_json': json.dumps(variants_data), 'cart_product_form': cart_product_form})

@login_required(login_url='store:login')
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        variant = get_object_or_404(ProductVariant, id=cd['variant_id'])

        if cd['quantity'] > variant.stock:
            messages.error(request, f"Maaf, stok untuk ukuran {variant.size} hanya tersisa {variant.stock}.")
            return redirect('store:product_detail', id=product.id, slug=product.slug)

        cart.add(product=product, variant=variant, quantity=cd['quantity'], override_quantity=cd['override'])
        messages.success(request, "Produk berhasil ditambahkan ke keranjang!")

    return redirect('store:cart_detail')

def cart_remove(request, product_id, variant_id):
    cart = Cart(request); product = get_object_or_404(Product, id=product_id); variant = get_object_or_404(ProductVariant, id=variant_id)
    cart.remove(variant); messages.info(request, "Produk telah dihapus dari keranjang.")
    return redirect('store:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'override': True, 'variant_id': item['variant'].id})
    return render(request, 'store/cart.html', {'cart': cart})

def register(request):
    if request.user.is_authenticated: return redirect('store:landing_page')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(); login(request, user); return redirect('store:landing_page')
    else: form = UserRegisterForm()
    return render(request, 'store/auth/register.html', {'form': form})

def custom_logout_view(request):
    logout(request)
    messages.success(request, "Anda telah berhasil logout.")
    return redirect('store:landing_page')

@login_required
def account_dashboard(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/auth/account_dashboard.html', {'orders': orders})

@login_required
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user)
    form = AddressForm()
    return render(request, 'store/auth/address_list.html', {'addresses': addresses, 'form': form})

@login_required
def address_add_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Alamat baru berhasil ditambahkan.")
    return redirect('store:address_list')

@login_required
def address_delete_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.info(request, "Alamat berhasil dihapus.")
    return redirect('store:address_list')

@login_required
def address_set_default_view(request, address_id):
    Address.objects.filter(user=request.user).update(is_default=False)
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, "Alamat utama berhasil diubah.")
    return redirect('store:address_list')

@login_required
def account_details_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save(); p_form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui.')
            return redirect('store:account_details')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    context = {'u_form': u_form, 'p_form': p_form}
    return render(request, 'store/auth/account_details.html', context)

@login_required
def address_add_from_checkout_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Alamat baru berhasil ditambahkan.")
    return redirect('store:order_create')


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            
            # Logika kupon dihapus
            order.shipping_cost = 15000 # Contoh biaya pengiriman
            order.save()
            
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], variant=item['variant'], price=item['price'], quantity=item['quantity'])
            
            snap_token = create_snap_transaction(order)
            if snap_token:
                order.midtrans_snap_token = snap_token
                order.save()
                cart.clear()
                return render(request, 'store/payment.html', {
                    'snap_token': snap_token,
                    'client_key': settings.MIDTRANS_CLIENT_KEY
                })
            else:
                messages.error(request, "Gagal membuat transaksi pembayaran. Silakan coba lagi.")
                return redirect('store:order_create')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            default_address = Address.objects.filter(user=request.user, is_default=True).first()
            if default_address:
                initial_data = {
                    'first_name': default_address.full_name.split(' ')[0],
                    'last_name': ' '.join(default_address.full_name.split(' ')[1:]),
                    'email': request.user.email,
                    'address': default_address.address_line,
                    'city': default_address.city,
                    'postal_code': default_address.postal_code,
                }
            else:
                initial_data = {'email': request.user.email, 'first_name': request.user.first_name, 'last_name': request.user.last_name}
        form = OrderCreateForm(initial=initial_data)
        
    saved_addresses = Address.objects.filter(user=request.user) if request.user.is_authenticated else None
    address_form = AddressForm()
    return render(request, 'store/checkout.html', {'cart': cart, 'form': form, 'saved_addresses': saved_addresses, 'address_form': address_form})


@login_required
def retry_payment_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'paid':
        messages.info(request, "Pesanan ini sudah dibayar.")
        return redirect('store:account_dashboard')
    
    snap_token = create_snap_transaction(order)
    if snap_token:
        order.midtrans_snap_token = snap_token
        order.save()
        return render(request, 'store/payment.html', {
            'snap_token': snap_token,
            'client_key': settings.MIDTRANS_CLIENT_KEY
        })
    else:
        messages.error(request, "Gagal membuat transaksi pembayaran. Silakan coba lagi.")
        return redirect('store:account_dashboard')

@csrf_exempt
def midtrans_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        midtrans_order_id = data.get('order_id')
        transaction_status = data.get('transaction_status')
        fraud_status = data.get('fraud_status')
        signature_key = data.get('signature_key')
        
        server_key = settings.MIDTRANS_SERVER_KEY
        input_string = midtrans_order_id + data.get('status_code') + data.get('gross_amount') + server_key
        hashed_input = hashlib.sha512(input_string.encode()).hexdigest()

        if hashed_input != signature_key:
            return HttpResponse(status=403)

        if midtrans_order_id.startswith('payment_notif_test'):
            return HttpResponse(status=200)

        try:
            original_order_id = int(midtrans_order_id.split('-')[0])
            order = Order.objects.get(id=original_order_id)

            if order.status == 'paid':
                return HttpResponse(status=200)

            if transaction_status == 'settlement' and fraud_status == 'accept':
                with transaction.atomic():
                    order.status = 'paid'
                    order.save()
                    
                    for item in order.items.all():
                        item.variant.stock -= item.quantity
                        item.variant.save()
                
                # Kirim email notifikasi ke admin menggunakan Django Mail
                try:
                    admin_users = User.objects.filter(is_staff=True)
                    admin_emails = [user.email for user in admin_users if user.email]
                    if not admin_emails:
                        admin_emails = [settings.DEFAULT_ADMIN_EMAIL]
                    
                    subject_admin = f"Pembayaran Berhasil untuk Pesanan #{order.id}"
                    html_message_admin = render_to_string('emails/admin_payment_notification.html', {'order': order})
                    plain_message_admin = strip_tags(html_message_admin)
                    send_mail(
                        subject_admin, plain_message_admin, settings.EMAIL_HOST_USER, 
                        admin_emails, html_message=html_message_admin
                    )
                except Exception as e:
                    print(f"Gagal mengirim email notifikasi ke admin: {e}")

                # Kirim invoice ke pelanggan
                try:
                    subject_customer = f"Invoice untuk Pesanan Anda #{order.id}"
                    html_message_customer = render_to_string('emails/customer_invoice.html', {'order': order})
                    plain_message_customer = strip_tags(html_message_customer)
                    send_mail(subject_customer, plain_message_customer, settings.EMAIL_HOST_USER, [order.email], html_message=html_message_customer)
                except Exception as e:
                    print(f"Gagal mengirim invoice ke pelanggan: {e}")

            elif transaction_status in ['cancel', 'deny', 'expire']:
                order.status = 'failed'
                order.save()
            
            return HttpResponse(status=200)
        
        except (Order.DoesNotExist, ValueError, IndexError) as e:
            return HttpResponse(status=404)
            
    return HttpResponse(status=400)




def order_confirmation(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id) if order_id else None
    if 'order_id' in request.session: del request.session['order_id']
    return render(request, 'store/order_confirmation.html', {'order': order})


@staff_member_required
def offline_sale_view(request):
    """
    Page admin untuk mencatat penjualan OFFLINE
    dan mengurangi stok dengan aman
    """

    if request.method == "POST":
        variant_id = request.POST.get("variant_id")
        quantity = int(request.POST.get("quantity", 0))
        price = int(request.POST.get("price", 0))
        channel = request.POST.get("channel", "offline")
        note = request.POST.get("note", "")

        if quantity <= 0:
            messages.error(request, "Jumlah harus lebih dari 0")
            return redirect("store:admin_offline_sale")

        try:
            with transaction.atomic():
                variant = (
                    ProductVariant.objects
                    .select_for_update()
                    .get(id=variant_id)
                )

                if variant.stock < quantity:
                    messages.error(
                        request,
                        f"Stok tidak cukup. Sisa: {variant.stock}"
                    )
                    return redirect("store:admin_offline_sale")

                # Kurangi stok (AMAN)
                variant.stock = F("stock") - quantity
                variant.save()
                variant.refresh_from_db()

                # Catat penjualan offline
                OfflineSale.objects.create(
                    variant=variant,
                    quantity=quantity,
                    price=price or variant.product.price,
                    channel=channel,
                    staff=request.user,
                    note=note,
                )

            messages.success(
                request,
                f"Penjualan berhasil. Sisa stok: {variant.stock}"
            )
            return redirect("store:admin_offline_sale")

        except ProductVariant.DoesNotExist:
            messages.error(request, "Varian tidak ditemukan")
            return redirect("store:admin_offline_sale")

    # GET
    variants = ProductVariant.objects.select_related(
        "product"
    ).order_by("product__name", "color", "size")

    recent_sales = OfflineSale.objects.select_related(
        "variant", "staff"
    ).order_by("-created_at")[:10]

    return render(
        request,
        "admin/offline_sale.html",
        {
            "variants": variants,
            "recent_sales": recent_sales,
        }
    )