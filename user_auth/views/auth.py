from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import IntegrityError
from django.urls import reverse


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        errors = []
        try:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse(
                    {
                        "success": True,
                        "message": "تم تسجيل الدخول بنجاح",
                        "redirect_url": reverse("dashboard:index"),
                    }
                )
            else:
                errors.append("اسم المستخدم أو كلمة المرور غير صحيحة")
                return JsonResponse({"success": False, "errors": errors})
        except Exception as e:
            errors.append(str(e))
            return JsonResponse({"success": False, "errors": errors})

    return render(request, "auth.html", {"mode": "login"})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        errors = []

        if not all([username, email, password, confirm_password]):
            errors.append("يرجى ملء جميع الحقول")
        elif password != confirm_password:
            errors.append("كلمات المرور غير متطابقة")
        elif User.objects.filter(username=username).exists():
            errors.append("اسم المستخدم موجود بالفعل")
        elif User.objects.filter(email=email).exists():
            errors.append("البريد الإلكتروني مستخدم بالفعل")

        if not errors:
            try:
                user = User.objects.create_user(
                    username=username, email=email, password=password
                )
                login(request, user)
                return JsonResponse(
                    {"success": True, "message": "تم إنشاء الحساب بنجاح"}
                )
            except IntegrityError:
                errors.append("حدث خطأ أثناء إنشاء الحساب")
            except Exception as e:
                errors.append(str(e))

        return JsonResponse({"success": False, "errors": errors})

    return render(request, "auth.html", {"mode": "signup"})


def lost_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        errors = []

        if not email:
            errors.append("يرجى إدخال البريد الإلكتروني")
        else:
            if User.objects.filter(email=email).exists():
                # logic for sending reset email would go here
                return JsonResponse(
                    {
                        "success": True,
                        "message": "تم إرسال رابط تعيين كلمة المرور إلى بريدك الإلكتروني",
                    }
                )
            else:
                errors.append("البريد الإلكتروني غير موجود")

        return JsonResponse({"success": False, "errors": errors})

    return render(request, "auth.html", {"mode": "lost_password"})


def logout_view(request):
    logout(request)
    return redirect("user_auth:login")
