#!/usr/bin/env python3
"""
TributeMaker Email Configuration Helper
Helps users set up email authentication with various providers and troubleshoot issues.
"""

import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailConfigHelper:
    """Helper class for email configuration and testing"""
    
    # Common email provider configurations
    PROVIDERS = {
        'gmail': {
            'name': 'Gmail',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'requires_app_password': True,
            'setup_url': 'https://myaccount.google.com/apppasswords',
            'instructions': [
                '1. Enable 2-Factor Authentication on your Google account',
                '2. Go to https://myaccount.google.com/apppasswords',
                '3. Generate an App Password for "Mail"',
                '4. Use the 16-character App Password (not your regular password)'
            ]
        },
        'outlook': {
            'name': 'Outlook/Hotmail',
            'smtp_server': 'smtp-mail.outlook.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'requires_app_password': False,
            'setup_url': 'https://outlook.live.com/mail/',
            'instructions': [
                '1. Use your regular Outlook/Hotmail email and password',
                '2. Make sure "Less secure app access" is enabled if needed',
                '3. Some accounts may require App Password - check security settings'
            ]
        },
        'yahoo': {
            'name': 'Yahoo Mail',
            'smtp_server': 'smtp.mail.yahoo.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'requires_app_password': True,
            'setup_url': 'https://login.yahoo.com/account/security',
            'instructions': [
                '1. Enable 2-Factor Authentication on your Yahoo account',
                '2. Go to Account Security settings',
                '3. Generate an App Password for "Mail"',
                '4. Use the App Password instead of your regular password'
            ]
        },
        'sendgrid': {
            'name': 'SendGrid (Recommended for Production)',
            'smtp_server': 'smtp.sendgrid.net',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'requires_app_password': False,
            'setup_url': 'https://sendgrid.com/',
            'instructions': [
                '1. Sign up for a free SendGrid account',
                '2. Create an API key in Settings > API Keys',
                '3. Use "apikey" as username and your API key as password',
                '4. Verify your sender identity'
            ]
        },
        'mailgun': {
            'name': 'Mailgun (Recommended for Production)',
            'smtp_server': 'smtp.mailgun.org',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'requires_app_password': False,
            'setup_url': 'https://www.mailgun.com/',
            'instructions': [
                '1. Sign up for a free Mailgun account',
                '2. Add and verify your domain',
                '3. Get SMTP credentials from your domain settings',
                '4. Use the provided username and password'
            ]
        }
    }
    
    def __init__(self):
        # Load .env file first
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Environment variables loaded from .env file")
        except ImportError:
            print("ℹ️  python-dotenv not installed. Using system environment variables only.")
        except Exception as e:
            print(f"⚠️  Error loading .env file: {e}")
        
        self.current_config = self.load_current_config()
    
    def load_current_config(self):
        """Load current email configuration from environment"""
        return {
            'smtp_server': os.environ.get('MAIL_SERVER', ''),
            'smtp_port': int(os.environ.get('MAIL_PORT', 587)),
            'username': os.environ.get('MAIL_USERNAME', ''),
            'password': os.environ.get('MAIL_PASSWORD', ''),
            'use_tls': os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true',
            'use_ssl': os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
        }
    
    def test_network_connectivity(self, server, port, timeout=10):
        """Test basic network connectivity to SMTP server"""
        try:
            print(f"Testing network connectivity to {server}:{port}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((server, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Network connectivity OK")
                return True
            else:
                print(f"❌ Network connectivity failed (error code: {result})")
                return False
        except Exception as e:
            print(f"❌ Network connectivity test failed: {e}")
            return False
    
    def test_smtp_connection(self, config, timeout=30):
        """Test SMTP connection with given configuration"""
        try:
            print(f"Testing SMTP connection to {config['smtp_server']}:{config['smtp_port']}...")
            
            if config.get('use_ssl'):
                server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'], timeout=timeout)
            else:
                server = smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=timeout)
                if config.get('use_tls'):
                    server.starttls()
            
            if config['username'] and config['password']:
                server.login(config['username'], config['password'])
                print(f"✅ SMTP authentication successful")
            
            server.quit()
            print(f"✅ SMTP connection successful")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP authentication failed: {e}")
            return False
        except Exception as e:
            print(f"❌ SMTP connection failed: {e}")
            return False
    
    def send_test_email(self, config, to_email=None):
        """Send a test email using the given configuration"""
        try:
            if not to_email:
                to_email = config['username']
            
            msg = MIMEMultipart()
            msg['From'] = config['username']
            msg['To'] = to_email
            msg['Subject'] = "TributeMaker Email Test"
            
            body = """
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d9982f;">TributeMaker Email Test</h2>
                <p>Congratulations! Your email configuration is working correctly.</p>
                <p>This test email was sent successfully from your TributeMaker application.</p>
                <p style="color: #666; font-size: 12px;">
                    You can safely delete this email.
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            if config.get('use_ssl'):
                server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'], timeout=30)
            else:
                server = smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=30)
                if config.get('use_tls'):
                    server.starttls()
            
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Test email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Test email failed: {e}")
            return False
    
    def generate_env_config(self, provider_key, username, password):
        """Generate .env configuration for a specific provider"""
        if provider_key not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_key}")
        
        provider = self.PROVIDERS[provider_key]
        
        config = f"""# TributeMaker Email Configuration - {provider['name']}
MAIL_SERVER={provider['smtp_server']}
MAIL_PORT={provider['smtp_port']}
MAIL_USE_TLS={provider['use_tls']}
MAIL_USE_SSL={provider['use_ssl']}

