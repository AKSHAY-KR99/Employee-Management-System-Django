from django.contrib import admin
from .models import User, DynamicField, DynamicForm, Employee, EmployeeFieldValue

admin.site.register(User)
admin.site.register(DynamicField)
admin.site.register(DynamicForm)
admin.site.register(Employee)
admin.site.register(EmployeeFieldValue)