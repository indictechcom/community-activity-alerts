from flask import Blueprint, jsonify,redirect, url_for

def create_auth_blueprint(mwoauth):
    auth_bp = Blueprint('auth', __name__)

    
    @auth_bp.route('/login')
    def login():
        return redirect(url_for('mwoauth.login'))

    @auth_bp.route('/logout')
    def logout():
        return redirect(url_for('mwoauth.logout'))

    @auth_bp.route('/user')
    def get_user():
        print("Fetching user info")
        username = mwoauth.get_current_user(True)  # use the shared instance
        print(f"Current user: {username}")
        if username:
            return jsonify({"isAuthenticated": True, "username": username})
        else:
            return jsonify({"error": "Not authenticated"}), 401

    return auth_bp
