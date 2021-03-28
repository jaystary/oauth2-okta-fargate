from flask import Flask, render_template, url_for, redirect
from flask_oidc import OpenIDConnect
from flask_talisman import Talisman
from flask_cors import CORS

csp = {
 'default-src': [
        '\'self\'',
        'maxcdn.bootstrapcdn.com'
    ]
}
app = Flask(__name__)
Talisman(app, force_https_permanent='true', force_https='true',content_security_policy=csp)
CORS(app)


app.config.update({
    'SECRET_KEY': 'SomethingNotEntirelySecret',
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_SCOPES': ["openid", "profile", "email"],
    'OIDC_CALLBACK_ROUTE': '/authorization-code/callback',
    'OVERWRITE_REDIRECT_URI' : 'https://login.jaysbox.io/authorization-code/callback',
    'PREFERRED_URL_SCHEME' : 'https'
    
})

oidc = OpenIDConnect(app)


@app.route("/")
def home():
    return render_template("home.html", oidc=oidc)


@app.route("/login")
@oidc.require_login
def login():
    return redirect(url_for("profile"))


@app.route("/profile")
@oidc.require_login
def profile():
    info = oidc.user_getinfo(["sub", "name", "email"])

    return render_template("profile.html", profile=info, oidc=oidc)


@app.route("/logout", methods=["POST"])
def logout():
    oidc.logout()
    return redirect(url_for("home"))

@app.route("/health")
def hhealth():
    status_code = flask.Response(status=200)
    return status_code




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
