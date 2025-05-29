#!/usr/bin/env python3
"""
TributeMaker Email Setup Script
Simple script to help users set up email authentication
"""

import os
import sys
from email_service import EmailService

def create_env_file():
    """Create .env file with email configuration"""
    print("🔧 TributeMaker Email Setup")
    print("=" * 40)
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return False
    
    print("\n📧 Email Provider Setup")
    print("Choose your email provider:")
    print("1. Gmail (Recommended)")
    print("2. Outlook/Hotmail")
    print("3. Yahoo Mail")
    print("4. Custom SMTP")
    print("5. Skip email setup (Development mode)")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        return setup_gmail()
    elif choice == "2":
        return setup_outlook()
    elif choice == "3":
        return setup_yahoo()
    elif choice == "4":
        return setup_custom()
    elif choice == "5":
        return setup_development_mode()
    else:
        print("❌ Invalid choice. Please run the script again.")
        return False

def setup_gmail():
    """Set up Gmail configuration"""
    print("\n📧 Gmail Setup")
    print("=" * 20)
    
    print("To use Gmail, you need to:")
    print("1. Enable 2-Factor Authentication on your Google account")
    print("2. Generate an App Password (not your regular password)")
    print("3. Use the 16-character App Password")
    print("\n🔗 App Password setup: https://myaccount.google.com/apppasswords")
    
    email = input("\nEnter your Gmail address: ").strip()
    if not email.endswith('@gmail.com'):
        print("⚠️  Warning: This doesn't look like a Gmail address")
    
    password = input("Enter your Gmail App Password (16 characters): ").strip()
    if len(password) != 16:
        print("⚠️  Warning: Gmail App Passwords are usually 16 characters")
    
    env_content = f"""# TributeMaker Email Configuration
# Gmail SMTP settings
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Your Gmail credentials
MAIL_USERNAME={email}
MAIL_PASSWORD={password}

# Application settings
SECRET_KEY=tribute-maker-secret-key-2024-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production
DATABASE_URL=sqlite:///tributemaker.db

# Email verification settings
DEVELOPMENT_MODE=false
EMAIL_VERIFICATION_ENABLED=true
"""
    
    return save_env_file(env_content)

def setup_outlook():
    """Set up Outlook configuration"""
    print("\n📧 Outlook/Hotmail Setup")
    print("=" * 25)
    
    email = input("Enter your Outlook/Hotmail address: ").strip()
    password = input("Enter your password: ").strip()
    
    env_content = f"""# TributeMaker Email Configuration
# Outlook SMTP settings
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Your Outlook credentials
MAIL_USERNAME={email}
MAIL_PASSWORD={password}

# Application settings
SECRET_KEY=tribute-maker-secret-key-2024-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production
DATABASE_URL=sqlite:///tributemaker.db

# Email verification settings
DEVELOPMENT_MODE=false
EMAIL_VERIFICATION_ENABLED=true
"""
    
    return save_env_file(env_content)

def setup_yahoo():
    """Set up Yahoo configuration"""
    print("\n📧 Yahoo Mail Setup")
    print("=" * 18)
    
    print("For Yahoo Mail, you may need to:")
    print("1. Enable 2-Factor Authentication")
    print("2. Generate an App Password")
    
    email = input("\nEnter your Yahoo email address: ").strip()
    password = input("Enter your Yahoo password/app password: ").strip()
    
    env_content = f"""# TributeMaker Email Configuration
# Yahoo SMTP settings
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Your Yahoo credentials
MAIL_USERNAME={email}
MAIL_PASSWORD={password}

# Application settings
SECRET_KEY=tribute-maker-secret-key-2024-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production
DATABASE_URL=sqlite:///tributemaker.db

# Email verification settings
DEVELOPMENT_MODE=false
EMAIL_VERIFICATION_ENABLED=true
"""
    
    return save_env_file(env_content)

