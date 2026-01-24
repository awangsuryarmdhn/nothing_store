import midtransclient
from django.conf import settings
import uuid

def create_snap_transaction(order):
    """
    Create Midtrans Snap transaction and return (token, midtrans_order_id).
    Returns (None, None) if failed.
    """
    # Inisialisasi klien Snap Midtrans
    snap = midtransclient.Snap(
        is_production=settings.MIDTRANS_IS_PRODUCTION,
        server_key=settings.MIDTRANS_SERVER_KEY,
        client_key=settings.MIDTRANS_CLIENT_KEY
    )

    # Siapkan item_details terlebih dahulu
    item_details = []
    for item in order.items.all():
        item_details.append({
            'id': f"VAR-{item.variant.id}", # Menambahkan prefix untuk menghindari ID yang sama
            'price': int(item.price),
            'quantity': item.quantity,
            'name': f"{item.product.name} ({item.variant.color} - {item.variant.size})"
        })

    # Tambahkan biaya pengiriman sebagai item terpisah
    if order.shipping_cost > 0:
        item_details.append({
            'id': 'SHIPPING_COST',
            'price': int(order.shipping_cost),
            'quantity': 1,
            'name': 'Biaya Pengiriman'
        })

    # Generate Midtrans Order ID (simpan untuk lookup status nanti)
    midtrans_order_id = f"{order.id}-{uuid.uuid4().hex[:6]}"
    
    # Siapkan parameter transaksi
    transaction_details = {
        'order_id': midtrans_order_id,
        'gross_amount': int(order.get_total_cost())
    }
    
    customer_details = {
        'first_name': order.first_name,
        'last_name': order.last_name,
        'email': order.email,
    }

    params = {
        'transaction_details': transaction_details,
        'item_details': item_details,
        'customer_details': customer_details
    }

    try:
        transaction = snap.create_transaction(params)
        # Return both token and order_id
        return transaction['token'], midtrans_order_id
    except Exception as e:
        print(f"Error Midtrans: {e}")
        return None, None