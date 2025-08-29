from flask import Flask, render_template_string, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
app.secret_key = "super-secret-key"  # change to something random!

# Firebase setup
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Hardcoded users (username: password)
USERS = {
    "shourik": "pass1",
    "ethan": "pass2",
    "luca": "pass3",
    "richard": "pass4",
    "henok": "pass5",
    "anish": "pass6"
}

# HTML templates
LOGIN_HTML = """
<!doctype html>
<html>
<head><title>Login</title></head>
<body>
  <h1>Login</h1>
  <form method="post" action="/login">
    Username: <input type="text" name="username"><br>
    Password: <input type="password" name="password"><br>
    <input type="submit" value="Login">
  </form>
  {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
</body>
</html>
"""

BID_HTML = """
<!doctype html>
<html>
<head><title>Bid Form</title></head>
<body>
  <h1>Welcome {{ user }}!</h1>
  <form method="post" action="/">
    College: <input type="text" name="college"><br>
    Bid Number: <input type="text" name="bid_number"><br>
    <input type="submit" value="Submit">
  </form>

  <form method="post" action="/clear" style="margin-top:20px;">
    <input type="submit" value="Clear My Bids" style="background:red;color:white;">
  </form>

  <h2>Your Entries</h2>
  <ul>
    {% for entry in entries %}
      <li>{{ entry["college"] }} - Bid: {{ entry["bid_number"] }}</li>
    {% endfor %}
  </ul>

  <a href="/logout">Logout</a>
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect(url_for("index"))
        else:
            return render_template_string(LOGIN_HTML, error="Invalid credentials")
    return render_template_string(LOGIN_HTML, error=None)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    collection_ref = db.collection("bids")

    if request.method == "POST":
        data = {
            "user": user,
            "college": request.form["college"],
            "bid_number": request.form["bid_number"]
        }
        collection_ref.add(data)
        return redirect(url_for("index"))

    # Get only this user's entries
    docs = collection_ref.where("user", "==", user).stream()
    entries = [doc.to_dict() for doc in docs]

    return render_template_string(BID_HTML, user=user, entries=entries)

@app.route("/clear", methods=["POST"])
def clear():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]

    collection_ref = db.collection("bids")
    docs = collection_ref.where("user", "==", user).stream()
    for doc in docs:
        doc.reference.delete()

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
