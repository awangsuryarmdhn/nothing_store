# store/services/notification_service.py

# Komen bagian import appwrite karena library sudah dihapus
# from appwrite.client import Client 
# from appwrite.services.database import Database

def send_payment_notification_to_admin(order_id, amount, customer_name):
    """
    Fungsi dummy sementara.
    Nanti bisa diganti pakai Email/WhatsApp gateway lain jika mau.
    """
    print(f"[LOG] Notifikasi: Order baru {order_id} dari {customer_name} sebesar {amount}")
    return True