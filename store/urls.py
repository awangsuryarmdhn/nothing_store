from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'store'

urlpatterns = [
    path('akun/pesanan/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('pesanan/bayar/<int:order_id>/', views.retry_payment_view, name='retry_payment'),
    path('webhook/midtrans/', views.midtrans_webhook, name='midtrans_webhook'),
    path('tentang-kami/', views.about_us_view, name='about_us'),
    path('akun/alamat/', views.address_list_view, name='address_list'),
    path('akun/alamat/tambah/', views.address_add_view, name='address_add'),
    path('akun/alamat/hapus/<int:address_id>/', views.address_delete_view, name='address_delete'),
    path('akun/alamat/set-default/<int:address_id>/', views.address_set_default_view, name='address_set_default'),
    path('checkout/alamat/tambah/', views.address_add_from_checkout_view, name='address_add_from_checkout'),
    path('', views.landing_page_view, name='landing_page'),
    path('produk/', views.product_list, name='product_list'),
    path('produk/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('produk/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('daftar/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='store/auth/login.html'), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('akun/', views.account_dashboard, name='account_dashboard'),
    path('akun/detail/', views.account_details_view, name='account_details'),
    path('keranjang/', views.cart_detail, name='cart_detail'),
    path('keranjang/tambah/<int:product_id>/', views.cart_add, name='cart_add'),
    path('keranjang/hapus/<int:product_id>/<int:variant_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.order_create, name='order_create'),
    path('checkout/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('konfirmasi-pesanan/', views.order_confirmation, name='order_confirmation'),
    path('size-guide/', views.size_guide_view, name='size_guide'),
    path(
        "offline-sale/",
        views.offline_sale_view,
        name="offline_sale",
    ),
]