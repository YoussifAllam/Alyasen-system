from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile


@receiver(post_save, sender=User)
def save_user_password_profile(sender: type, instance: User, created: bool, **kwargs: dict) -> None:
    if created:
        Profile.objects.get_or_create(user=instance)  # ignore the error
    else:
        # For existing users without a profile, create one
        if not hasattr(instance, "profile"):
            Profile.objects.get_or_create(user=instance)  # ignore
