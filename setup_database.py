
#!/usr/bin/env python3
"""
Database Setup Script for Indian Stock Market Backtesting System

This script helps you set up the database connection and test it.
"""
import os
import sys
import getpass
from pathlib import Path

def create_env_file():
    """Create a .env file with database configuration."""
    print("Database Configuration Setup")
    print("=" * 40)
    
    # Get database configuration from user
    print("\nPlease provide your PostgreSQL database configuration:")
    
    host = input("Database Host (default: localhost): ").strip() or "localhost"
    port = input("Database Port (default: 5432): ").strip() or "5432"
    database = input("Database Name (default: stock_backtesting): ").strip() or "stock_backtesting"
    user = input("Database User (default: postgres): ").strip() or "postgres"
    password = getpass.getpass("Database Password: ").strip()
    
    # Validate port
    try:
        port_int = int(port)
        if port_int <= 0 or port_int > 65535:
            print("Error: Port must be between 1 and 65535")
            return False
    except ValueError:
        print("Error: Port must be a valid number")
        return False
    
    # Create .env file content
    env_content = f"""# Database Configuration
DB_HOST={host}
DB_PORT={port}
DB_NAME={database}
DB_USER={user}
DB_PASSWORD={password}

# API Configuration
NSEPY_TIMEOUT=30
YAHOO_TIMEOUT=30

# Default Settings
DEFAULT_START_DATE=2020-01-01
DEFAULT_END_DATE=2023-12-31
DEFAULT_SHORT_WINDOW=20
DEFAULT_LONG_WINDOW=50

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=backtesting.log
"""
    
    # Write .env file
    env_file = Path(".env")
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"\n✓ .env file created successfully at {env_file.absolute()}")
        return True
    except Exception as e:
        print(f"Error creating .env file: {e}")
        return False

def test_database_connection():
    """Test the database connection."""
    print("\nTesting Database Connection...")
    print("-" * 30)
    
    try:
        # Import after .env file is created
        from config.settings import DB_CONFIG
        from config.database import DATABASE_URL
        
        print(f"✓ Database configuration loaded successfully")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  Database: {DB_CONFIG['database']}")
        print(f"  User: {DB_CONFIG['user']}")
        
        # Test connection
        from database.connection import db_manager
        
        if db_manager.test_connection():
            print("✓ Database connection successful!")
            return True
        else:
            print("✗ Database connection failed!")
            return False
            
    except Exception as e:
        print(f"✗ Error testing database connection: {e}")
        return False

def create_database():
    """Create the database if it doesn't exist."""
    print("\nCreating Database Tables...")
    print("-" * 30)
    
    try:
        from database.operations import init_database
        init_database()
        print("✓ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"✗ Error creating database tables: {e}")
        return False

def main():
    """Main setup function."""
    print("Indian Stock Market Backtesting System - Database Setup")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file already exists")
        overwrite = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Using existing .env file")
        else:
            if not create_env_file():
                return
    else:
        if not create_env_file():
            return
    
    # Test connection
    if not test_database_connection():
        print("\nDatabase connection failed. Please check your configuration:")
        print("1. Make sure PostgreSQL is running")
        print("2. Verify the database credentials in .env file")
        print("3. Ensure the database exists (or create it manually)")
        print("4. Check if the user has proper permissions")
        return
    
    # Create tables
    if not create_database():
        print("\nFailed to create database tables.")
        return
    
    print("\n" + "=" * 60)
    print("✓ Database setup completed successfully!")
    print("You can now run the backtesting system.")
    print("=" * 60)

if __name__ == "__main__":
    main()
