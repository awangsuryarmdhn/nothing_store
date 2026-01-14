from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from store.models import Product, ProductVariant, Order, OrderItem, ProductImage
from .forms import ProductForm, VariantFormSet, ImageFormSet
import json
from datetime import datetime

# Helper: Cek apakah user adalah staff
def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def dashboard_home(request):
    total_orders = Order.objects.count()
    total_products = Product.objects.filter(available=True).count()
    
    # --- ANALYTICS ---\r
    # 1. Sales Chart Data (DAILY for Current Month)
    from django.db.models.functions import TruncDay
    from django.utils import timezone
    import calendar

    now = timezone.now()
    current_year = now.year
    current_month = now.month
    
    # Get number of days in current month
    _, num_days = calendar.monthrange(current_year, current_month)
    
    # Initialize all days to 0
    days_map = {i: 0 for i in range(1, num_days + 1)}
    
    # Query Paid Orders for this month
    orders_this_month = Order.objects.filter(
        status='paid', 
        created__year=current_year,
        created__month=current_month
    ).prefetch_related('items')
    
    for o in orders_this_month:
        # Localize time to get correct day in Jakarta timezone if needed, 
        # but for simplicity o.created.day usually works if TZ is set.
        d = o.created.astimezone(timezone.get_current_timezone()).day
        days_map[d] += float(o.get_total_cost())
        
    sales_labels = [str(i) for i in range(1, num_days + 1)]
    sales_data = [days_map[i] for i in range(1, num_days + 1)]

    # Determine Total Revenue using DB Aggregation (Faster than looping)
    # Filter only PAID orders
    from django.db.models import F
    
    item_revenue = OrderItem.objects.filter(order__status='paid').aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or 0
    
    shipping_revenue = Order.objects.filter(status='paid').aggregate(
        total=Sum('shipping_cost')
    )['total'] or 0
    
    total_revenue = item_revenue + shipping_revenue

    # Latest Orders (Includes POS & Store)
    latest_orders = Order.objects.select_related('user').prefetch_related('items__product', 'items__variant').order_by('-created')[:10]

    context = {
        'total_orders': total_orders,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'latest_orders': latest_orders,
        'sales_labels': json.dumps(sales_labels),
        'sales_data': json.dumps(sales_data),
    }
    return render(request, 'dashboard/home.html', context)

@login_required
@user_passes_test(is_staff)
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        variant_formset = VariantFormSet(request.POST, prefix='variants')
        image_formset = ImageFormSet(request.POST, request.FILES, prefix='images')

        if form.is_valid() and variant_formset.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                product = form.save()
                
                # Save Variants
                variants = variant_formset.save(commit=False)
                for variant in variants:
                    variant.product = product
                    variant.save()
                variant_formset.save_m2m()

                # 1. Handle Existing Formset Images (Edit/Delete)
                images = image_formset.save(commit=False)
                for image in images:
                    image.product = product
                    image.save()
                image_formset.save_m2m()

                # 2. Handle Bulk Upload (New Images)
                for file in request.FILES.getlist('images'):
                    ProductImage.objects.create(product=product, image=file)
                
                return redirect('dashboard:product_manage')
    else:
        form = ProductForm()
        variant_formset = VariantFormSet(prefix='variants')
        image_formset = ImageFormSet(prefix='images')

    return render(request, 'dashboard/form_product.html', {
        'form': form,
        'variant_formset': variant_formset,
        'image_formset': image_formset,
        'title': 'Tambah Produk Baru'
    })

@login_required
@user_passes_test(is_staff)
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        variant_formset = VariantFormSet(request.POST, instance=product, prefix='variants')
        image_formset = ImageFormSet(request.POST, request.FILES, instance=product, prefix='images')

        if form.is_valid() and variant_formset.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                product = form.save() # Save main form
                variant_formset.save()
                image_formset.save()
                
                # Handle Bulk Upload (New Images)
                for file in request.FILES.getlist('images'):
                    ProductImage.objects.create(product=product, image=file)

                return redirect('dashboard:product_manage')
    else:
        form = ProductForm(instance=product)
        variant_formset = VariantFormSet(instance=product, prefix='variants')
        image_formset = ImageFormSet(instance=product, prefix='images')

    return render(request, 'dashboard/form_product.html', {
        'form': form,
        'variant_formset': variant_formset,
        'image_formset': image_formset,
        'title': f'Edit Produk: {product.name}'
    })

@login_required
@user_passes_test(is_staff)
def product_manage(request):
    products = Product.objects.all().select_related('category').prefetch_related('variants', 'images').order_by('-created')
    
    # Get Supabase Config
    from decouple import config
    supabase_url = config('SUPABASE_URL', default='')
    supabase_key = config('SUPABASE_KEY', default='')

    return render(request, 'dashboard/product_list.html', {
        'products': products,
        'supabase_url': supabase_url,
        'supabase_key': supabase_key
    })

@login_required
@user_passes_test(is_staff)
def pos_view(request):
    # Ambil semua produk dan varian untuk POS
    
    # Get Supabase Config
    from decouple import config
    supabase_url = config('SUPABASE_URL', default='')
    supabase_key = config('SUPABASE_KEY', default='')
    
    # Midtrans Config
    from django.conf import settings

    return render(request, 'dashboard/pos.html', {
        'supabase_url': supabase_url,
        'supabase_key': supabase_key,
        'midtrans_client_key': settings.MIDTRANS_CLIENT_KEY,
        'midtrans_is_production': settings.MIDTRANS_IS_PRODUCTION
    })

