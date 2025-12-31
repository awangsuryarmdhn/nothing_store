from django.conf import settings
from django.contrib.auth.models import User
from appwrite.client import Client
from appwrite.services.messaging import Messaging
from appwrite.id import ID
from appwrite.exception import AppwriteException

def send_payment_notification_to_admin(order):
    """
    Mengirim notifikasi email ke semua staf/admin melalui Appwrite Messaging.
    """
    client = Client()
    client.set_endpoint('https://cloud.appwrite.io/v1')
    client.set_project(settings.APPWRITE_PROJECT_ID)
    client.set_key(settings.APPWRITE_API_KEY)

    messaging = Messaging(client)
    
    admin_users = User.objects.filter(is_staff=True)
    admin_emails = [user.email for user in admin_users if user.email]

    if not admin_emails:
        print("Tidak ada email admin yang ditemukan untuk dikirimi notifikasi.")
        return

    subject = f"Pembayaran Berhasil untuk Pesanan #{order.id}"
    content = (
        f"<h2>Pembayaran Berhasil Diterima</h2>"
        f"<p>Pembayaran untuk pesanan dengan nomor <strong>#{order.id}</strong> telah berhasil diterima.</p>"
        f"<p><strong>Detail Pelanggan:</strong></p>"
        f"<ul>"
        f"<li>Nama: {order.first_name} {order.last_name}</li>"
        f"<li>Email: {order.email}</li>"
        f"</ul>"
        f"<p><strong>Total Pembayaran:</strong> Rp {order.get_total_cost()}</p>"
        f"<p>Silakan proses pesanan ini.</p>"
    )

    try:
        # DIPERBARUI: Menghapus argumen provider_id yang tidak perlu
        message = messaging.create_email(
            message_id=ID.unique(),
            subject=subject,
            content=content,
            recipients=admin_emails
        )
        print(f"Notifikasi pembayaran untuk pesanan #{order.id} telah dikirim melalui Appwrite.")
        return message
    except AppwriteException as e:
        print(f"Gagal mengirim notifikasi melalui Appwrite: {e.message}")
        return None
