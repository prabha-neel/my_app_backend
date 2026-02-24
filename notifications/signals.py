from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from students_classroom.models import JoinRequest, JoinRequestStatus, ClassroomSession
from .models import Notification

# 1. Teacher Recruitment Alert
@receiver(post_save, sender=JoinRequest)
def notify_teacher_hiring(sender, instance, created, **kwargs):
    # Agar request ACCEPT hui hai aur purpose TEACHER hai
    if not created and instance.status == JoinRequestStatus.ACCEPTED:
        if instance.session.purpose == 'TEACHER':
            Notification.objects.create(
                recipient=instance.user,
                title="Welcome to the Team!",
                message=f"Mubarak ho! Aap ab {instance.session.organization.name} mein Teacher hain. Apna Dashboard check karein.",
                notification_type='success'
            )

# 2. Seats Full Alert (Teacher/Admin ke liye)
@receiver(post_save, sender=JoinRequest)
def notify_session_full(sender, instance, created, **kwargs):
    # Jab koi request ACCEPT ho, tab check karo limit
    if not created and instance.status == JoinRequestStatus.ACCEPTED:
        session = instance.session
        accepted_count = session.join_requests.filter(status=JoinRequestStatus.ACCEPTED).count()
        
        if accepted_count >= session.student_limit:
            # Teacher ko alert bhejo
            Notification.objects.create(
                recipient=session.teacher, # Jis teacher ki class hai
                title="Classroom Full!",
                message=f"Bhai, {session.target_standard.name} ki seats full ho gayi hain ({accepted_count}/{session.student_limit}).",
                notification_type='warning'
            )

# 3. Account Deactivation Alert
# Iske liye hum NormalUser ke pre_save ka use karenge (kyunki soft_delete field change hogi)
from django.contrib.auth import get_user_model
User = get_user_model()

@receiver(pre_save, sender=User)
def notify_account_deactivation(sender, instance, **kwargs):
    if instance.pk: # Agar user pehle se exist karta hai
        old_instance = User.objects.get(pk=instance.pk)
        # Agar pehle active tha aur ab is_active=False ho raha hai (Soft Delete)
        if old_instance.is_active and not instance.is_active:
            # Hum yahan SuperAdmin ya kisi relevant admin ko notify kar sakte hain
            # Abhi ke liye hum sirf ek notification record bana rahe hain
            print(f"Alert: Account {instance.username} deactivate kiya ja raha hai.")