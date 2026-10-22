from django.urls import path
from . import views

urlpatterns = [
    path('api/auth/login/', views.api_login),
    path('api/vuln/products/', views.vuln_products),
    path('api/vuln/products/create/', views.vuln_product_create),
    path('api/vuln/products/<str:product_id>/', views.vuln_product_detail),
    path('api/vuln/profile/', views.vuln_profile),
    path('api/vuln/admin/stats/', views.vuln_admin_stats),
    path('api/safe/products/', views.safe_products),
    path('api/products/<int:product_id>/comments/', views.comment_create),
]