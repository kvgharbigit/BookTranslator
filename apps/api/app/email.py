import httpx
from typing import Dict, Optional

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """Email service using Resend API."""
    
    def __init__(self):
        self.api_key = settings.resend_api_key
        self.from_email = settings.email_from
        self.base_url = "https://api.resend.com"
    
    async def send_completion_email(
        self,
        to_email: str,
        download_urls: Dict[str, str],
        job_id: str,
        output_format: str = "translation"
    ) -> bool:
        """Send completion email with download links."""

        # Customize subject based on format
        if output_format == "bilingual":
            subject = "Your bilingual book is ready!"
        elif output_format == "both":
            subject = "Your translated books are ready!"
        else:
            subject = "Your translated book is ready!"

        html_content = self._create_completion_html(download_urls, job_id, output_format)

        return await self._send_email(to_email, subject, html_content)
    
    async def send_failure_email(
        self, 
        to_email: str, 
        job_id: str, 
        error_message: str
    ) -> bool:
        """Send failure notification email."""
        
        subject = "Translation failed - EPUB Translator"
        
        html_content = self._create_failure_html(job_id, error_message)
        
        return await self._send_email(to_email, subject, html_content)
    
    def _create_completion_html(self, download_urls: Dict[str, str], job_id: str, output_format: str = "translation") -> str:
        """Create HTML content for completion email."""

        format_links = []

        # Customize message based on format
        if output_format == "bilingual":
            intro_message = "Great news! Your bilingual book has been completed successfully. Choose your preferred format below:"
        elif output_format == "both":
            intro_message = "Great news! Your translation and bilingual books have been completed successfully. Choose your preferred format below:"
        else:
            intro_message = "Great news! Your EPUB translation has been completed successfully. Choose your preferred format below:"

        # Standard translation files
        if download_urls.get("epub"):
            format_links.append(f'''
                <a href="{download_urls['epub']}" style="display: block; margin: 10px 0; padding: 12px; background: #e3f2fd; text-decoration: none; border-radius: 4px; color: #1976d2;">
                    📚 <strong>EPUB</strong> - For e-readers (Kindle, Apple Books)
                </a>
            ''')

        if download_urls.get("pdf"):
            format_links.append(f'''
                <a href="{download_urls['pdf']}" style="display: block; margin: 10px 0; padding: 12px; background: #f3e5f5; text-decoration: none; border-radius: 4px; color: #7b1fa2;">
                    📄 <strong>PDF</strong> - For printing or mobile reading
                </a>
            ''')

        if download_urls.get("txt"):
            format_links.append(f'''
                <a href="{download_urls['txt']}" style="display: block; margin: 10px 0; padding: 12px; background: #e8f5e8; text-decoration: none; border-radius: 4px; color: #388e3c;">
                    📝 <strong>TXT</strong> - Plain text for any device
                </a>
            ''')

        # Bilingual files (if available)
        if download_urls.get("bilingual_epub"):
            format_links.append(f'''
                <a href="{download_urls['bilingual_epub']}" style="display: block; margin: 10px 0; padding: 12px; background: #e8eaf6; text-decoration: none; border-radius: 4px; color: #3f51b5;">
                    📚 <strong>EPUB (Bilingual)</strong> - Side-by-side translation for e-readers
                </a>
            ''')

        if download_urls.get("bilingual_pdf"):
            format_links.append(f'''
                <a href="{download_urls['bilingual_pdf']}" style="display: block; margin: 10px 0; padding: 12px; background: #fce4ec; text-decoration: none; border-radius: 4px; color: #c2185b;">
                    📄 <strong>PDF (Bilingual)</strong> - Side-by-side translation for printing
                </a>
            ''')

        if download_urls.get("bilingual_txt"):
            format_links.append(f'''
                <a href="{download_urls['bilingual_txt']}" style="display: block; margin: 10px 0; padding: 12px; background: #e0f2f1; text-decoration: none; border-radius: 4px; color: #00796b;">
                    📝 <strong>TXT (Bilingual)</strong> - Side-by-side translation as plain text
                </a>
            ''')

        links_html = ''.join(format_links)
        
        # Customize title based on format
        if output_format == "bilingual":
            title = "Your bilingual book is ready!"
        elif output_format == "both":
            title = "Your translated books are ready!"
        else:
            title = "Your translated book is ready!"

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
            <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h1 style="color: #2563eb; margin-bottom: 20px; text-align: center;">📚 {title}</h1>

                <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
                    {intro_message}
                </p>
                
                <div style="margin: 20px 0;">
                    {links_html}
                </div>
                
                <div style="background: #f3f4f6; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #6b7280;">
                        <strong>Important:</strong> Download links expire in 48 hours. Files are automatically deleted after 7 days for your privacy.
                    </p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                
                <p style="font-size: 14px; color: #6b7280; text-align: center; margin: 0;">
                    Job ID: {job_id[:8]}... | EPUB Translator | Professional AI Translation Service
                </p>
            </div>
        </body>
        </html>
        '''
    
    def _create_failure_html(self, job_id: str, error_message: str) -> str:
        """Create HTML content for failure email."""
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Translation failed</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
            <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h1 style="color: #dc2626; margin-bottom: 20px; text-align: center;">❌ Translation Failed</h1>
                
                <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
                    We're sorry, but your EPUB translation could not be completed due to a technical issue.
                </p>
                
                <div style="background: #fef2f2; border: 1px solid #fecaca; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #991b1b;">
                        <strong>Error:</strong> {error_message}
                    </p>
                </div>
                
                <div style="background: #f3f4f6; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #6b7280;">
                        <strong>What to do next:</strong><br>
                        • You have not been charged for this failed translation<br>
                        • Please try uploading your file again<br>
                        • If the problem persists, contact our support team
                    </p>
                </div>
                
                <div style="text-align: center; margin: 20px 0;">
                    <a href="https://your-domain.com" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Try Again
                    </a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                
                <p style="font-size: 14px; color: #6b7280; text-align: center; margin: 0;">
                    Job ID: {job_id[:8]}... | EPUB Translator | Professional AI Translation Service
                </p>
            </div>
        </body>
        </html>
        '''
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via Resend API."""
        
        if not self.api_key:
            logger.warning("No Resend API key configured, skipping email")
            return False
        
        payload = {
            "from": self.from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Email sent successfully to {to_email}")
                    return True
                else:
                    logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False


# Global email service instance
email_service = EmailService()