
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nothing_brain_project.settings')
django.setup()

from store.models import Order

print("--- RESETTING ORDERS ---")
count = Order.objects.count()
print(f"Found {count} orders to delete.")

if count > 0:
    Order.objects.all().delete()
    print("All orders have been deleted successfully.")
else:
    print("No orders to delete.")

print("--- DONE ---")
