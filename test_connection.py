#!/usr/bin/env python3
"""
Simple database connection test script.
"""
import os
import sys
from pathlib import Path

def test_basic_connection():
    """Test basic database connection without SQLAlchemy."""
    print("Testing basic database connection...")
    
    try:
        import psycopg2
        from config.settings import DB_CONFIG
        
        print(f"Connecting to: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"Database: {DB_CONFIG['database']}")
        print(f"User: {DB_CONFIG['user']}")
        
        # Test direct connection
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Basic connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection."""
    print("\nTesting SQLAlchemy connection...")
    
    try:
        from database.connection import db_manager
        
        if db_manager.test_connection():
            print("✓ SQLAlchemy connection successful!")
            return True
        else:
            print("✗ SQLAlchemy connection failed!")
            return False
            
    except Exception as e:
        print(f"✗ SQLAlchemy connection error: {e}")
        return False

def test_database_creation():
    """Test database table creation."""
    print("\nTesting database table creation...")
    
    try:
        from database.operations import init_database
        init_database()
        print("✓ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"✗ Database table creation failed: {e}")
        return False

def main():
    """Main test function."""
    print("Database Connection Test")
    print("=" * 40)
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("✗ .env file not found!")
        print("Please run 'python setup_database.py' first to create the .env file.")
        return
    
    # Test basic connection
    if not test_basic_connection():
        print("\nBasic connection failed. Please check:")
        print("1. PostgreSQL is running")
        print("2. Database credentials in .env file")
        print("3. Database exists")
        return
    
    # Test SQLAlchemy connection
    if not test_sqlalchemy_connection():
        print("\nSQLAlchemy connection failed. This might be a version compatibility issue.")
        return
    
    # Test table creation
    if not test_database_creation():
        print("\nTable creation failed.")
        return
    
    print("\n" + "=" * 40)
    print("✓ All database tests passed!")
    print("Your database is ready for use.")
    print("=" * 40)

if __name__ == "__main__":
    main()
