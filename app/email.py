import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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

    try:
        email = Mail(
            from_email=os.getenv("MAIL_DEFAULT_SENDER"),
            to_emails=user_email,
            subject=subject,
            plain_text_content=message
        )

        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(email)

        print("Email sent successfully:", response.status_code)

    except Exception as e:
        print("SendGrid Error:", e)