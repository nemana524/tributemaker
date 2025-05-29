#!/usr/bin/env python3
"""
Fix Email Timeout Issues
Provides solutions for SMTP connection timeouts
"""

import os
import socket
import time
from email_service import email_service

def test_network_connectivity():
    """Test basic network connectivity to common SMTP servers"""
    print("🔍 Testing Network Connectivity")
    print("=" * 40)
    
    smtp_servers = [
        ("Gmail", "smtp.gmail.com", 587),
        ("Gmail SSL", "smtp.gmail.com", 465),
        ("Outlook", "smtp-mail.outlook.com", 587),
        ("Yahoo", "smtp.mail.yahoo.com", 587),
    ]
    
    working_servers = []
    
    for name, server, port in smtp_servers:
        try:
            print(f"Testing {name} ({server}:{port})...", end=" ")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            result = sock.connect_ex((server, port))
            sock.close()
            
            if result == 0:
                print("✅ Connected")
                working_servers.append((name, server, port))
            else:
                print("❌ Failed")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return working_servers

def create_development_env():
    """Create a development mode .env file"""
    print("\n🔧 Creating Development Mode Configuration")
    print("=" * 50)
    
    env_content = """# TributeMaker Email Configuration - Development Mode
# This configuration disables email verification for development

# Email settings (disabled)
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=
MAIL_PASSWORD=

# Application settings
SECRET_KEY=tribute-maker-secret-key-2024-development
JWT_SECRET_KEY=jwt-secret-string-development
DATABASE_URL=sqlite:///tributemaker.db

# Development mode settings (email verification disabled)
DEVELOPMENT_MODE=true
EMAIL_VERIFICATION_ENABLED=false
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ Development mode .env file created!")
        print("📧 Email verification is now DISABLED")
        print("👤 Users will be automatically verified when they register")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def create_working_email_env(server_info):
    """Create .env with working email server"""
    name, server, port = server_info
    
    print(f"\n📧 Setting up {name} configuration")
    print("=" * 40)
    
    email = input(f"Enter your {name} email address: ").strip()
    password = input(f"Enter your {name} password/app password: ").strip()
    
    use_ssl = port == 465
    use_tls = port == 587
    
    env_content = f"""# TributeMaker Email Configuration - {name}
MAIL_SERVER={server}
MAIL_PORT={port}
MAIL_USE_TLS={str(use_tls).lower()}
MAIL_USE_SSL={str(use_ssl).lower()}

# Your {name} credentials
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
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ {name} configuration saved!")
        return True
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def test_current_config():
    """Test the current email configuration"""
    print("🧪 Testing Current Configuration")
    print("=" * 40)
    
    print(f"📧 Email configured: {email_service.is_configured()}")
    print(f"📧 Email enabled: {email_service.is_enabled()}")
    print(f"🔧 Development mode: {email_service.config['development_mode']}")
    
    if email_service.is_configured():
        print(f"📧 Server: {email_service.config['smtp_server']}:{email_service.config['smtp_port']}")
        print(f"📧 Username: {email_service.config['username']}")
        
        print("\n🔌 Testing SMTP connection...")
        success, message = email_service.test_connection()
        
        if success:
            print("✅ Email configuration is working!")
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
    """Main function to fix email timeout issues"""
    print("🔧 TributeMaker Email Timeout Fix")
    print("=" * 50)
    
    print("The SMTP timeout error you're experiencing is common and usually caused by:")
    print("• Network/firewall blocking SMTP connections")
    print("• ISP restrictions on SMTP ports")
    print("• Corporate network policies")
    print("• Antivirus software blocking connections")
    
    print("\n🎯 Available Solutions:")
    print("1. Switch to Development Mode (Recommended for testing)")
    print("2. Test alternative SMTP servers")
    print("3. Try current configuration again")
    print("4. Exit")
    
    choice = input("\nChoose an option (1-4): ").strip()
    
    if choice == "1":
        # Development mode
        if create_development_env():
            print("\n✅ Development mode configured successfully!")
            print("🚀 You can now run your app without email issues:")
            print("   python app.py")
            print("\n👤 Users will be automatically verified when they register")
            print("📧 No email setup required for development")
            
            # Test the new configuration
            print("\n🧪 Testing new configuration...")
            # Reload email service
            email_service.config = email_service._load_config()
            test_current_config()
    
    elif choice == "2":
        # Test alternative servers
        working_servers = test_network_connectivity()
        
        if working_servers:
            print(f"\n✅ Found {len(working_servers)} working SMTP server(s)!")
            print("Choose a server to configure:")
            
            for i, (name, server, port) in enumerate(working_servers, 1):
                print(f"{i}. {name} ({server}:{port})")
            
            try:
                server_choice = int(input(f"\nChoose server (1-{len(working_servers)}): ")) - 1
                if 0 <= server_choice < len(working_servers):
                    selected_server = working_servers[server_choice]
                    
                    if create_working_email_env(selected_server):
                        print("\n🧪 Testing new configuration...")
                        # Reload email service
                        email_service.config = email_service._load_config()
                        test_current_config()
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Invalid input")
        else:
            print("\n❌ No SMTP servers are accessible from your network")
            print("🔧 Recommended: Switch to development mode")
            
            if input("\nSwitch to development mode? (y/N): ").lower() == 'y':
                create_development_env()
    
    elif choice == "3":
        # Test current configuration
        test_current_config()
    
    elif choice == "4":
        print("👋 Goodbye!")
        return
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 