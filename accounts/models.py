from django.contrib.auth.models import AbstractUser
from django.db import models

FIELD_TYPES = [
    ("text", "Text"),
    ("textarea", "Textarea"),
    ("number", "Number"),
    ("date", "Date"),
    ("email", "Email"),
    ("password", "Password"),
    ("select", "Select"),
    ("radio", "Radio"),
    ("checkbox", "Checkbox"),
]

class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)

    def __str__(self):
        return self.username
    

class DynamicForm(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
    

class DynamicField(models.Model):
    form = models.ForeignKey(DynamicForm, related_name="fields", on_delete=models.CASCADE)
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES, default="text")
    required = models.BooleanField(default=True)
    options = models.JSONField(blank=True, null=True, help_text="For select/radio/checkbox.")
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    help_text = models.CharField(max_length=255, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.label}"


class Employee(models.Model):
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name="employees")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Employee #{self.id} (Form: {self.form.name})"


class EmployeeFieldValue(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="field_values")
    field = models.ForeignKey(DynamicField, on_delete=models.CASCADE)
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.field.label}: {self.value} - {self.employee.id}"