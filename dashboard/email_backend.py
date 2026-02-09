from django.core.mail.backends.smtp import EmailBackend
from .models import EmailConfiguration


class DbEmailBackend(EmailBackend):
    def __init__(self, **kwargs):
        try:
            config = EmailConfiguration.objects.filter(is_active=True).first()
            if config:
                kwargs.update(
                    {
                        "host": config.email_host,
                        "port": config.email_port,
                        "user": config.email_host_user,
                        "password": config.email_host_password,
                        "use_tls": config.email_use_tls,
                        "use_ssl": config.email_use_ssl,
                    }
                )
        except Exception:
            pass
        super().__init__(**kwargs)
