import smtplib
from email.mime.text import MIMEText
import random
import string

def generate_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

code = generate_code()

sender_email = "mafiawebsiteemail@gmail.com"
sender_password = "fvvo udsx dsya kbbq"
recipient_email = "arnav.shah.2k10@gmail.com"
subject = "Email Verification"
body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .code {{ font-size: 24px; font-weight: bold; color: #007bff; letter-spacing: 2px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Welcome to Mafia Game!</h2>
        <p>Thank you for registering. Please verify your email address by entering the following code:</p>
        <p class="code">{code}</p>
        <p>This code will expire in 24 hours.</p>
        <p>If you didn't register for Mafia Game, please ignore this email.</p>
    </div>
</body>
</html> 
"""


html_message = MIMEText(body, 'html')
html_message['Subject'] = subject
html_message['From'] = sender_email
html_message['To'] = recipient_email
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
   
   server.login(sender_email, sender_password)
   server.sendmail(sender_email, recipient_email, html_message.as_string())