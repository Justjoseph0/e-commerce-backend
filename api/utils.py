from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
import os

def send_activation_email(user, request):
    # Generate activation token
    token = default_token_generator.make_token(user)
    
    # Create UID
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Manually set the frontend URL (ensure it’s your frontend’s base URL)
    frontend_url = "http://localhost:5173"  # Replace with your actual frontend URL
    
    # Construct the activation URL with frontend URL
    activation_link = f"{frontend_url}/activate/{uid}/{token}/"
    
    # Email subject and message
    subject = 'Activate Your Account'
    message = (
        f"Hello {user.username},\n\n"
        "Thank you for registering on our platform! "
        "To complete your registration and activate your account, "
        "please click the link below:\n\n"
        f"{activation_link}\n\n"
        "This link will expire soon, so please activate your account promptly.\n\n"
        "If you did not sign up for this account, you can safely ignore this email.\n\n"
        "Best regards,\nThe Wurld Blog Team"
    )
    
    # Send email
    send_mail(
        subject,
        message,
        'wurldblog@gmail.com',  # Sender email (use a proper email address for production)
        [user.email],           # Recipient email
        fail_silently=False,
    )
