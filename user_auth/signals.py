from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from user_auth.models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create a user profile when a user is created.
    If the user is a superuser (admin), the role is automatically set to admin.
    """
    if created:
        role = "patient"
        if instance.is_superuser:
            role = "admin"
        UserProfile.objects.get_or_create(user=instance, defaults={"role": role})


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the user profile when the user object is saved.
    """
    if hasattr(instance, "profile"):
        instance.profile.save()
