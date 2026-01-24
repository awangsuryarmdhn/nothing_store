from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('pos/', views.pos_view, name='pos'),
    path('pos/checkout/', views.pos_checkout, name='pos_checkout'),
    path('pos/search/', views.pos_search_api, name='pos_search_api'),
    path('products/', views.product_manage, name='product_manage'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/invoice/', views.order_invoice, name='order_invoice'),
    path('orders/<int:order_id>/retry/', views.order_retry_payment, name='order_retry_payment'),
    
    # Category Management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
]

