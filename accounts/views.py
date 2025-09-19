import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import DynamicForm, DynamicField, Employee, EmployeeFieldValue


User = get_user_model()


@csrf_exempt
def register_user(request):
    if request.method == 'GET':
        return render(request, 'user/register.html')
    elif request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone = request.POST.get("phone")
        profile_picture = request.FILES.get("profile_picture")

        if not username or not email or not password:
            return JsonResponse({"success": False, "error": "All fields are required"}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"success": False, "error": "Username already exists"}, status=400)
        
        user = User.objects.create(
            username=username,
            email=email,
            phone=phone,
            profile_picture=profile_picture,
            password=make_password(password)
        )
        return JsonResponse({"success": True, "message": "User registered successfully"})
    return JsonResponse({"error": "Invalid request"}, status=400)



@csrf_exempt
def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            return JsonResponse({"success": False, "error": "Both fields are required"}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({"success": True, "message": "Login successful"})
        else:
            return JsonResponse({"success": False, "error": "Invalid username or password"}, status=400)
    elif request.method == 'GET':
        return render(request, 'user/login.html')
    
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def dashboard_view(request):
    return render(request, "user/dashboard.html", {"user": request.user})


@login_required
def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/accounts/login/")


@login_required
@csrf_exempt
def change_password(request):
    if request.method == "GET":
        return render(request, "user/change_password.html")
    elif request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        user = request.user

        if not check_password(current_password, user.password):
            return JsonResponse({"success": False, "error": "Current password is incorrect"}, status=400)

        if new_password != confirm_password:
            return JsonResponse({"success": False, "error": "New passwords do not match"}, status=400)

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)

        return JsonResponse({"success": True, "message": "Password changed successfully", "redirect_url": reverse("dashboard")})

    return JsonResponse({"error": "Invalid request"}, status=400)



@login_required
@csrf_exempt
def profile_view(request):
    if request.method == "GET":
        return render(request, "user/profile.html", {"user": request.user})

    elif request.method == "POST":
        user = request.user
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        profile_picture = request.FILES.get("profile_picture")

        if username: user.username = username
        if email: user.email = email
        if phone: user.phone = phone
        if profile_picture: user.profile_picture = profile_picture

        user.save()

        return JsonResponse({"success": True, "message": "Profile updated successfully"})
    



def form_builder(request):
    return render(request, "formbuilder/form_builder.html")



def form_list(request):
    forms = DynamicForm.objects.all()
    return render(request, "formbuilder/form_list.html", {"forms": forms})



@csrf_exempt
def save_form(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))

        form_name = data.get("form_name")
        form_description = data.get("form_description", "")
        fields = data.get("fields", [])

        if not form_name or not fields:
            return JsonResponse({"success": False, "error": "Form name and fields are required"}, status=400)

        form = DynamicForm.objects.create(
            name=form_name,
            description=form_description
        )

        for index, field in enumerate(fields, start=1):
            DynamicField.objects.create(
                form=form,
                label=field.get("label"),
                field_type=field.get("field_type"),
                required=field.get("required", True),
                options=field.get("options", None),
                placeholder=field.get("placeholder", ""),
                help_text=field.get("help_text", ""),
                order=field.get("order", index)
            )

        return JsonResponse({"success": True, "message": "Form saved successfully", "form_id": form.id, "redirect_url": "/accounts/form/list/"})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)



def form_detail(request, form_id):
    form = get_object_or_404(DynamicForm, id=form_id)
    fields = form.fields.all()
    return render(request, "formbuilder/form_detail.html", {"form": form, "fields": fields})



# Employee details
# -------------------------------------

def create_employee_view(request):
    forms = DynamicForm.objects.all()
    return render(request, "employee/create_employee.html", {"forms": forms})


def get_form_fields(request, form_id):
    print("dark")
    try:
        form = DynamicForm.objects.get(id=form_id)
        fields = form.fields.all().order_by("order")

        fields_data = []
        for f in fields:
            fields_data.append({
                "id": f.id,
                "label": f.label,
                "field_type": f.field_type,
                "required": f.required,
                "placeholder": f.placeholder,
                "help_text": f.help_text,
                "options": f.options if f.options else []
            })

        return JsonResponse({"success": True, "form": form.name, "fields": fields_data})
    except DynamicForm.DoesNotExist:
        return JsonResponse({"success": False, "error": "Form not found"}, status=404)
    
    
