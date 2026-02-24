from django.db import models
from django.contrib.auth.models import User


class EmailConfiguration(models.Model):
    name = models.CharField(
        max_length=100, default="Primary Configuration", verbose_name="اسم الإعداد"
    )
    email_host = models.CharField(
        max_length=255, verbose_name="خادم البريد (SMTP Host)"
    )
    email_port = models.IntegerField(default=587, verbose_name="المنفذ (Port)")
    email_host_user = models.CharField(max_length=255, verbose_name="اسم المستخدم")
    email_host_password = models.CharField(max_length=255, verbose_name="كلمة المرور")
    email_use_tls = models.BooleanField(default=True, verbose_name="استخدام TLS")
    email_use_ssl = models.BooleanField(default=False, verbose_name="استخدام SSL")
    default_from_email = models.EmailField(verbose_name="البريد المرسل الافتراضي")
    is_active = models.BooleanField(default=False, verbose_name="تفعيل")

    class Meta:
        verbose_name = "إعدادات البريد الإلكتروني"
        verbose_name_plural = "إعدادات البريد الإلكتروني"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Ensure only one configuration is active
            EmailConfiguration.objects.filter(is_active=True).exclude(
                pk=self.pk
            ).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MedicalCase(models.Model):
    class CategoryChoices(models.TextChoices):
        CHILD = "child", "طفل"
        ADULT = "adult", "بالغ"
        ELDERY = "eldery", "مسن"

    class IntellectualDisabilityChoices(models.TextChoices):
        WEAK = "weak", "ضعيف"
        MIDDLE = "middle", "متوسط"
        HARD = "hard", "شديد"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="medical_cases",
        verbose_name="المستخدم",
    )
    category = models.CharField(
        max_length=10,
        choices=CategoryChoices.choices,
        verbose_name="الفئة",
    )

    # Child fields
    disorders = models.TextField(
        blank=True, null=True, verbose_name="الاضطرابات (مفصولة بفاصلة)"
    )
    syndromes = models.TextField(
        blank=True, null=True, verbose_name="المتلازمات (مفصولة بفاصلة)"
    )
    intellectual_disability = models.CharField(
        max_length=10,
        choices=IntellectualDisabilityChoices.choices,
        blank=True,
        null=True,
        verbose_name="الإعاقة الذهنية",
    )

    # Common/Category specific fields
    aphasie = models.BooleanField(default=False, verbose_name="الحبسة الكلامية")

    # Eldery fields
    alzheimer = models.BooleanField(default=False, verbose_name="ألزهايمر")
    parkinson = models.BooleanField(default=False, verbose_name="باركنسون")

    class Meta:
        verbose_name = "حالة طبية"
        verbose_name_plural = "الحالات الطبية"

    def __str__(self):
        return f"{self.user.username} - {self.get_category_display()}"
