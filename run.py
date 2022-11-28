import sys
import boto3
from smtplib import SMTPException
from flask import Flask, request, render_template, redirect
from flask_mail import Mail, Message
# from flask_executor import Executor # - removed for Python Anywhere
import mysql.connector


# Initiate AWS SSM integration for secrets storage
ssm = boto3.client('ssm')

# Initialize Flask app and pull secret key from AWS
app = Flask(__name__)
app.secret_key = ssm.get_parameter(Name="FOLIO_APP_SECRET", WithDecryption=True)['Parameter']['Value']

# executor = Executor(app)  # Initialise the executor object for asynchronous sending of email - removed for Python Anywhere


def file_to_db(data, ssm):
    """Takes the response from form completion and files it to a CSV for tracking"""
    try:
        mydb = mysql.connector.connect(
            host=ssm.get_parameter(Name="FOLIO_DB_HOST")['Parameter']['Value'],
            user=ssm.get_parameter(Name="FOLIO_DB_USER")['Parameter']['Value'],
            password=ssm.get_parameter(Name="FOLIO_DB_PASS", WithDecryption=True)['Parameter']['Value'],
        )
    except mysql.connector.Error as err:
        sys.stderr.write(err)
        return err

    mydb.database = "jonotassia$default"
    mycursor = mydb.cursor()

    name = data["name"]
    email = data["email"]
    subject = data["subject"]
    message = data["message"]

    sql = "INSERT INTO form_data (name, email, subject, message) VALUES (%s, %s, %s, %s)"
    val = (name, email, subject, message)

    mycursor.execute(sql, val)
    mydb.commit()

    print(mycursor.lastrowid)


# @executor.job  # Mail sent asynchronously using Flask-Executor library - removed for Python Anywhere
def form_to_mail(data, app, ssm):
    """Takes the response from form completion and sends it to email.
    Credentials for email auth pulled via API to Hashicorp Vault."""
    name = data["name"]
    email_address = data["email"]
    subject = data["subject"]
    message = data["message"]

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = ssm.get_parameter(Name="FOLIO_MAIL_USERNAME")['Parameter']['Value']
    app.config['MAIL_PASSWORD'] = ssm.get_parameter(Name="FOLIO_MAIL_PASSWORD", WithDecryption=True)['Parameter']['Value']
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

    mail = Mail(app)
    recipients = ssm.get_parameter(Name="FOLIO_MAIL_TO_EMAIL")['Parameter']['Value']

    msg = Message(subject=f"{name}: {subject}", recipients=[recipients], sender=app.config['MAIL_USERNAME'])
    msg.body = f"From: {email_address}\n\n{message}"

    try:
        mail.send(msg)

    except SMTPException as err:
        return err


@app.route('/<string:page_name>')
def web_page(page_name):
    return render_template(page_name)


@app.route("/")
def index():
    """Defines route for websites home page"""
    return render_template("/index.html")


@app.route("/submit", methods=["POST", "GET"])
def submit_form():
    """This route is triggered upon clicking submit form (method = POST)
    and sends an email notification via the form_to_mail func"""
    if request.method == "POST":
        response = request.form.to_dict()

        file_to_db(response, ssm)                  # Hide when not on Python Anywhere
        form_to_mail(response, app, ssm)             # Use this for Python Anywhere as it does not support asynch queues
        # form_to_mail.submit(response, app, ssm)    # Submit using asynchronous queue from Flask-Executor

        return redirect(request.referrer)

    else:
        return "Something went wrong."


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

