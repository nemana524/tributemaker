#!/usr/bin/env python3
"""
Fix .env file App Password format
"""

import os
import re

def fix_env_password():
    """Help user fix the App Password in .env file"""
    
    print("🔧 App Password Format Fixer")
    print("=" * 40)
    
    # Read current .env file
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find current password
        password_match = re.search(r'MAIL_PASSWORD=(.+)', content)
        if password_match:
            current_password = password_match.group(1).strip()
            print(f"Current password: '{current_password}'")
            print(f"Length: {len(current_password)} characters")
            print(f"Contains spaces: {'Yes' if ' ' in current_password else 'No'}")
            
            # Show what it should look like
            cleaned_password = current_password.replace(' ', '').replace('-', '')
            print(f"\nCleaned password (spaces removed): '{cleaned_password}'")
            print(f"Cleaned length: {len(cleaned_password)} characters")
            
            if len(cleaned_password) == 16:
                print("✅ After removing spaces, length is correct!")
                
                # Ask user if they want to auto-fix
                print(f"\n🔧 Would you like me to update your .env file?")
                print(f"Current: MAIL_PASSWORD={current_password}")
                print(f"Fixed:   MAIL_PASSWORD={cleaned_password}")
                
                response = input("\nType 'yes' to auto-fix, or 'no' to fix manually: ").lower().strip()
                
                if response == 'yes':
                    # Update the file
                    new_content = content.replace(f'MAIL_PASSWORD={current_password}', f'MAIL_PASSWORD={cleaned_password}')
                    
                    with open('.env', 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print("✅ .env file updated successfully!")
                    print("🧪 Run 'python diagnose_email.py' to test the fix")
                    return True
                else:
                    print("\n📝 Manual fix instructions:")
                    print("1. Open .env file in a text editor")
                    print(f"2. Find: MAIL_PASSWORD={current_password}")
                    print(f"3. Replace with: MAIL_PASSWORD={cleaned_password}")
                    print("4. Save the file")
                    return False
            else:
                print(f"❌ Even after removing spaces, length is {len(cleaned_password)} (should be 16)")
                print("\n🔑 You need to generate a new Gmail App Password:")
                print("1. Go to https://myaccount.google.com/")
                print("2. Security → 2-Step Verification → App passwords")
                print("3. Generate new password for 'Mail'")
                print("4. Copy the 16-character password")
                print("5. Update your .env file")
                return False
        else:
            print("❌ Could not find MAIL_PASSWORD in .env file")
            return False
            
    except FileNotFoundError:
        print("❌ .env file not found")
        return False
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def show_gmail_instructions():
    """Show detailed Gmail App Password instructions"""
    print("\n" + "=" * 50)
    print("📧 HOW TO GET GMAIL APP PASSWORD")
    print("=" * 50)
    print("1. Go to: https://myaccount.google.com/")
    print("2. Click 'Security' in the left sidebar")
    print("3. Under 'Signing in to Google', click '2-Step Verification'")
    print("4. If not enabled, set up 2-Step Verification first")
    print("5. Scroll down and click 'App passwords'")
    print("6. Select 'Mail' from the dropdown")
    print("7. Click 'Generate'")
    print("8. Copy the 16-character password (might show as: abcd 1234 efgh 5678)")
    print("9. Remove spaces: abcd1234efgh5678")
    print("10. Use this in your .env file")

if __name__ == "__main__":
    success = fix_env_password()
    
    if not success:
        show_gmail_instructions()
    
    print(f"\n🧪 After fixing, test with: python diagnose_email.py") 