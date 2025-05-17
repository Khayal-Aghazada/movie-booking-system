# app/utils.py

import smtplib
from email.mime.text import MIMEText

def send_confirmation_email(to_email, subject, message):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "n199ald0@gmail.com"
    sender_password = "byzv uvsi twac nvlf"  # Use an app-specific password

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            print("Email sent successfully!")
    except Exception as e:
        print("Failed to send email:", e)
