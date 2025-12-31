from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

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