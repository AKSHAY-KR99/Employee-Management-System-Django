from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import register_user, login_user, dashboard_view, logout_user,change_password,\
    profile_view, form_builder, save_form, form_list, form_detail, create_employee_view, get_form_fields, \
    save_employee, employee_list, delete_employee, edit_employee, UserRegisterAPI, UserLoginAPI, UserProfileAPI, \
    ChangePasswordAPI, UserUpdateAPI, DynamicFormDetailAPI, DynamicFormListAPI, DynamicFormCreateAPI, \
        EmployeeCreateAPIView, EmployeeListByFormAPIView, EmployeeUpdateAPIView, EmployeeDeleteAPIView


urlpatterns = [
    path("register/", register_user, name="register"),
    path("login/", login_user, name="login"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("logout/", logout_user, name="logout"),
    path("change-password/", change_password, name="change_password"),
    path("profile/", profile_view, name="profile"),

    path("form/builder/", form_builder, name="form_builder"),
    path("form/save-form/", save_form, name="save_form"),
    path("form/list/", form_list, name="form_list"),
    path("form/detail/<int:form_id>/", form_detail, name="form_detail"),
    
    
    path("employee/create/", create_employee_view, name="create_employee"),
    path("employee/get-form-fields/<int:form_id>/", get_form_fields, name="get_form_fields"),
    path("employee/save/", save_employee, name="save_employee"),
    path("employee/list/", employee_list, name="employee_list"),
    path('employee/delete/<int:employee_id>/', delete_employee, name='delete_employee'),
    path('employee/edit/<int:employee_id>/', edit_employee, name='edit_employee'),
    
    
    path('api/register/', UserRegisterAPI.as_view(), name='api-register'),
    path('api/login/', UserLoginAPI.as_view(), name='api-login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/profile/', UserProfileAPI.as_view(), name='api-profile'),
    path('api/change-password/', ChangePasswordAPI.as_view(), name='change-password'),
    path("api/profile-update/", UserUpdateAPI.as_view(), name="user-profile"),
    path("api/forms/", DynamicFormListAPI.as_view(), name="form-list"),
    path("api/forms/create/", DynamicFormCreateAPI.as_view(), name="form-create"),
    path("api/forms/<int:id>/", DynamicFormDetailAPI.as_view(), name="form-detail"),
    path("api/employees/create/", EmployeeCreateAPIView.as_view(), name="employee-create"),
    path("api/employees/form/<int:form_id>/", EmployeeListByFormAPIView.as_view(), name="employee-list-by-form"),
    path("api/employees/update/<int:id>", EmployeeUpdateAPIView.as_view(), name="employee-update"),
    path("api/employees/delete/<int:employee_id>/", EmployeeDeleteAPIView.as_view(), name="employee-delete")
]