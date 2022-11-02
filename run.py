import os
import sys
from dotenv import load_dotenv
from smtplib import SMTPException
from flask import Flask, request, render_template, redirect
from flask_mail import Mail, Message
# from flask_executor import Executor # - removed for Python Anywhere
import mysql.connector
# import hvac   # https://hvac.readthedocs.io/en/stable/overview.html


load_dotenv()
app = Flask(__name__)
# executor = Executor(app)  # Initialise the executor object for asynchronous sending of email - removed for Python Anywhere

# TODO: hide this secret key using vault
app.secret_key = os.getenv("APP_SECRET")

def file_to_db(data):
    """Takes the response from form completion and files it to a CSV for tracking"""
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
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
def form_to_mail(data, app):
    """Takes the response from form completion and sends it to email.
    Credentials for email auth pulled via API to Hashicorp Vault."""
    name = data["name"]
    email_address = data["email"]
    subject = data["subject"]
    message = data["message"]

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    # TODO: Deploy vault with AWS to feed credentials into login below and mail_to address
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

    mail = Mail(app)

    msg = Message(subject=f"{name}: {subject}", recipients=[os.getenv('MAIL_TO_EMAIL')], sender=app.config['MAIL_USERNAME'])
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
        file_to_db(response)                  # Hide when not on Python Anywhere
        form_to_mail(response, app)             # Use this for Python Anywhere as it does not support asynch queues
        # form_to_mail.submit(response, app)    # Submit using asynchronous queue from Flask-Executor

        return redirect(request.referrer)

    else:
        return "Something went wrong."


# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5000, debug=True)


# TODO: Update facts section with current numbers
# TODO: Update portfolio with list of works