# Your {provider['name']} credentials
MAIL_USERNAME={username}
MAIL_PASSWORD={password}

# Setup instructions for {provider['name']}:
"""
        
        for instruction in provider['instructions']:
            config += f"# {instruction}\n"
        
        config += f"# Setup URL: {provider['setup_url']}\n"
        
        return config
    
    def diagnose_current_setup(self):
        """Diagnose the current email setup and provide recommendations"""
        print("🔍 TributeMaker Email Configuration Diagnosis")
        print("=" * 60)
        
        config = self.current_config
        
        # Check if configuration exists
        if not config['username'] or not config['password']:
            print("❌ Email credentials not configured")
            print("📝 Recommendation: Set up email credentials in .env file")
            self.show_setup_options()
            return False
        
        print(f"📧 Current configuration:")
        print(f"   Server: {config['smtp_server']}:{config['smtp_port']}")
        print(f"   Username: {config['username']}")
        print(f"   TLS: {config['use_tls']}, SSL: {config['use_ssl']}")
        
        # Test network connectivity
        if not self.test_network_connectivity(config['smtp_server'], config['smtp_port']):
            print("\n🔧 Network connectivity issues detected:")
            print("   - Check your firewall settings")
            print("   - Try using a mobile hotspot")
            print("   - Contact your ISP about SMTP restrictions")
            print("   - Consider using a cloud email service (SendGrid, Mailgun)")
            return False
        
        # Test SMTP connection
        if not self.test_smtp_connection(config):
            print("\n🔧 SMTP connection issues detected:")
            print("   - Verify your email credentials")
            print("   - Check if App Password is required")
            print("   - Try alternative email providers")
            self.show_alternative_providers()
            return False
        
        # Test email sending
        if self.send_test_email(config):
            print("\n🎉 Email configuration is working perfectly!")
            return True
        else:
            print("\n⚠️ Email sending failed despite successful connection")
            return False
    
    def show_setup_options(self):
        """Show available email provider setup options"""
        print("\n📋 Available Email Providers:")
        print("-" * 40)
        
        for key, provider in self.PROVIDERS.items():
            print(f"\n{provider['name']} ({key}):")
            print(f"   Server: {provider['smtp_server']}:{provider['smtp_port']}")
            print(f"   App Password Required: {'Yes' if provider['requires_app_password'] else 'No'}")
            print(f"   Setup: {provider['setup_url']}")
    
    def show_alternative_providers(self):
        """Show alternative email providers for better reliability"""
        print("\n🌟 Recommended Alternative Providers:")
        print("-" * 45)
        
        alternatives = ['sendgrid', 'mailgun', 'outlook']
        for key in alternatives:
            provider = self.PROVIDERS[key]
            print(f"\n✨ {provider['name']}:")
            for instruction in provider['instructions']:
                print(f"   {instruction}")
            print(f"   Setup: {provider['setup_url']}")
    
    def interactive_setup(self):
        """Interactive email setup wizard"""
        print("\n🧙‍♂️ TributeMaker Email Setup Wizard")
        print("=" * 40)
        
        self.show_setup_options()
        
        print("\nWhich email provider would you like to use?")
        provider_keys = list(self.PROVIDERS.keys())
        for i, key in enumerate(provider_keys, 1):
            print(f"{i}. {self.PROVIDERS[key]['name']} ({key})")
        
        try:
            choice = int(input("\nEnter your choice (1-{}): ".format(len(provider_keys))))
            if 1 <= choice <= len(provider_keys):
                provider_key = provider_keys[choice - 1]
                provider = self.PROVIDERS[provider_key]
                
                print(f"\n📋 Setting up {provider['name']}:")
                for instruction in provider['instructions']:
                    print(f"   {instruction}")
                
                username = input(f"\nEnter your {provider['name']} email: ").strip()
                password = input(f"Enter your {provider['name']} password/app password: ").strip()
                
                # Generate configuration
                env_config = self.generate_env_config(provider_key, username, password)
                
                # Test configuration
                test_config = {
                    'smtp_server': provider['smtp_server'],
                    'smtp_port': provider['smtp_port'],
                    'username': username,
                    'password': password,
                    'use_tls': provider['use_tls'],
                    'use_ssl': provider['use_ssl']
                }
                
                print(f"\n🧪 Testing {provider['name']} configuration...")
                if self.test_smtp_connection(test_config):
                    print(f"\n✅ {provider['name']} configuration successful!")
                    
                    # Save to .env file
                    with open('.env', 'w') as f:
                        f.write(env_config)
                    print("💾 Configuration saved to .env file")
                    
                    # Send test email
                    if input("\nSend test email? (y/n): ").lower() == 'y':
                        self.send_test_email(test_config)
                else:
                    print(f"\n❌ {provider['name']} configuration failed")
                    print("Please check your credentials and try again")
            else:
                print("Invalid choice")
        except (ValueError, KeyboardInterrupt):
            print("\nSetup cancelled")

def main():
    """Main function for command-line usage"""
    helper = EmailConfigHelper()
    
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'diagnose':
            helper.diagnose_current_setup()
        elif command == 'setup':
            helper.interactive_setup()
        elif command == 'providers':
            helper.show_setup_options()
        else:
            print("Usage: python email_config_helper.py [diagnose|setup|providers]")
    else:
        # Default: run diagnosis
        helper.diagnose_current_setup()

if __name__ == "__main__":
    main() 