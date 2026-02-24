from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from user_auth.models import UserProfile


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
        return str(self.name)


class BaseMedicalCase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="المستخدم",
        limit_choices_to={"profile__role": UserProfile.RoleChoices.PATIENT},
    )

    class genderChoices(models.TextChoices):
        MALE = "male", "ذكر"
        FEMALE = "female", "أنثى"

    full_name = models.CharField(
        max_length=100, verbose_name="الاسم الكامل", blank=True, null=True
    )
    age = models.IntegerField(verbose_name="العمر", blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=genderChoices.choices,
        verbose_name="الجنس",
        blank=True,
        null=True,
    )
    aphasie = models.BooleanField(default=False, verbose_name="الحبسة الكلامية")

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if hasattr(self, "user") and self.user:
            profile = getattr(self.user, "profile", None)
            if profile:
                if profile.role != UserProfile.RoleChoices.PATIENT:
                    raise ValidationError({"user": "يجب أن يكون المستخدم في دور مريض."})
            else:
                raise ValidationError({"user": "المستخدم ليس له ملف تعريف."})

    def __str__(self):
        return f"{self.user.username} - {str(self._meta.verbose_name)}"


class ChildMedicalCase(BaseMedicalCase):
    class IntellectualDisabilityChoices(models.TextChoices):
        WEAK = "weak", "ضعيف"
        MIDDLE = "middle", "متوسط"
        HARD = "hard", "شديد"

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

    class Meta:
        verbose_name = "حالة طبية (طفل)"
        verbose_name_plural = "حالات طبية (أطفال)"


class AdultMedicalCase(BaseMedicalCase):
    class Meta:
        verbose_name = "حالة طبية (بالغ)"
        verbose_name_plural = "حالات طبية (بالغين)"


class ElderlyMedicalCase(BaseMedicalCase):
    alzheimer = models.BooleanField(default=False, verbose_name="ألزهايمر")
    parkinson = models.BooleanField(default=False, verbose_name="باركنسون")

    class Meta:
        verbose_name = "حالة طبية (مسن)"
        verbose_name_plural = "حالات طبية (مسنين)"
