from django.db import models


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
