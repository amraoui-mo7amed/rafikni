from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    class RoleChoices(models.TextChoices):
        ADMIN = "admin", "مدير"
        DOC = "doc", "طبيب"
        PATIENT = "patient", "مريض"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name="المستخدم"
    )
    birthdate = models.DateField(null=True, blank=True, verbose_name="تاريخ الميلاد")
    role = models.CharField(
        max_length=10,
        choices=RoleChoices.choices,
        default=RoleChoices.PATIENT,
        verbose_name="الدور",
    )
    profile_pic = models.ImageField(
        upload_to="profiles/", null=True, blank=True, verbose_name="الصورة الشخصية"
    )
    phone_number = models.CharField(
        max_length=15, null=True, blank=True, verbose_name="رقم الهاتف"
    )

    class Meta:
        verbose_name = "ملف المستخدم"
        verbose_name_plural = "ملفات المستخدمين"

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
