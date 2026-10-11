from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_welcome_email(user_id):
    user = CustomUser.objects.get(id=user_id)
    send_mail(
        'Welcome to DreamKaro Cricket',
        f'Hi {user.username}, ready to join contests?',
        'noreply@dreamkaro.com',
        [user.email],
        fail_silently=False,
    )

@shared_task
def process_payment_async(transaction_id):
    # Payment gateway integration logic
    pass
