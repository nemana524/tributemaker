#!/usr/bin/env python3
"""
Alternative Email Solutions for TributeMaker
Provides different ways to handle email verification in local development
"""

import os
import json
import secrets
from datetime import datetime

def create_email_simulation():
    """Simulate email sending by creating local files"""
    print("📧 Email Simulation Mode")
    print("=" * 40)
    
    print("This mode simulates email sending by creating local files.")
    print("Perfect for testing the email flow without actual email sending.")
    print()
    
    # Create emails directory
    os.makedirs('simulated_emails', exist_ok=True)
    
    # Generate test verification token
    verification_token = secrets.token_urlsafe(32)
    recipient = input("Enter email address to simulate sending to: ").strip()
    
    if not recipient:
        print("❌ Email address required")
        return
    
    # Create email content
    email_content = {
        "to": recipient,
        "subject": "🎬 Verify Your TributeMaker Account",
        "verification_token": verification_token,
        "verification_url": f"http://localhost:5000/api/auth/verify/{verification_token}",
        "timestamp": datetime.now().isoformat(),
        "type": "verification"
    }
    
    # Save to file
    filename = f"simulated_emails/verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(email_content, f, indent=2)
    
    print(f"✅ Email simulated and saved to: {filename}")
    print(f"📧 Recipient: {recipient}")
    print(f"🔗 Verification URL: {email_content['verification_url']}")
    print()
    print("💡 To verify the user, visit the verification URL in your browser")
    print("   or use the verification token in your app")

def create_webhook_solution():
    """Create a webhook-based email solution"""
    print("🔗 Webhook Email Solution")
    print("=" * 40)
    
    print("This creates a webhook endpoint that captures email sending requests.")
    print("Useful for testing email flows without actual email delivery.")
    print()
    
    webhook_code = '''
# Add this to your app.py for webhook-based email testing

@app.route('/api/webhook/email-sent', methods=['POST'])
def webhook_email_sent():
    """Webhook endpoint for email testing"""
    data = request.get_json()
    
    # Log the email that would have been sent
    print(f"📧 EMAIL WEBHOOK: {data.get('type', 'unknown')} email")
    print(f"   To: {data.get('to')}")
    print(f"   Subject: {data.get('subject')}")
    print(f"   Token: {data.get('verification_token')}")
    print(f"   URL: {data.get('verification_url')}")
    
    # Save to file for testing
    os.makedirs('webhook_emails', exist_ok=True)
    filename = f"webhook_emails/{data.get('type', 'email')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return jsonify({"status": "received", "message": "Email webhook processed"})

# Modify your email service to use webhook in development
def send_verification_email_webhook(user_email, verification_token, base_url):
    """Send verification email via webhook for testing"""
    webhook_data = {
        "type": "verification",
        "to": user_email,
        "subject": "🎬 Verify Your TributeMaker Account",
        "verification_token": verification_token,
        "verification_url": f"{base_url}api/auth/verify/{verification_token}",
        "timestamp": datetime.now().isoformat()
    }
    
    # In development, just log and save
    print(f"📧 WEBHOOK EMAIL: Verification email for {user_email}")
    print(f"🔗 Verification URL: {webhook_data['verification_url']}")
    
    # Save to file
    os.makedirs('webhook_emails', exist_ok=True)
    filename = f"webhook_emails/verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(webhook_data, f, indent=2)
    
    return True, "Email sent via webhook"
'''
    
    print("📝 Webhook code generated!")
    print("Add the above code to your app.py to enable webhook email testing.")
    
    # Save webhook code to file
    with open('webhook_email_solution.py', 'w') as f:
        f.write(webhook_code)
    
    print("✅ Webhook solution saved to: webhook_email_solution.py")

def create_console_email_solution():
    """Create a console-based email solution"""
    print("🖥️  Console Email Solution")
    print("=" * 40)
    
    print("This solution prints email content to the console.")
    print("Perfect for development when you just need to see the verification links.")
    print()
    
    console_code = '''
# Console Email Solution for TributeMaker
# Add this to your email_service.py

def send_verification_email_console(user_email, verification_token, base_url):
    """Send verification email to console for development"""
    
    verification_url = f"{base_url}api/auth/verify/{verification_token}"
    
    print("\\n" + "="*60)
    print("📧 VERIFICATION EMAIL (Console Mode)")
    print("="*60)
    print(f"To: {user_email}")
    print(f"Subject: 🎬 Verify Your TributeMaker Account")
    print(f"\\nVerification URL:")
    print(f"🔗 {verification_url}")
    print("\\nTo verify this user, copy the URL above and visit it in your browser.")
    print("="*60 + "\\n")
    
    # Also save to file for easy access
    os.makedirs('console_emails', exist_ok=True)
    filename = f"console_emails/verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w') as f:
        f.write(f"Verification Email\\n")
        f.write(f"To: {user_email}\\n")
        f.write(f"Token: {verification_token}\\n")
        f.write(f"URL: {verification_url}\\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\\n")
    
    return True, f"Verification email logged to console and saved to {filename}"

# Update your email_service.py to use console mode in development
def send_verification_email(user_email, verification_token, base_url):
    """Send verification email with fallback to console"""
    
    # Try normal email sending first
    if email_service.is_configured() and email_service.is_enabled():
        try:
            return email_service.send_verification_email(user_email, verification_token, base_url)
        except Exception as e:
            print(f"Email sending failed: {e}")
            print("Falling back to console mode...")
    
    # Fallback to console mode
    return send_verification_email_console(user_email, verification_token, base_url)
'''
    
    print("📝 Console email solution generated!")
    
    # Save console code to file
    with open('console_email_solution.py', 'w') as f:
        f.write(console_code)
    
    print("✅ Console solution saved to: console_email_solution.py")
    
    # Test console email
    print("\\n🧪 Testing Console Email...")
    recipient = input("Enter email address to test console email: ").strip()
    if recipient:
        verification_token = secrets.token_urlsafe(32)
        verification_url = f"http://localhost:5000/api/auth/verify/{verification_token}"
        
        print("\\n" + "="*60)
        print("📧 VERIFICATION EMAIL (Console Mode)")
        print("="*60)
        print(f"To: {recipient}")
        print(f"Subject: 🎬 Verify Your TributeMaker Account")
        print(f"\\nVerification URL:")
        print(f"🔗 {verification_url}")
        print("\\nTo verify this user, copy the URL above and visit it in your browser.")
        print("="*60 + "\\n")

def main():
    """Main function for email alternatives"""
    print("🔧 TributeMaker Email Alternatives")
    print("=" * 50)
    
    print("Since SMTP is blocked on your network, here are alternative solutions:")
    print()
    print("1. 📧 Email Simulation (Save emails as files)")
    print("2. 🔗 Webhook Solution (HTTP endpoint for email testing)")
    print("3. 🖥️  Console Solution (Print emails to terminal)")
    print("4. 📱 Network Solutions (Try different connection)")
    print("5. Exit")
    
    choice = input("\\nChoose option (1-5): ").strip()
    
    if choice == "1":
        create_email_simulation()
    elif choice == "2":
        create_webhook_solution()
    elif choice == "3":
        create_console_email_solution()
    elif choice == "4":
        print("📱 Network Solutions:")
        print("=" * 30)
        print("1. Try mobile hotspot from your phone")
        print("2. Use a different WiFi network")
        print("3. Use a VPN service")
        print("4. Try from a different location")
        print("5. Use cloud services (Heroku, Railway, etc.)")
        print()
        print("💡 The SMTP timeout suggests your ISP/network is blocking SMTP ports.")
        print("   This is common on residential and corporate networks.")
    elif choice == "5":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 