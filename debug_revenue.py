
import os
import django
from django.db.models import Sum, F

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nothing_brain_project.settings')
django.setup()

from store.models import Order, OrderItem

print("--- REVENUE DEBUG ---")
paid_orders = Order.objects.filter(status='paid')
print(f"Total Paid Orders: {paid_orders.count()}")

item_revenue = OrderItem.objects.filter(order__status='paid').aggregate(
    total=Sum(F('price') * F('quantity'))
)['total'] or 0
print(f"Item Revenue (Paid): {item_revenue}")

shipping_revenue = Order.objects.filter(status='paid').aggregate(
    total=Sum('shipping_cost')
)['total'] or 0
print(f"Shipping Revenue (Paid): {shipping_revenue}")

total_calculated = item_revenue + shipping_revenue
print(f"TOTAL REVENUE (Paid): {total_calculated}")

print("\n--- DETAILED PAID ORDERS ---")
for o in paid_orders:
    print(f"Order #{o.id}: Status={o.status}, Total={o.get_total_cost()}")

print("\n--- PENDING ORDERS CHECK ---")
pending_orders = Order.objects.filter(status='pending')
print(f"Total Pending Orders: {pending_orders.count()}")
for o in pending_orders:
    print(f"Order #{o.id}: Status={o.status}, Total={o.get_total_cost()}")

print("--- END DEBUG ---")
