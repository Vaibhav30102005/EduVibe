from flask_mail import Message
import os
from flask_mail import Message
from app import mail

def send_otp_email(user_email, otp, purpose="verification"):

    if purpose == "reset":
        subject = "EduVibe Password Reset OTP"
        message = f"""
You requested a password reset.

Your password reset OTP is:

{otp}

If you did not request this, please ignore this email.
"""

    else:
        subject = "EduVibe Email Verification"
        message = f"""
Welcome to EduVibe!

Your email verification code is:

{otp}

Enter this code to complete registration.
"""

    msg = Message(
        subject=subject,
        sender=os.getenv("MAIL_USERNAME"),
        recipients=[user_email]
    )

    msg.body = message

    mail.send(msg)