#!/usr/bin/env python3
"""
Authentication configuration for Adcellerant Social Caption Generator
"""

import hashlib
import os
from datetime import datetime, timedelta

# === User Configuration ===
# You can add multiple users here
AUTHORIZED_USERS = {
    "admin": {
        "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"
        "role": "admin",
        "access_level": "full"
    },
    "adcellerant": {
        "password_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  # "hello"
        "role": "user", 
        "access_level": "standard"
    }
}

# === Simple Password Options ===
SIMPLE_PASSWORDS = {
    "adcellerant2025": {"level": "standard"},
    "admin123": {"level": "admin"},
    "demo": {"level": "demo"}  # Limited features
}

def hash_password(password):
    """Create SHA256 hash of password."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username, password):
    """Verify username/password combination."""
    if username in AUTHORIZED_USERS:
        password_hash = hash_password(password)
        return AUTHORIZED_USERS[username]["password_hash"] == password_hash
    return False

def verify_simple_password(password):
    """Verify simple password (no username required)."""
    return password in SIMPLE_PASSWORDS

def get_access_level(identifier):
    """Get access level for user or password."""
    if identifier in AUTHORIZED_USERS:
        return AUTHORIZED_USERS[identifier]["access_level"]
    elif identifier in SIMPLE_PASSWORDS:
        return SIMPLE_PASSWORDS[identifier]["level"]
    return None

# === Session Management ===
def create_session_token():
    """Create a simple session token."""
    return hashlib.sha256(f"{datetime.now()}{os.urandom(16)}".encode()).hexdigest()[:16]

def is_session_valid(session_start, max_hours=24):
    """Check if session is still valid."""
    if not session_start:
        return False
    
    session_time = datetime.fromisoformat(session_start)
    return datetime.now() - session_time < timedelta(hours=max_hours)

# === Password Generation Helper ===
def generate_password_hash(password):
    """Helper function to generate password hashes for new users."""
    return hash_password(password)

# Example usage:
# print(f"Password hash for 'mypassword': {generate_password_hash('mypassword')}")
