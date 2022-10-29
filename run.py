import os
from flask import Flask, request, flash, redirect, render_template
import csv

app = Flask(__name__)
secret_key = os.urandom(12).hex()
app.secret_key = secret_key


def file_to_csv(data):
    with open("database.csv", "a", newline="") as database:
        name = data["name"]
        email = data["email"]
        subject = data["subject"]
        message = data["message"]
        csv_write = csv.writer(database)
        csv_write.writerow([name, email, subject, message])


@app.route("/")
def index():
    return render_template("/index.html")


@app.route("/submit", methods=["POST", "GET"])
def submit_form():
    if request.method == "POST":
        try:
            response = request.form.to_dict()
            file_to_csv(response)

        except:
            return "Unable to save to database."

        # flash()
        return f"Thank you, {response['name']}. I will be in touch shortly."

    else:
        return "Something went wrong."


#TODO: Determine why message is not appearing in the database
#TODO: Rebuild PHP form using Python (or figure out an alternative path
#TODO: Update content so that it is not generic

