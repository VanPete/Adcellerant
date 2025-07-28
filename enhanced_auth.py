#!/usr/bin/env python3
"""
Enhanced Authentication Functions for Adcellerant Social Caption Generator
"""

import streamlit as st
from datetime import datetime
from auth_config import verify_simple_password, get_access_level, create_session_token, is_session_valid

def enhanced_password_check():
    """Enhanced password check with session management and access levels."""
    
    def password_entered():
        """Process password input."""
        entered_password = st.session_state["app_password"]
        
        if verify_simple_password(entered_password):
            # Valid password
            st.session_state["authenticated"] = True
            st.session_state["access_level"] = get_access_level(entered_password)
            st.session_state["session_token"] = create_session_token()
            st.session_state["session_start"] = datetime.now().isoformat()
            st.session_state["login_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            del st.session_state["app_password"]  # Don't store password
            st.success("✅ Authentication successful!")
            st.experimental_rerun()
        else:
            st.session_state["authenticated"] = False
            st.session_state["auth_attempts"] = st.session_state.get("auth_attempts", 0) + 1

    # Check if already authenticated and session is valid
    if st.session_state.get("authenticated") and st.session_state.get("session_start"):
        if is_session_valid(st.session_state["session_start"]):
            return True
        else:
            # Session expired
            st.warning("🕐 Your session has expired. Please login again.")
            for key in ["authenticated", "access_level", "session_token", "session_start", "login_time"]:
                if key in st.session_state:
                    del st.session_state[key]

    # Show login form
    show_login_form(password_entered)
    return False

def show_login_form(password_callback):
    """Display the login form."""
    st.markdown("## 🔐 Adcellerant Social Caption Generator")
    st.markdown("### Access Required")
    
    # Logo or branding area
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("🚀 **AI-Powered Social Media Caption Generator**\n\nPlease enter your access password to continue.")
    
    # Password input
    st.text_input(
        "🔑 Access Password:",
        type="password",
        on_change=password_callback,
        key="app_password",
        help="Enter your provided access password",
        placeholder="Enter password..."
    )
    
    # Show authentication attempts
    if st.session_state.get("auth_attempts", 0) > 0:
        attempts = st.session_state["auth_attempts"]
        if attempts >= 3:
            st.error(f"❌ Authentication failed {attempts} times. Please contact Adcellerant for assistance.")
            st.info("💡 **Need Help?** Contact your administrator for the correct password.")
        else:
            st.error(f"❌ Incorrect password. Attempt {attempts}/3")
    
    # Help section
    with st.expander("ℹ️ Need Access?"):
        st.markdown("""
        **To get access to this application:**
        
        1. 📞 Contact Adcellerant support
        2. 📧 Email your administrator
        3. 💬 Request access through your team lead
        
        **Demo Access Available:**
        - Contact us for a demonstration password
        - Limited features available in demo mode
        """)
    
    # Footer
    st.markdown("---")
    st.caption("🔒 Secure access • 🤖 AI-powered • 📱 Social media optimized")

def show_session_info():
    """Show session information in sidebar."""
    if st.session_state.get("authenticated"):
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Session Info")
            
            access_level = st.session_state.get("access_level", "standard")
            login_time = st.session_state.get("login_time", "Unknown")
            
            st.write(f"**Access Level:** {access_level.title()}")
            st.write(f"**Login Time:** {login_time}")
            
            # Access level indicator
            if access_level == "admin":
                st.success("🔑 Admin Access")
            elif access_level == "demo":
                st.warning("🎯 Demo Mode")
            else:
                st.info("✅ Standard Access")
            
            # Logout button
            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                logout_user()

def logout_user():
    """Handle user logout."""
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("👋 You have been logged out successfully.")
    st.experimental_rerun()

def require_access_level(required_level):
    """Check if user has required access level."""
    current_level = st.session_state.get("access_level", "")
    
    level_hierarchy = {
        "demo": 1,
        "standard": 2, 
        "admin": 3
    }
    
    required_rank = level_hierarchy.get(required_level, 999)
    current_rank = level_hierarchy.get(current_level, 0)
    
    return current_rank >= required_rank

def demo_mode_warning():
    """Show warning for demo mode limitations."""
    if st.session_state.get("access_level") == "demo":
        st.warning("🎯 **Demo Mode** - Some features may be limited. Contact us for full access!")
        return True
    return False
