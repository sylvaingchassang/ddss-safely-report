from flask_login import LoginManager

from safely_report.models import User

login_manager = LoginManager()
login_manager.login_view = "auth.index"


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()
