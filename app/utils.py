import os
import base64
import logging
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import  asyncio
load_dotenv()


async def send_verification_email(link: str, email: str):
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token"
    )

    try:
        service = build('gmail', 'v1', credentials=creds)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                .container {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    max-width: 500px;
                    margin: 0 auto;
                    padding: 40px 20px;
                    background-color: #ffffff;
                    border-radius: 16px;
                    border: 1px solid #e2e8f0;
                    text-align: center;
                }}
                .logo {{ font-size: 26px; font-weight: 800; color: #1a202c; margin-bottom: 30px; letter-spacing: -1px; }}
                .button {{
                    display: inline-block;
                    padding: 16px 36px;
                    background-color: #3182ce;
                    color: #ffffff !important;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    margin: 20px 0;
                }}
                .text {{ color: #4a5568; font-size: 15px; line-height: 1.6; margin-bottom: 20px; }}
                .link-alt {{ font-size: 12px; color: #a0aec0; word-break: break-all; margin-top: 20px; }}
                .footer {{ font-size: 12px; color: #cbd5e0; margin-top: 40px; padding-top: 20px; border-top: 1px solid #edf2f7; }}
            </style>
        </head>
        <body style="background-color: #f7fafc; padding: 20px; margin: 0;">
            <div class="container">
                <div class="logo">CERBETS</div>
                <h2 style="color: #2d3748;">Confirm your registration</h2>
                <p class="text">
                    Welcome to Cerbets! To start using the platform, please confirm your email address:
                </p>
                <a href="{link}" class="button">Confirm email</a>
                <p class="text" style="margin-top: 25px;">This link is valid for 15 minutes.</p>
                <div class="link-alt">
                    If the button does not work, copy and paste this link:<br>{link}
                </div>
                <div class="footer">
                    © 2025 Cerbets API Team.<br>
                    You received this email because you created an account on cerbets.com
                </div>
            </div>
        </body>
        </html>
        """

        message = MIMEText(html_content, "html")
        message['to'] = email
        message['from'] = "cerbetsapinoreply@gmail.com"
        message['subject'] = "Подтверждение почты"

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        logging.info(f"Email sent to {email}")

    except Exception as e:
        logging.error(f"Error sending email: {e}")
        raise e
