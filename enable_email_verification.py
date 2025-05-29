#!/usr/bin/env python3
"""
Enable Email Verification for TributeMaker
Helps configure email sending while keeping development mode as backup
"""

import os
import shutil
from datetime import datetime
from email_service import email_service

def backup_current_env():
    """Backup current .env file"""
    if os.path.exists('.env'):
        backup_name = f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        shutil.copy('.env', backup_name)
        print(f"✅ Current .env backed up as: {backup_name}")
        return backup_name
    return None

def create_email_enabled_env(email_config):
    """Create .env with email verification enabled"""
    env_content = f"""# TributeMaker Email Configuration - Email Verification Enabled
MAIL_SERVER={email_config['server']}
MAIL_PORT={email_config['port']}
MAIL_USE_TLS={str(email_config['use_tls']).lower()}
MAIL_USE_SSL={str(email_config['use_ssl']).lower()}

# Your email credentials
MAIL_USERNAME={email_config['username']}
MAIL_PASSWORD={email_config['password']}

# Application settings
SECRET_KEY=tribute-maker-secret-key-2024-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production
DATABASE_URL=sqlite:///tributemaker.db

# Email verification settings (ENABLED)
DEVELOPMENT_MODE=false
EMAIL_VERIFICATION_ENABLED=true
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_email_sending():
    """Test email sending with a real verification email"""
    print("\n🧪 Testing Email Sending")
    print("=" * 40)
    
    # Reload email service with new config
    email_service.config = email_service._load_config()
    
    print(f"📧 Email configured: {email_service.is_configured()}")
    print(f"📧 Email enabled: {email_service.is_enabled()}")
    print(f"🔧 Development mode: {email_service.config['development_mode']}")
    
    if not email_service.is_configured():
        print("❌ Email not configured properly")
        return False
    
    # Test SMTP connection
    print("\n🔌 Testing SMTP connection...")
    success, message = email_service.test_connection()
    
    if not success:
        print(f"❌ SMTP connection failed: {message}")
        return False
    
    print("✅ SMTP connection successful!")
    
    # Test sending a verification email
    test_email = input("\nEnter an email address to test verification email sending: ").strip()
    if not test_email:
        print("❌ No email provided")
        return False
    
    print(f"\n📧 Sending test verification email to {test_email}...")
    
    # Generate a test token
    import secrets
    test_token = secrets.token_urlsafe(32)
    
    try:
        success, message = email_service.send_verification_email(
            test_email, 
            test_token, 
            "http://localhost:5000/"
        )
        
        if success:
            print("✅ Verification email sent successfully!")
            print(f"📧 Check {test_email} for the verification email")
            print(f"🔗 Verification link: http://localhost:5000/api/auth/verify/{test_token}")
            return True
        else:
            print(f"❌ Failed to send email: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def main():
    """Main function to enable email verification"""
    print("📧 Enable Email Verification for TributeMaker")
    print("=" * 50)
    
    print("This will configure your app to send actual verification emails.")
    print("Users will need to click the email link to verify their accounts.")
    print()
    
    # Show current status
    print("📊 Current Status:")
    print(f"📧 Email configured: {email_service.is_configured()}")
    print(f"📧 Email enabled: {email_service.is_enabled()}")
    print(f"🔧 Development mode: {email_service.config['development_mode']}")
    
    if email_service.is_enabled():
        print("\n✅ Email verification is already enabled!")
        if input("Test email sending? (y/N): ").lower() == 'y':
            test_email_sending()
        return
    
    print("\n🎯 Email Provider Options:")
    print("1. Gmail (with App Password)")
    print("2. Outlook/Hotmail")
    print("3. Yahoo Mail")
    print("4. Custom SMTP")
    print("5. Cancel (keep development mode)")
    
    choice = input("\nChoose an option (1-5): ").strip()
    
    if choice == "5":
        print("👋 Keeping development mode - no changes made")
        return
    
    # Email provider configurations
    providers = {
        "1": {"name": "Gmail", "server": "smtp.gmail.com", "port": 587, "use_tls": True, "use_ssl": False},
        "2": {"name": "Outlook", "server": "smtp-mail.outlook.com", "port": 587, "use_tls": True, "use_ssl": False},
        "3": {"name": "Yahoo", "server": "smtp.mail.yahoo.com", "port": 587, "use_tls": True, "use_ssl": False},
        "4": {"name": "Custom", "server": "", "port": 587, "use_tls": True, "use_ssl": False}
    }
    
    if choice not in providers:
        print("❌ Invalid choice")
        return
    
    provider = providers[choice]
    
    print(f"\n📧 Setting up {provider['name']} Email")
    print("=" * 40)
    
    if choice == "4":  # Custom SMTP
        provider["server"] = input("SMTP Server: ").strip()
        provider["port"] = int(input("SMTP Port (587): ") or "587")
        provider["use_tls"] = input("Use TLS? (Y/n): ").lower() != 'n'
        provider["use_ssl"] = input("Use SSL? (y/N): ").lower() == 'y'
    
    # Get credentials
    email_address = input(f"Enter your {provider['name']} email address: ").strip()
    
    if choice == "1":  # Gmail
        print("\n🔐 Gmail requires an App Password:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Generate an App Password for 'Mail'")
        print("3. Use the 16-character password below")
        password = input("\nEnter your Gmail App Password: ").strip()
    else:
        password = input(f"Enter your {provider['name']} password: ").strip()
    
    if not email_address or not password:
        print("❌ Email and password are required")
        return
    
    # Backup current config
    backup_file = backup_current_env()
    
    # Create email configuration
    email_config = {
        "server": provider["server"],
        "port": provider["port"],
        "use_tls": provider["use_tls"],
        "use_ssl": provider["use_ssl"],
        "username": email_address,
        "password": password
    }
    
    # Create new .env file
    if create_email_enabled_env(email_config):
        print(f"\n✅ {provider['name']} email configuration saved!")
        print("📧 Email verification is now ENABLED")
        
        # Test the configuration
        if test_email_sending():
            print("\n🎉 Email verification is working perfectly!")
            print("📧 Users will now receive verification emails when they register")
            print("🔗 They must click the email link to verify their accounts")
            
            if backup_file:
                print(f"\n💾 Your previous config is backed up as: {backup_file}")
                print("   You can restore it anytime if needed")
        else:
            print("\n❌ Email configuration failed!")
            if backup_file and os.path.exists(backup_file):
                print("🔄 Restoring previous configuration...")
                shutil.copy(backup_file, '.env')
                print("✅ Previous configuration restored")
    else:
        print("❌ Failed to save email configuration")
        if backup_file and os.path.exists(backup_file):
            print("🔄 Restoring previous configuration...")
            shutil.copy(backup_file, '.env')

if __name__ == "__main__":
    main() 