import smtplib
from email.mime.text import MIMEText
import random
import string
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

def generate_verification_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def send_verification_email(user, verification_code):
    sender_email = settings.EMAIL_HOST_USER
    sender_password = settings.EMAIL_HOST_PASSWORD
    recipient_email = user.email
    subject = "Email Verification - Mafia Game"
    
    context = {
        'username': user.username,
        'verification_code': verification_code
    }
    
    html_content = render_to_string('myapp/email/verification_email.html', context)
    
    html_message = MIMEText(html_content, 'html')
    html_message['Subject'] = subject
    html_message['From'] = sender_email
    html_message['To'] = recipient_email
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, html_message.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_password_reset_email(user):
    sender_email = settings.EMAIL_HOST_USER
    sender_password = settings.EMAIL_HOST_PASSWORD
    recipient_email = user.email
    subject = "Password Reset - Mafia Game"
    
    # Generate reset token
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Construct reset link with proper URL formatting
    reset_link = f"{settings.PASSWORD_RESET_URL}/reset-password/{uid}/{token}"
    
    context = {
        'username': user.username,
        'reset_link': reset_link
    }
    
    html_content = render_to_string('myapp/email/password_reset_email.html', context)
    
    html_message = MIMEText(html_content, 'html')
    html_message['Subject'] = subject
    html_message['From'] = sender_email
    html_message['To'] = recipient_email
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, html_message.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False 