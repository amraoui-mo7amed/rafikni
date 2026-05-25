from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import Payment
from .utils import notify_admins


@receiver(post_save, sender=Payment)
def notify_admins_on_new_payment(sender, instance, created, **kwargs):
    """
    Sends a notification to all admins when a new payment is submitted.
    """
    if created:
        notify_admins(
            title="إيصال دفع جديد",
            message=f"قام المستخدم {instance.user.username} برفع إيصال دفع",
            notification_type="info",
            link=reverse("dashboard:payment_list"),
        )