@login_required 
@csrf_exempt
def save_employee(request):
    """Save employee details submitted from dynamic form"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            form_id = data.get("form_id")
            fields = data.get("fields", [])

            form = get_object_or_404(DynamicForm, id=form_id)
            employee = Employee.objects.create(form=form)

            for field_data in fields:
                field_id = field_data.get("field_id")
                value = field_data.get("value")

                field = get_object_or_404(DynamicField, id=field_id, form=form)
                EmployeeFieldValue.objects.create(
                    employee=employee,
                    field=field,
                    value=value
                )

            return JsonResponse({"success": True, "message": "Employee created successfully!"})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


def employee_list(request):
    forms = DynamicForm.objects.all()
    selected_form_id = request.GET.get("form")
    employees = Employee.objects.all()
    selected_form = None
    fields = None

    if selected_form_id:
        selected_form = DynamicForm.objects.filter(id=selected_form_id).first()

        if selected_form:
            employees = employees.filter(form_id=selected_form.id)
            fields = selected_form.fields.all()
            for key, value in request.GET.items():
                if key.startswith("field_") and value.strip():
                    field_id = key.split("_")[1]
                    employees = employees.filter(
                        field_values__field_id=field_id,
                        field_values__value__icontains=value
                    )

    return render(request, "employee/employee_list.html", {
        "forms": forms,
        "employees": employees.distinct(),
        "selected_form_id": selected_form_id,
        "selected_form": selected_form,
        "fields": fields,
    })
    
    
def delete_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    employee.delete()

    form_id = request.GET.get('form', '')
    if form_id:
        return redirect(f'/accounts/employee/list/?form={form_id}')
    return redirect('/accounts/employee/list/')


def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    form = employee.form
    fields = form.fields.all()

    existing_values = {fv.field.id: fv.value for fv in employee.field_values.all()}

    if request.method == "POST":
        for field in fields:
            field_value = request.POST.get(f'field_{field.id}', '')
            fv, created = EmployeeFieldValue.objects.get_or_create(
                employee=employee, field=field
            )
            fv.value = field_value
            fv.save()
        return redirect(f'/accounts/employee/list/?form={form.id}')

    return render(request, 'employee/edit_employee.html', {
        'employee': employee,
        'form': form,
        'fields': fields,
        'existing_values': existing_values,
    })
    
    


# REST APIs for All the above functionalities
# --------------------------------------------------

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .serializers import UserRegisterSerializer, UserLoginSerializer, UserDetailSerializer, ChangePasswordSerializer, \
    LogoutSerializer, UserUpdateSerializer, DynamicFormSerializer, EmployeeCreateSerializer, EmployeeReadSerializer, EmployeeUpdateSerializer


class UserRegisterAPI(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserLoginAPI(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                "success": True,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh)
            })
        else:
            return Response({
                "success": False,
                "error": "Invalid username or password"
            }, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserDetailSerializer(user)
        return Response({
            "success": True,
            "user": serializer.data
        })
       
     
        
class ChangePasswordAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        if not check_password(current_password, user.password):
            return Response({"success": False, "error": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(new_password)
        user.save()
        return Response({"success": True, "message": "Password changed successfully"})
    


class UserUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserUpdateSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Profile updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DynamicFormCreateAPI(generics.CreateAPIView):
    queryset = DynamicForm.objects.all()
    serializer_class = DynamicFormSerializer
    permission_classes = [IsAuthenticated]


class DynamicFormListAPI(generics.ListAPIView):
    queryset = DynamicForm.objects.all()
    serializer_class = DynamicFormSerializer
    permission_classes = [IsAuthenticated]


class DynamicFormDetailAPI(generics.RetrieveAPIView):
    queryset = DynamicForm.objects.all()
    serializer_class = DynamicFormSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    

class EmployeeCreateAPIView(generics.CreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeCreateSerializer
    permission_classes = [IsAuthenticated]
    

class EmployeeListByFormAPIView(generics.ListAPIView):
    serializer_class = EmployeeReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        form_id = self.kwargs.get("form_id")
        return Employee.objects.filter(form_id=form_id).prefetch_related("field_values__field")


class EmployeeUpdateAPIView(generics.UpdateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    

class EmployeeDeleteAPIView(APIView):
    def delete(self, request, employee_id):
        employee = get_object_or_404(Employee, id=employee_id)
        employee.delete()
        return Response(
            {"success": True, "message": "Employee deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )