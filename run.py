import os
from flask import Flask, request, render_template
import flask_mail
import csv
import smtplib
from email.message import EmailMessage
import hvac   # https://hvac.readthedocs.io/en/stable/overview.html

app = Flask(__name__)

# TODO: hide this secret key using vault
secret_key = os.urandom(12).hex()
app.secret_key = secret_key


def file_to_csv(data):
    """Takes the response from form completion and files it to a CSV for tracking"""
    with open("database.csv", "a", newline="") as database:
        name = data["name"]
        email = data["email"]
        subject = data["subject"]
        message = data["message"]

        csv_write = csv.writer(database)
        csv_write.writerow([name, email, subject, message])


def form_to_mail(data):
    """Takes the response from form completion and sends it to email.
    Credentials for email auth pulled via API to Hashicorp Vault"""
    name = data["name"]
    email_address = data["email"]
    subject = data["subject"]
    message = data["message"]

    email = EmailMessage()
    email["from"] = name
    email["to"] = ''            # TODO: Add email address
    email["subject"] = subject

    email.set_content(email_address, message)

    # TODO: Rebuild using flask-mail
    try:
        with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
            smtp.ehlo()  # alerts the SMTP server that we are awake and ready to send
            smtp.starttls()  # TLS is an encryption mechanism
            # TODO: Deploy vault with AWS to feed credentials into login below
            smtp.login()   # Uses HVAC API to pull credentials from Vault
            smtp.send_message(email)

    except smtplib.SMTPResponseException as err:
        return err

@app.route("/")
def index():
    """Defines route for websites home page"""
    return render_template("/index.html")


@app.route("/submit", methods=["POST", "GET"])
def submit_form():
    """This route is triggered upon clicking submit form (method = POST)
    and sends an email notification via the form_to_mail func"""
    if request.method == "POST":
        try:
            response = request.form.to_dict()
            file_to_csv(response)
            form_to_mail(response)

        except:
            return "Unable to save to database."

        return f"Thank you, {response['name']}. I will be in touch shortly."

    else:
        return "Something went wrong."


# TODO: Rebuild PHP form using Python (or figure out an alternative path)
# TODO: Update content so that it is not generic

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)