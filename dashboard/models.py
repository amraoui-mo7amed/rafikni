from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from user_auth.models import UserProfile


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
    is_approved = models.BooleanField(default=False, verbose_name="مقبول")

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
    """Generic Payment model"""

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "قيد المراجعة"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="المستخدم",
    )
    # Generic relation to the payable object (CourseEnrollment, MedicalCase, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="نوع المحتوى",
    )
    object_id = models.PositiveIntegerField(verbose_name="معرف الكائن")
    content_object = GenericForeignKey("content_type", "object_id")

    receipt_image = models.ImageField(
        upload_to="payments/receipts/%Y/%m/", verbose_name="صورة الإيصال"
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="حالة الدفع",
    )
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


class Notification(models.Model):
    """Notification model for user notifications"""

    class NotificationType(models.TextChoices):
        INFO = "info", "معلومة"
        SUCCESS = "success", "نجاح"
        WARNING = "warning", "تحذير"
        ERROR = "error", "خطأ"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="المستخدم",
    )
    title = models.CharField(max_length=255, verbose_name="العنوان")
    message = models.TextField(verbose_name="الرسالة")
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        verbose_name="نوع الإشعار",
    )
    is_read = models.BooleanField(default=False, verbose_name="مقروء")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    read_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ القراءة")
    link = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="الرابط",
        help_text="رابط اختياري للتنقل",
    )

    class Meta:
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class Article(models.Model):
    """Article model for blog and educational content"""

    class CategoryChoices(models.TextChoices):
        BEFORE_BIRTH = "before_birth", "قبل الولادة"
        DURING_BIRTH = "during_birth", "أثناء الولادة"
        AFTER_BIRTH = "after_birth", "بعد الولادة"

    title = models.CharField(max_length=255, verbose_name="عنوان المقال")
    slug = models.SlugField(
        max_length=255, unique=True, verbose_name="الرابط المختصر", allow_unicode=True
    )
    content = models.TextField(verbose_name="المحتوى")
    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        verbose_name="الفئة",
    )
    tags = models.CharField(
        max_length=500,
        verbose_name="الوسوم (مفصولة بفاصلة)",
        blank=True,
        help_text="لأغراض SEO",
    )
    thumbnail = models.ImageField(
        upload_to="articles/thumbnails/",
        verbose_name="صورة الغلاف",
        blank=True,
        null=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name="الكاتب",
    )
    is_published = models.BooleanField(default=False, verbose_name="تم النشر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مقال"
        verbose_name_plural = "المقالات"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_tags_list(self):
        """Return tags as a list for SEO and display"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
        return []
