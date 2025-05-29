#!/usr/bin/env python3
"""
Enable Console Email Mode for TributeMaker
Enables email verification with console fallback when SMTP fails
"""

import os
import shutil
from datetime import datetime

def backup_current_env():
    """Backup current .env file"""
    if os.path.exists('.env'):
        backup_name = f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        shutil.copy('.env', backup_name)
        print(f"✅ Current .env backed up as: {backup_name}")
        return backup_name
    return None

def create_console_email_env():
    """Create .env with email verification enabled and console fallback"""
    env_content = """# TributeMaker Email Configuration - Console Mode
# Email verification enabled with console fallback for SMTP failures

# Email settings (will fallback to console if SMTP fails)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Application settings
SECRET_KEY=tribute-maker-secret-key-2024-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production
DATABASE_URL=sqlite:///tributemaker.db

# Email verification settings (ENABLED with console fallback)
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

def main():
    """Enable console email mode"""
    print("📧 Enable Console Email Mode for TributeMaker")
    print("=" * 60)
    
    print("This mode enables email verification with automatic console fallback.")
    print("When SMTP fails (like your current network issue), verification")
    print("emails will be printed to the console instead.")
    print()
    
    print("✅ Benefits:")
    print("• Email verification is enabled")
    print("• Users get verification emails when SMTP works")
    print("• Console fallback when SMTP fails (like now)")
    print("• Verification URLs are printed to terminal")
    print("• Email content saved to files for testing")
    print()
    
    if input("Enable console email mode? (y/N): ").lower() != 'y':
        print("👋 No changes made")
        return
    
    # Backup current config
    backup_file = backup_current_env()
    
    # Create new .env file
    if create_console_email_env():
        print("\n✅ Console email mode enabled!")
        print("📧 Email verification is now ENABLED with console fallback")
        print()
        print("🎯 How it works:")
        print("1. When users register, the system tries to send email via SMTP")
        print("2. If SMTP fails (like your current network), it falls back to console")
        print("3. Verification URLs are printed to your terminal")
        print("4. You can copy the URL and verify users manually")
        print("5. Email content is also saved to 'console_emails/' folder")
        print()
        print("🚀 Test it now:")
        print("1. Start your Flask app: python app.py")
        print("2. Register a new user")
        print("3. Watch the console for verification URLs")
        print("4. Copy the URL to verify the user")
        
        if backup_file:
            print(f"\n💾 Your previous config is backed up as: {backup_file}")
    else:
        print("❌ Failed to enable console email mode")

if __name__ == "__main__":
    main() 