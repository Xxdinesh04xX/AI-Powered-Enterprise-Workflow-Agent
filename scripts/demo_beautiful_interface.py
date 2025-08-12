"""
Demo script for the beautiful AI-Powered Enterprise Workflow Agent interface.

This script demonstrates the beautiful web interface and its features.
"""

import webbrowser
import time
import requests
import json

def main():
    """Run the beautiful interface demo."""
    
    print("🎨 AI-Powered Enterprise Workflow Agent - Beautiful Interface Demo")
    print("=" * 70)
    
    # Check if server is running
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
        else:
            print("❌ Server is not responding properly")
            return
    except:
        print("❌ Server is not running. Please start it with: python scripts/start_api.py")
        return
    
    print("\n🌐 Opening beautiful web interface...")
    print("URL: http://127.0.0.1:8000")
    print("\n🎯 Features you can try:")
    print("  • Create new tasks with AI classification")
    print("  • Test the AI classification system")
    print("  • View real-time statistics")
    print("  • Generate comprehensive reports")
    print("  • Browse team information")
    print("  • Beautiful, modern design with animations")
    
    print("\n📱 The interface includes:")
    print("  • Gradient backgrounds and modern cards")
    print("  • Smooth animations and hover effects")
    print("  • Real-time data loading")
    print("  • Toast notifications")
    print("  • Responsive design for mobile/desktop")
    print("  • Beautiful icons and typography")
    
    print("\n🚀 Try these example tasks:")
    print("  1. 'The email server is down and users cannot send emails'")
    print("  2. 'We need to hire a new software developer for our team'")
    print("  3. 'Please review the vendor contracts expiring next month'")
    
    print("\n" + "=" * 70)
    print("🎉 Enjoy the beautiful AI-powered workflow automation!")
    
    # Open browser
    webbrowser.open('http://127.0.0.1:8000')

if __name__ == "__main__":
    main()
