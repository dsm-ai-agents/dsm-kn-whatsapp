#!/usr/bin/env python3
"""
WhatsApp AI Chatbot - Legacy Entry Point
========================================
This file has been refactored into modular components with organized folder structure.
This script now simply redirects to the new structured application.

For the new structured layout, see:
- app.py (main application)
- src/ (organized source code)
- docs/REFACTORING_GUIDE.md (documentation)

Author: Rian Infotech
Version: 2.2 (Refactored & Structured)
"""

import warnings
import sys

def main():
    """Main entry point that redirects to the refactored application."""
    
    print("=" * 70)
    print("🏗️  STRUCTURED & REFACTORED APPLICATION")
    print("=" * 70)
    print("This application has been refactored into modular components")
    print("with a clean, organized folder structure.")
    print("")
    print("📁 Project Structure:")
    print("  📂 src/")
    print("    ├── 📂 config/          - Configuration & settings")
    print("    │   ├── config.py       - Environment & app config")
    print("    │   └── persona_manager.py - Bot personality")
    print("    ├── 📂 core/            - Core business logic")
    print("    │   ├── conversation_manager.py - Chat history")
    print("    │   └── supabase_client.py - Database operations")
    print("    ├── 📂 handlers/        - Message & API handlers")
    print("    │   ├── ai_handler.py   - OpenAI integration")
    print("    │   ├── whatsapp_handler.py - WhatsApp API")
    print("    │   └── message_processor.py - Message processing")
    print("    ├── 📂 api/             - REST API endpoints")
    print("    │   └── api_routes.py   - All API routes")
    print("    └── 📂 utils/           - Utility functions")
    print("        └── bulk_messaging.py - Bulk operations")
    print("")
    print("  📂 docs/                 - Documentation")
    print("  📂 backup/               - Backup files")
    print("  📂 static/               - Web assets")
    print("  📂 templates/            - HTML templates")
    print("")
    print("🚀 Entry Points:")
    print("  • app.py              - Main structured application")
    print("  • script.py           - This legacy redirect")
    print("")
    print("📖 Documentation:")
    print("  • docs/REFACTORING_GUIDE.md - Complete refactoring guide")
    print("")
    print("=" * 70)
    
    # Ask user if they want to proceed with the new app
    try:
        response = input("Do you want to run the new structured application? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            print("\n🚀 Starting structured application...")
            # Import and run the new application
            from app import app, logger, PERSONA_NAME
            from src.handlers.ai_handler import is_openai_configured
            from src.handlers.whatsapp_handler import is_wasender_configured
            
            logger.info(f"Starting {PERSONA_NAME} WhatsApp Bot...")
            logger.info(f"OpenAI configured: {is_openai_configured()}")
            logger.info(f"WaSender configured: {is_wasender_configured()}")
            
            # Run Flask app
            app.run(debug=True, port=5001, host='0.0.0.0')
        else:
            print("\n✋ Exiting. Use 'python3 app.py' to run the structured application directly.")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please run 'python3 app.py' directly.")
        sys.exit(1)


if __name__ == '__main__':
    main() 