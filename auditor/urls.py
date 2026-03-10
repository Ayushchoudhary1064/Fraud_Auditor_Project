from django.conf.urls.static import static
from django.urls import path
from . import views
from django.conf import settings
urlpatterns = [
    # Public Launch Page
    path('', views.index, name='index'), # Corrected: Points to views.index

    # User Authentication & Pages
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='signup'),
    path('home/', views.home, name='home'), # Dedicated path for post-login home page
    path('submitclaim/', views.submit_claim, name='submit_claim'),
    path('viewstatus/', views.view_status, name='view_status'),
    path('profile/', views.view_user_profile, name='view_user_profile'),
    path('logout/', views.logout_view, name='logout'),

    # Admin Routes
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/dashboard/', views.admin_home, name='admin_home'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/users/', views.admin_manage_users, name='admin_manage_users'),
    path('admin/model/', views.admin_model_execution, name='admin_model_execution'),
    path('admin/network/', views.admin_covisit_network, name='admin_covisit_network'),
    path('admin/fraudreport/', views.admin_fraud_report, name='admin_fraud_report'),
    path('admin/claims/', views.admin_claim_list, name='admin_claim_list'),
    path('admin/users/delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    # Point the fraud check action to the new consolidated view
    path('admin/claim/<int:claim_id>/assess_status/', views.assess_claim_status, name='assess_claim_status'),
    # You had two separate fraud check URLs previously.
    # The 'assess_claim_status' replaces both.
    # It's recommended to remove these older ones if not used elsewhere:
    # path('admin/claim/<int:claim_id>/fraud_check/', views.check_fraud_for_claim, name='check_fraud_for_claim'),
    # path('admin/claim/<int:claim_id>/check_fraud/', views.check_fraud, name='check_fraud'),
]
