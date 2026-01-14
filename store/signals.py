from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, ProductVariant
from .supabase_client import get_supabase_client
import json

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Membuat Profile jika User baru dibuat, atau memastikan profile ada untuk user lama.
    """
    if created:
        Profile.objects.create(user=instance)
    # Pastikan profile selalu tersimpan, dan buat jika tidak ada (untuk user lama seperti superuser)
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=ProductVariant)
def broadcast_stock_update(sender, instance, **kwargs):
    """
    Kirim sinyal realtime ke Supabase saat stok varian berubah
    """
    from django.db import transaction
    
    def send_update():
        supabase = get_supabase_client()
        if supabase:
            try:
                payload = {
                    'id': instance.id,
                    'stock': instance.stock,
                    'product_name': instance.product.name,
                    'variant': f"{instance.color}/{instance.size}"
                }
                # Kirim pesan 'stock_update' ke channel 'stock-updates'
                supabase.channel('stock-updates').send(
                    type='broadcast',
                    event='stock_update',
                    payload=payload
                )
            except Exception as e:
                print(f"Supabase Broadcast Error: {e}")

    # Pastikan dikirim hanya saat transaksi sukses (commit)
    transaction.on_commit(send_update)