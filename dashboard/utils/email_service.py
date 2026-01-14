from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_invoice_email(order):
    """
    Sends an invoice email to the customer after a successful order.
    """
    if not order.email:
        return False

    subject = f"Invoice Pesanan #{order.id} - Nothing Brain Store"
    
    # Render HTML content
    html_message = render_to_string('dashboard/emails/invoice_email.html', {'order': order})
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            html_message=html_message,
            fail_silently=True # Don't crash POS if email fails
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_low_stock_email(variant):
    """
    Sends a warning email to staff when stock is low (<= 5).
    """
    if variant.stock > 5:
        return
        
    from django.contrib.auth.models import User
    staff_emails = list(User.objects.filter(is_staff=True).values_list('email', flat=True))
    
    # Filter empty emails
    staff_emails = [e for e in staff_emails if e]
    
    if not staff_emails:
        return

    subject = f"PERINGATAN: Stok Menipis - {variant.product.name}"
    message = f"""
    Stok produk berikut menipis:
    
    Produk: {variant.product.name}
    Varian: {variant.color} / {variant.size}
    Sisa Stok: {variant.stock}
    
    Harap segera lakukan restock.
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            staff_emails,
            fail_silently=True
        )
        print(f"Low stock email sent for {variant.product.name}")
    except Exception as e:
        print(f"Failed to send low stock email: {e}")
