#!/usr/bin/env python3
"""
Authentication module for the Social Post Generator application.
"""

import streamlit as st
from config.constants import APP_PASSWORD
from config.settings import SESSION_KEYS
from utils.helpers import clear_session_keys

def check_password() -> bool:
    """Returns True if the user has entered the correct password.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == APP_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        _show_login_form(password_entered)
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        _show_login_error(password_entered)
        return False
    else:
        # Password correct
        return True

def show_logout_option():
    """Show logout option in sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔓 Session")
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            logout_user()

def logout_user():
    """Clear authentication-related session state and logout."""
    # Clear only authentication-related session state
    # Company directory and other persistent data remain intact
    cleared_count = clear_session_keys(SESSION_KEYS["AUTH_KEYS"])
    
    if cleared_count > 0:
        st.success(f"✅ Logged out successfully! ({cleared_count} session items cleared)")
    
    st.rerun()

def _show_login_form(password_callback):
    """Show the login form for first-time access."""
    st.markdown("## 🔐 Access Required")
    st.info("This application requires a password to access. Please contact Maddie Stitt for access.")
    st.text_input(
        "Password", 
        type="password", 
        on_change=password_callback, 
        key="password",
        help="Enter the application password"
    )
    
    # Add some styling
    st.markdown("""
    <style>
    .password-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 50vh;
    }
    </style>
    """, unsafe_allow_html=True)

def _show_login_error(password_callback):
    """Show the login form with error message."""
    st.markdown("## 🔐 Access Required")
    st.error("❌ Incorrect password. Please try again.")
    st.info("This application requires a password to access. Please contact Maddie Stitt for access.")
    st.text_input(
        "Password", 
        type="password", 
        on_change=password_callback, 
        key="password",
        help="Enter the application password"
    )

def is_authenticated() -> bool:
    """Check if user is currently authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    return st.session_state.get("password_correct", False)