@login_required
@user_passes_test(is_staff)
def pos_search_api(request):
    """
    API for POS Search (Server-side)
    """
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category', 'all')
    
    products = Product.objects.filter(available=True).select_related('category').prefetch_related('variants', 'images')

    # Filter Category
    if category_slug != 'all':
        products = products.filter(category__slug=category_slug)

    # Filter Query (Name or SKU or Variant SKU)
    from django.db.models import Q
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(variants__id__icontains=query) |
            Q(variants__color__icontains=query) |
            Q(variants__size__icontains=query)
        ).distinct()

    # Limit results for performance
    products = products[:50]
    
    items = []
    for p in products:
        product_images = list(p.images.all())
        main_img_url = product_images[0].image.url if product_images else ''
        
        # We need to return individual variants as "items" for the POS
        for v in p.variants.all():
            items.append({
                'id': v.id,
                'name': f"{p.name} ({v.color}/{v.size})",
                'price': float(v.get_active_price),
                'stock': v.stock,
                'image': main_img_url,
                'sku': f"{p.id}-{v.id}",
                'category': p.category.slug if p.category else 'uncategorized'
            })
            
    # Double check filtering on items list if query was specific to a variant SKU
    if query:
        q_lower = query.lower()
        # Optional: Additional filtering if needed

    return JsonResponse({'items': items})

@login_required
@user_passes_test(is_staff)
def order_list(request):
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        orders = Order.objects.filter(status=status_filter).order_by('-created')
    else:
        orders = Order.objects.all().order_by('-created')
        
    # Handle CSV Export
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="orders_{status_filter}_{datetime.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Date', 'Customer', 'Email', 'Status', 'Total', 'Channel'])

        for order in orders:
            writer.writerow([
                order.id, 
                order.created.strftime("%Y-%m-%d %H:%M"), 
                f"{order.first_name} {order.last_name}",
                order.email,
                order.status,
                order.get_total_cost(),
                order.channel
            ])
        return response
    
    return render(request, 'dashboard/order_list.html', {
        'orders': orders,
        'status_filter': status_filter
    })

@login_required
@user_passes_test(is_staff)
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            return redirect('dashboard:order_detail', order_id=order.id)
            
    return render(request, 'dashboard/order_detail.html', {'order': order})

@login_required
@user_passes_test(is_staff)
@csrf_exempt
def pos_checkout(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_items = data.get('items', [])
            email = data.get('email', '')
            payment_type = data.get('payment_type', 'cash') 

            if not cart_items:
                return JsonResponse({'status': 'error', 'message': 'Keranjang kosong'})

            with transaction.atomic():
                # Create Order
                order = Order.objects.create(
                    channel='pos',
                    cashier=request.user,
                    first_name='Walk-in',
                    last_name='Customer',
                    email=email if email else 'pos@store.local',
                    status='pending', 
                    shipping_cost=0
                )

                # Create OrderItems
                for item in cart_items:
                    variant_id = item['id']
                    qty = item['qty']
                    # Lock for consistency, but only deduct if cash
                    variant = ProductVariant.objects.select_for_update().get(id=variant_id)
                    
                    if variant.stock < qty:
                        # Even if we don't deduct, we must check availability
                        raise Exception(f"Stok {variant.product.name} ({variant.size}) habis. Sisa: {variant.stock}")
                    
                    # DEDUCT STOCK LOGIC:
                    # Only deduct immediately for CASH (Paid).
                    # For Qr (Pending), we expect Webhook to deduct it upon Settlement.
                    if payment_type == 'cash':
                        variant.stock -= qty
                        variant.save()
                        
                        # Check Low Stock
                        from dashboard.utils.email_service import send_low_stock_email
                        send_low_stock_email(variant)

                    OrderItem.objects.create(
                        order=order,
                        product=variant.product,
                        variant=variant,
                        price=variant.get_active_price,
                        quantity=qty
                    )

                # ----------------
                # PAYMENT LOGIC
                # ----------------
                
                if payment_type == 'qr':
                    # 2. Get Snap Token
                    from store.midtrans_service import create_snap_transaction
                    snap_token = create_snap_transaction(order)
                    
                    if not snap_token:
                        # Log the detailed error from service if possible, or assume config error
                        raise Exception("Gagal membuat transaksi Midtrans. Cek Payment Gateway.")
                        
                    return JsonResponse({'status': 'success', 'order_id': order.id, 'snap_token': snap_token, 'payment_type': 'qr'})

                else:
                    # CASH PAYMENT
                    order.status = 'paid'
                    order.save()

                    # --- EMAIL NOTIFICATION (Only for Paid/Cash) ---
                    from dashboard.utils.email_service import send_invoice_email
                    if email:
                        try:
                            # Send email (skip if fails)
                            send_invoice_email(order)
                        except Exception as e:
                            print(f"Email Error (Ignored): {e}")

            return JsonResponse({'status': 'success', 'order_id': order.id, 'payment_type': 'cash'})

        except ProductVariant.DoesNotExist:
             return JsonResponse({'status': 'error', 'message': 'Produk tidak ditemukan.'}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid Method'}, status=405)

@login_required
@user_passes_test(is_staff)
def order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'dashboard/invoice_print.html', {'order': order})

@login_required
@user_passes_test(is_staff)
def order_retry_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.status == 'paid':
        return redirect('dashboard:order_detail', order_id=order.id)
        
    # Generate new token if needed
    from store.midtrans_service import create_snap_transaction
    from django.conf import settings
    
    snap_token = create_snap_transaction(order)
    if snap_token:
        order.midtrans_snap_token = snap_token
        order.save()
        
    return render(request, 'dashboard/payment_retry.html', {
        'order': order,
        'snap_token': snap_token,
        'client_key': settings.MIDTRANS_CLIENT_KEY,
        'midtrans_is_production': settings.MIDTRANS_IS_PRODUCTION
    })
