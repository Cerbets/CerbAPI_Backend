import os
import httpx
import logging
from dotenv import load_dotenv

# Настройка логирования для отслеживания ошибок
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")


async def send_verification_email(link: str, email: str):
    # Если вы используете onboarding@resend.dev,
    # 'to' может быть ТОЛЬКО вашей личной почтой, на которую вы регали Resend.
    # Для отправки всем нужно подтвердить свой домен.
    from_email ="info@cerbets.streamlit.app"

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
            <h2 style="color: #2d3748;">Подтвердите регистрацию</h2>
            <p class="text">
                Рады видеть вас в Cerbets! Чтобы начать пользоваться платформой, подтвердите свой электронный адрес:
            </p>
            <a href="{link}" class="button">Подтвердить почту</a>
            <p class="text" style="margin-top: 25px;">Ссылка действительна 15 минут.</p>
            <div class="link-alt">
                Если кнопка не работает, скопируйте ссылку:<br>{link}
            </div>
            <div class="footer">
                © 2025 Cerbets API Team. <br>
                Вы получили это письмо, так как создали аккаунт на cerbets.com
            </div>
        </div>
    </body>
    </html>
    """

    payload = {
        "from": from_email,
        "to": [email],
        "subject": "Подтверждение аккаунта Cerbets",
        "html": html_content,
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response = await client.post(
                "https://api.resend.com/emails",
                headers=headers,
                json=payload,
            )

            # Если статус не 2xx, выводим подробности ошибки от Resend
            if response.is_error:
                logger.error(f"Resend API Error: {response.status_code} - {response.text}")

            response.raise_for_status()
            logger.info(f"Email sent successfully to {email}")
            return response.json()

        except httpx.HTTPStatusError as e:
            # Здесь мы ловим 403, 401, 422 и т.д.
            logger.error(f"HTTP error occurred: {e.response.status_code}")
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise e