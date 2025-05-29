#!/usr/bin/env python3
"""
TributeMaker Email Service
Simplified and robust email authentication system
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """Simplified email service for TributeMaker"""
    
    def __init__(self, app=None):
        self.app = app
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load email configuration from environment variables"""
        try:
            # Load environment variables from .env file if available
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            logger.info("python-dotenv not installed. Using system environment variables.")
        
        config = {
            'smtp_server': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.environ.get('MAIL_PORT', 587)),
            'username': os.environ.get('MAIL_USERNAME', ''),
            'password': os.environ.get('MAIL_PASSWORD', ''),
            'use_tls': os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
            'use_ssl': os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true',
            'development_mode': os.environ.get('DEVELOPMENT_MODE', 'true').lower() == 'true',
            'email_verification_enabled': os.environ.get('EMAIL_VERIFICATION_ENABLED', 'true').lower() == 'true'
        }
        
        return config
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.config['username'] and self.config['password'])
    
    def is_enabled(self) -> bool:
        """Check if email verification is enabled"""
        return self.config['email_verification_enabled'] and self.is_configured()
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test SMTP connection"""
        if not self.is_configured():
            return False, "Email credentials not configured"
        
        try:
            logger.info(f"Testing SMTP connection to {self.config['smtp_server']}:{self.config['smtp_port']}")
            
            # Create SMTP connection
            if self.config['use_ssl']:
                server = smtplib.SMTP_SSL(
                    self.config['smtp_server'], 
                    self.config['smtp_port'], 
                    timeout=30
                )
            else:
                server = smtplib.SMTP(
                    self.config['smtp_server'], 
                    self.config['smtp_port'], 
                    timeout=30
                )
                
                if self.config['use_tls']:
                    # Create secure SSL context
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # Test authentication
            server.login(self.config['username'], self.config['password'])
            server.quit()
            
            logger.info("✅ SMTP connection successful")
            return True, "SMTP connection successful"
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"SMTP connection failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def send_verification_email_console(self, user_email, verification_token, base_url):
        """Send verification email to console for development (when SMTP fails)"""
        
        verification_url = f"{base_url}api/auth/verify/{verification_token}"
        
        print("\n" + "="*70)
        print("📧 VERIFICATION EMAIL (Console Mode - SMTP Failed)")
        print("="*70)
        print(f"To: {user_email}")
        print(f"Subject: 🎬 Verify Your TributeMaker Account")
        print(f"\nVerification URL:")
        print(f"🔗 {verification_url}")
        print(f"\nTo verify this user:")
        print(f"1. Copy the URL above")
        print(f"2. Paste it in your browser")
        print(f"3. Or use this token directly: {verification_token}")
        print("="*70 + "\n")
        
        # Also save to file for easy access
        import os
        from datetime import datetime
        os.makedirs('console_emails', exist_ok=True)
        filename = f"console_emails/verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(f"Verification Email\n")
            f.write(f"To: {user_email}\n")
            f.write(f"Token: {verification_token}\n")
            f.write(f"URL: {verification_url}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        
        return True, f"Verification email logged to console and saved to {filename}"

    def _create_verification_email(self, user_email, verification_token, base_url):
        """Create verification email content"""
        verification_url = f"{base_url}api/auth/verify/{verification_token}"
        
        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Verify Your TributeMaker Account</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🎬 TributeMaker</h1>
        <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Create Beautiful Video Tributes</p>
    </div>
    
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
        <h2 style="color: #333; margin-top: 0;">Welcome to TributeMaker! 🎉</h2>
        
        <p>Thank you for joining TributeMaker! To complete your registration and start creating beautiful video tributes, please verify your email address.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}" 
               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; 
                      padding: 15px 30px; 
                      text-decoration: none; 
                      border-radius: 25px; 
                      font-weight: bold; 
                      font-size: 16px;
                      display: inline-block;
                      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                ✅ Verify My Email
            </a>
        </div>
        
        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            If the button doesn't work, copy and paste this link into your browser:<br>
            <a href="{verification_url}" style="color: #667eea; word-break: break-all;">{verification_url}</a>
        </p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        
        <p style="color: #888; font-size: 12px; text-align: center; margin: 0;">
            This email was sent from TributeMaker. If you didn't create an account, you can safely ignore this email.
        </p>
    </div>
</body>
</html>
        """
        
        # Text content
        text_content = f"""
Welcome to TributeMaker!

Thank you for joining TributeMaker! To complete your registration and start creating beautiful video tributes, please verify your email address.

Click this link to verify your email:
{verification_url}

If you didn't create an account, you can safely ignore this email.

Best regards,
The TributeMaker Team
        """
        
        return html_content.strip(), text_content.strip()

    def send_verification_email(self, user_email: str, verification_token: str, request_host: str = None) -> Tuple[bool, str]:
        """Send email verification with console fallback for SMTP failures"""
        
        # Check if email verification is enabled
        if not self.is_enabled():
            if self.config['development_mode']:
                logger.info("📧 Email verification disabled in development mode")
                return True, "Email verification disabled in development mode"
            else:
                logger.warning("📧 Email verification not configured")
                return False, "Email verification not configured"
        
        # Generate base URL
        if request_host:
            base_url = request_host.rstrip('/')
        else:
            base_url = "http://localhost:5000"
        
        # If not configured, use console mode
        if not self.is_configured():
            return self.send_verification_email_console(user_email, verification_token, base_url)
        
        # Try normal email sending first
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['username']
            msg['To'] = user_email
            msg['Subject'] = "🎬 Verify Your TributeMaker Account"
            
            # Create email content
            html_content, text_content = self._create_verification_email(user_email, verification_token, base_url)
            
            # Attach both versions
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            success, error_msg = self._send_email(msg)
            
            if success:
                logger.info(f"✅ Verification email sent successfully to {user_email}")
                return True, "Verification email sent successfully"
            else:
                logger.error(f"❌ Failed to send verification email to {user_email}: {error_msg}")
                # Fall back to console mode
                print(f"⚠️  SMTP email sending failed: {error_msg}")
                print("📧 Falling back to console email mode...")
                return self.send_verification_email_console(user_email, verification_token, base_url)
                
        except Exception as e:
            # SMTP failed - fall back to console mode
            print(f"⚠️  SMTP email sending failed: {e}")
            print("📧 Falling back to console email mode...")
            return self.send_verification_email_console(user_email, verification_token, base_url)
    
    def _send_email(self, msg: MIMEMultipart) -> Tuple[bool, str]:
        """Send email using SMTP"""
        try:
            # Create SMTP connection
            if self.config['use_ssl']:
                server = smtplib.SMTP_SSL(
                    self.config['smtp_server'], 
                    self.config['smtp_port'], 
                    timeout=30
                )
            else:
                server = smtplib.SMTP(
                    self.config['smtp_server'], 
                    self.config['smtp_port'], 
                    timeout=30
                )
                
                if self.config['use_tls']:
                    # Create secure SSL context
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # Authenticate and send
            server.login(self.config['username'], self.config['password'])
            server.send_message(msg)
            server.quit()
            
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError as e:
            return False, f"SMTP Authentication failed: {str(e)}"
        except Exception as e:
            return False, f"SMTP error: {str(e)}"
    
    def send_password_reset_email(self, user_email: str, reset_token: str, request_host: str = None) -> Tuple[bool, str]:
        """Send password reset email"""
        if not self.is_enabled():
            return False, "Email service not configured"
        
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['username']
            msg['To'] = user_email
            msg['Subject'] = "Reset Your TributeMaker Password"
            
            # Generate reset URL
            if request_host:
                base_url = request_host.rstrip('/')
            else:
                base_url = "http://localhost:5000"
            
            reset_url = f"{base_url}/reset-password?token={reset_token}"
            
            # Create HTML content
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Reset Your Password</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #d9982f;">TributeMaker</h1>
    </div>
    
    <div style="background: #f8f9fa; padding: 30px; border-radius: 8px;">
        <h2 style="color: #333;">Password Reset Request</h2>
        <p style="color: #666; line-height: 1.6;">
            We received a request to reset your password. Click the button below to create a new password:
        </p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" 
               style="background: #d9982f; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: 600;">
                Reset Password
            </a>
        </div>
        
        <p style="color: #666; font-size: 14px;">
            If you didn't request this password reset, please ignore this email.
            This link will expire in 1 hour.
        </p>
    </div>
</body>
</html>
            """.strip()
            
            # Create plain text version
            text_content = f"""
TributeMaker Password Reset

We received a request to reset your password.

Click this link to reset your password:
{reset_url}

If you didn't request this password reset, please ignore this email.
This link will expire in 1 hour.

Best regards,
The TributeMaker Team
            """.strip()
            
            # Attach both versions
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            success, error_msg = self._send_email(msg)
            
            if success:
                logger.info(f"✅ Password reset email sent to {user_email}")
                return True, "Password reset email sent successfully"
            else:
                logger.error(f"❌ Failed to send password reset email: {error_msg}")
                return False, f"Failed to send email: {error_msg}"
                
        except Exception as e:
            error_msg = f"Password reset email creation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

# Global email service instance
email_service = EmailService() 