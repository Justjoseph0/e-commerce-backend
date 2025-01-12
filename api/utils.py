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
    
  
    frontend_url = "http://localhost:5173"  
    
    # activation URL for frontend 
    activation_link = f"{frontend_url}/activate/{uid}/{token}/"
    
   
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
        'wurldblog@gmail.com',  
        [user.email],           # Recipient email
        fail_silently=False,
    )



def send_resetpassword_email(user,request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))


    frontend_url = "http://localhost:5173" 

    activation_link = f"{frontend_url}/reset-password-confirm/{uid}/{token}/"

    send_mail(
        'Password Reset Request',
        f'Click the following link to reset your password: {activation_link}',
        'wurldblog@gmail.com',
        [user.email],
        fail_silently=False,
     )


def notify_user(order):
    """Send professional email notification for order status updates."""
    html_message = f"""
        <html>
            <body style="font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #2c3338; max-width: 600px; margin: 0 auto; background-color: #f7f7f7; padding: 20px;">
                <div style="background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #1a1a1a; font-size: 24px; margin: 0;">Order Status Update</h1>
                        <p style="color: #666; font-size: 16px; margin-top: 5px;">Order #{order.reference}</p>
                    </div>

                    <p style="font-size: 16px;">Dear {order.user.username},</p>

                    <div style="background-color: #f8fafc; border-left: 4px solid #0066cc; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 16px;">Your order status has been updated to:
                            <span style="display: block; color: #0066cc; font-size: 18px; font-weight: 600; margin-top: 5px;">
                                {order.delivery_status.upper()}
                            </span>
                        </p>
                    </div>

                    <div style="background-color: #f8fafc; border-radius: 6px; padding: 20px; margin: 20px 0;">
                        <h2 style="color: #1a1a1a; font-size: 18px; margin: 0 0 15px 0;">Order Summary</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #666;">Order ID:</td>
                                <td style="padding: 8px 0; text-align: right; font-weight: 500;">{order.reference}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;">Total Amount:</td>
                                <td style="padding: 8px 0; text-align: right; font-weight: 500;">${order.total_amount:,.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;">Delivery Address:</td>
                                <td style="padding: 8px 0; text-align: right; font-weight: 500;">{order.address}</td>
                            </tr>
                        </table>
                    </div>

                    <div style="margin: 30px 0;">
                        <h2 style="color: #1a1a1a; font-size: 18px; margin-bottom: 10px;">Next Steps</h2>
                        <p style="color: #444; margin: 0;">You'll receive automatic notifications as your order progresses. For any questions, contact our support team at <a href="mailto:wurldblog@gmail.com" style="color: #0066cc; text-decoration: none;">wurldblog@gmail.com</a>.</p>
                    </div>

                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

                    <p style="color: #666; font-size: 14px; margin: 0;">Best regards,<br>The Wurld Blog Team</p>
                </div>
            </body>
        </html>
    """

    plain_text = f"""
Dear {order.user.username},

Your order #{order.reference} status has been updated to: {order.delivery_status.upper()}

Order Summary:
- Order ID: {order.reference}
- Total Amount: ${order.total_amount:,.2f}
- Delivery Address: {order.address}

You'll receive automatic notifications as your order progresses. For any questions, contact our support team at wurldblog@gmail.com.

Best regards,
The Wurld Blog Team
    """

    send_mail(
        subject=f"Order Status Update - #{order.reference}",
        message=plain_text,
        from_email='wurldblog@gmail.com',
        recipient_list=[order.user.email],
        fail_silently=False,
        html_message=html_message
    )