def setup_custom():
    """Set up custom SMTP configuration"""
    print("\n📧 Custom SMTP Setup")
    print("=" * 20)
    
    server = input("Enter SMTP server (e.g., smtp.example.com): ").strip()
    port = input("Enter SMTP port (usually 587 or 465): ").strip()
    use_tls = input("Use TLS? (y/N): ").strip().lower() == 'y'
    use_ssl = input("Use SSL? (y/N): ").strip().lower() == 'y'
    email = input("Enter your email address: ").strip()
    password = input("Enter your password: ").strip()
    
    env_content = f"""# TributeMaker Email Configuration
# Custom SMTP settings
MAIL_SERVER={server}
MAIL_PORT={port}
MAIL_USE_TLS={str(use_tls).lower()}
MAIL_USE_SSL={str(use_ssl).lower()}

# Your email credentials
MAIL_USERNAME={email}
MAIL_PASSWORD={password}

# Application settings
SECRET_KEY=tribute-maker-secret-key-2024-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production
DATABASE_URL=sqlite:///tributemaker.db

# Email verification settings
DEVELOPMENT_MODE=false
EMAIL_VERIFICATION_ENABLED=true
"""
    
    return save_env_file(env_content)

def setup_development_mode():
    """Set up development mode without email"""
    print("\n🔧 Development Mode Setup")
    print("=" * 25)
    
    print("Setting up development mode without email verification.")
    print("Users will be automatically verified when they register.")
    
    env_content = """# TributeMaker Email Configuration
# Development mode - no email required
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=
MAIL_PASSWORD=

# Application settings
SECRET_KEY=tribute-maker-secret-key-2024-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production
DATABASE_URL=sqlite:///tributemaker.db

# Development mode settings
DEVELOPMENT_MODE=true
EMAIL_VERIFICATION_ENABLED=false
"""
    
    return save_env_file(env_content)

def save_env_file(content):
    """Save .env file and test configuration"""
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("\n✅ .env file created successfully!")
        
        # Test the configuration
        print("\n🧪 Testing email configuration...")
        email_service = EmailService()
        
        if email_service.is_configured():
            success, message = email_service.test_connection()
            if success:
                print("✅ Email configuration test successful!")
                print("📧 Email verification is ready to use.")
                return True
            else:
                print(f"❌ Email configuration test failed: {message}")
                print("\n🔧 Please check your credentials and try again.")
                print("You can edit the .env file manually or run this script again.")
                return False
        else:
            if email_service.config['development_mode']:
                print("✅ Development mode configured successfully!")
                print("📧 Email verification is disabled - users will be auto-verified.")
                return True
            else:
                print("❌ Email configuration incomplete.")
                return False
                
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_existing_config():
    """Test existing email configuration"""
    print("🧪 Testing existing email configuration...")
    
    email_service = EmailService()
    
    print(f"📧 Email configured: {email_service.is_configured()}")
    print(f"📧 Email enabled: {email_service.is_enabled()}")
    print(f"🔧 Development mode: {email_service.config['development_mode']}")
    
    if email_service.is_configured():
        print(f"📧 SMTP Server: {email_service.config['smtp_server']}:{email_service.config['smtp_port']}")
        print(f"📧 Username: {email_service.config['username']}")
        print(f"🔐 TLS: {email_service.config['use_tls']}, SSL: {email_service.config['use_ssl']}")
        
        success, message = email_service.test_connection()
        if success:
            print("✅ Email configuration is working correctly!")
            return True
        else:
            print(f"❌ Email test failed: {message}")
            return False
    else:
        if email_service.config['development_mode']:
            print("✅ Development mode - email verification disabled")
            return True
        else:
            print("❌ Email not configured")
            return False

def main():
    """Main setup function"""
    print("🚀 TributeMaker Email Setup")
    print("=" * 30)
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("📁 Found existing .env file")
        choice = input("Do you want to (t)est existing config or (r)econfigure? (t/r): ").strip().lower()
        
        if choice == 't':
            test_existing_config()
            return
        elif choice == 'r':
            create_env_file()
            return
        else:
            print("Testing existing configuration...")
            test_existing_config()
            return
    else:
        print("📁 No .env file found. Let's create one!")
        create_env_file()

if __name__ == "__main__":
    main() 