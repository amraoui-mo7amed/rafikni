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


class Course(models.Model):
    """Course model for educational content"""

    title = models.CharField(max_length=255, verbose_name="عنوان الدورة")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="السعر (د.ج)"
    )
    teacher_name = models.CharField(max_length=100, verbose_name="اسم المعلم")
    description = models.TextField(verbose_name="وصف الدورة")
    tags = models.CharField(
        max_length=500, verbose_name="الوسوم (مفصولة بفاصلة)", blank=True
    )
    thumbnail = models.ImageField(
        upload_to="courses/thumbnails/",
        verbose_name="صورة الغلاف",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="تم الإنشاء بواسطة",
        related_name="created_courses",
    )

    class Meta:
        verbose_name = "دورة تعليمية"
        verbose_name_plural = "الدورات التعليمية"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_video_count(self):
        return self.videos.count()

    def get_tags_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
        return []


class Video(models.Model):
    """Video model for course content"""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="videos", verbose_name="الدورة"
    )
    title = models.CharField(max_length=255, verbose_name="عنوان الفيديو")
    description = models.TextField(verbose_name="وصف الفيديو", blank=True)
    video_file = models.FileField(
        upload_to="courses/videos/", verbose_name="ملف الفيديو"
    )
    duration = models.DurationField(verbose_name="المدة", blank=True, null=True)
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_free = models.BooleanField(default=False, verbose_name="مجاني")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    class Meta:
        verbose_name = "فيديو"
        verbose_name_plural = "الفيديوهات"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def save(self, *args, **kwargs):
        """Automatically mark first video as free"""
        if self.order == 0 and self.course.videos.count() == 0:
            self.is_free = True
        super().save(*args, **kwargs)


class CourseEnrollment(models.Model):
    """Track user enrollment in courses"""

    class EnrollmentStatus(models.TextChoices):
        PENDING = "pending", "قيد الانتظار"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="course_enrollments",
        verbose_name="المستخدم",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="الدورة",
    )
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.PENDING,
        verbose_name="حالة التسجيل",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التسجيل")
    approved_at = models.DateTimeField(
        blank=True, null=True, verbose_name="تاريخ القبول"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="approved_enrollments",
        verbose_name="تم القبول بواسطة",
    )

    class Meta:
        verbose_name = "تسجيل في دورة"
        verbose_name_plural = "التسجيلات في الدورات"
        unique_together = ["user", "course"]

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"


class Payment(models.Model):
    """Payment model for course enrollment"""

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "قيد المراجعة"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"

    enrollment = models.OneToOneField(
        CourseEnrollment,
        on_delete=models.CASCADE,
        related_name="payment",
        verbose_name="التسجيل",
    )
    receipt_image = models.ImageField(
        upload_to="payments/receipts/%Y/%m/", verbose_name="صورة الإيصال"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="المبلغ المدفوع"
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="حالة الدفع",
    )
    notes = models.TextField(verbose_name="ملاحظات", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الدفع")
    reviewed_at = models.DateTimeField(
        blank=True, null=True, verbose_name="تاريخ المراجعة"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reviewed_payments",
        verbose_name="تمت المراجعة بواسطة",
    )

    class Meta:
        verbose_name = "دفع"
        verbose_name_plural = "المدفوعات"

    def __str__(self):
        return f"دفع {self.amount} د.ج - {self.enrollment.course.title}"
