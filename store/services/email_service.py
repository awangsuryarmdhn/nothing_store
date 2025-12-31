from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_payment_success_email_to_admin(order):
    """
    Mengirim email notifikasi ke semua staf/admin saat pembayaran berhasil.
    """
    admin_users = User.objects.filter(is_staff=True)
    admin_emails = [user.email for user in admin_users if user.email]

    if not admin_emails:
        print("Tidak ada email admin yang ditemukan untuk dikirimi notifikasi.")
        return

    subject = f"Pembayaran Berhasil untuk Pesanan #{order.id}"
    context = {'order': order}
    html_message = render_to_string('emails/admin_payment_notification.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        'no-reply@nothingbrain.com',
        admin_emails,
        html_message=html_message,
        fail_silently=False,
    )
    print(f"Email notifikasi pembayaran untuk pesanan #{order.id} telah dikirim.")