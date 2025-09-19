from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import DynamicField, DynamicForm, Employee, EmployeeFieldValue

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, error_messages={
        'required': 'Email is required.',
        'invalid': 'Enter a valid email address.'
    })
    password = serializers.CharField(write_only=True, required=True, error_messages={
        'required': 'Password is required.'
    })

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone', 'profile_picture']

    def validate(self, data):
        if not data.get('email'):
            raise serializers.ValidationError({"email": "Email is required."})
        if not data.get('password'):
            raise serializers.ValidationError({"password": "Password is required."})
        return data

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'profile_picture']

        
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New password and confirm password do not match"})
        return attrs

    

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "phone", "profile_picture"]

    def validate_username(self, value):
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class DynamicFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicField
        fields = [
            "id",
            "label",
            "field_type",
            "required",
            "options",
            "placeholder",
            "help_text",
            "order",
        ]

    def validate(self, attrs):
        ftype = attrs.get("field_type")
        options = attrs.get("options")

        if ftype in ["select", "radio", "checkbox"]:
            if not options or not isinstance(options, list):
                raise serializers.ValidationError(
                    {"options": "Options must be a non-empty list for select/radio/checkbox fields."}
                )
        return attrs


class DynamicFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicField
        fields = ["id", "label", "field_type", "required", "options", "placeholder", "help_text", "order"]


class DynamicFormSerializer(serializers.ModelSerializer):
    fields = DynamicFieldSerializer(many=True)

    class Meta:
        model = DynamicForm
        fields = ["id", "name", "description", "created_at", "updated_at", "fields"]

    def create(self, validated_data):
        fields_data = validated_data.pop("fields")
        form = DynamicForm.objects.create(**validated_data)

        for idx, field in enumerate(fields_data, start=1):
            order = field.pop("order", idx)
            DynamicField.objects.create(form=form, order=order, **field)

        return form
    


class EmployeeFieldValueSerializer(serializers.ModelSerializer):
    field_id = serializers.IntegerField()

    class Meta:
        model = EmployeeFieldValue
        fields = ["field_id", "value"]


class EmployeeCreateSerializer(serializers.ModelSerializer):
    form_id = serializers.IntegerField(write_only=True)
    fields = EmployeeFieldValueSerializer(many=True, write_only=True)

    class Meta:
        model = Employee
        fields = ["id", "form_id", "fields", "created_at"]

    def create(self, validated_data):
        form_id = validated_data.pop("form_id")
        fields_data = validated_data.pop("fields")

        try:
            form = DynamicForm.objects.get(id=form_id)
        except DynamicForm.DoesNotExist:
            raise serializers.ValidationError({"form_id": "Form not found."})

        employee = Employee.objects.create(form=form)

        for field_data in fields_data:
            field_id = field_data.get("field_id")
            value = field_data.get("value", "")

            try:
                field = DynamicField.objects.get(id=field_id, form=form)
            except DynamicField.DoesNotExist:
                raise serializers.ValidationError({"field_id": f"Invalid field_id {field_id} for this form"})

            EmployeeFieldValue.objects.create(
                employee=employee,
                field=field,
                value=value
            )

        return employee


class EmployeeFieldValueReadSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source="field.label", read_only=True)
    field_type = serializers.CharField(source="field.field_type", read_only=True)

    class Meta:
        model = EmployeeFieldValue
        fields = ["field_id", "field_label", "field_type", "value"]


class EmployeeReadSerializer(serializers.ModelSerializer):
    fields = EmployeeFieldValueReadSerializer(source="field_values", many=True, read_only=True)

    class Meta:
        model = Employee
        fields = ["id", "form_id", "fields", "created_at"]
        

class EmployeeFieldValueUpdateSerializer(serializers.ModelSerializer):
    field_id = serializers.IntegerField()

    class Meta:
        model = EmployeeFieldValue
        fields = ["field_id", "value"]


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    fields = EmployeeFieldValueUpdateSerializer(
        many=True, required=True, source="field_values"
    )

    class Meta:
        model = Employee
        fields = ["id", "form", "fields"]
        read_only_fields = ["form"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["fields"] = [
            {
                "field_id": fv.field.id,
                "label": fv.field.label,
                "value": fv.value
            }
            for fv in instance.field_values.all()
        ]
        return representation

    def update(self, instance, validated_data):
        fields_data = validated_data.pop("field_values", [])

        for field_data in fields_data:
            field_id = field_data.get("field_id")
            value = field_data.get("value")

            field_value, created = EmployeeFieldValue.objects.get_or_create(
                employee=instance, field_id=field_id
            )
            field_value.value = value
            field_value.save()

        instance.save()
        return instance