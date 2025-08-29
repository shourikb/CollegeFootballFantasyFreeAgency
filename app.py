from flask import Flask, render_template_string, request, redirect
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("firebase-key.json")  # downloaded from Firebase
firebase_admin.initialize_app(cred)
db = firestore.client()

HTML_FORM = """
<!doctype html>
<html>
<head>
  <title>Bid Form</title>
</head>
<body>
  <h1>Enter Bid</h1>
  <form method="post" action="/">
    Name: <input type="text" name="name"><br>
    College: <input type="text" name="college"><br>
    Bid Number: <input type="text" name="bid_number"><br>
    <input type="submit" value="Submit">
  </form>

  <h2>All Entries</h2>
  <ul>
    {% for entry in entries %}
      <li>{{ entry["name"] }} ({{ entry["college"] }}) - Bid: {{ entry["bid_number"] }}</li>
    {% endfor %}
  </ul>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    collection_ref = db.collection("bids")

    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "college": request.form["college"],
            "bid_number": request.form["bid_number"]
        }
        collection_ref.add(data)
        return redirect("/")

    docs = collection_ref.stream()
    entries = [doc.to_dict() for doc in docs]

    return render_template_string(HTML_FORM, entries=entries)

if __name__ == "__main__":
    app.run(debug=True)
