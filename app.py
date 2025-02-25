from flask import (
    Flask, render_template, request,
    session, redirect, url_for,
    flash, get_flashed_messages
)
import database as db
import emails
from flask_socketio import SocketIO, emit, send, join_room
# import tabula
# import pandas as pd
import emails
# import tabula
# import pandas as pd
from werkzeug.utils import secure_filename
import os
from threading import Thread
import tempfile
from events import tech_events, non_tech_events, workshops, person, dexters

UPLOAD_FOLDER = tempfile.gettempdir()  # Use system temp directory
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# List of workshops. Should be updated.


_tech_events = [i["event_name"] for i in tech_events]
_non_tech_events = [i["event_name"] for i in non_tech_events]
_dexturs = ["Code Trail", "Rapid Relfex"]

events = _tech_events + _non_tech_events + _dexturs


@app.route("/")
def index():
    name = None
    if "student_id" in session:
        student = db.get_student_by_id(session["student_id"])
        if student:
            name = student["name"]
        else:
            session.clear()
            name = None

    for i in workshops:
        i["seats_filled"] = db.get_workshop_registration_count(i["event_name"])
        if i["seats_filled"] >= i["seats"]:
            i["disabled"] = True

    return render_template("index.html",
                           name=name,
                           tech_events=tech_events,
                           non_tech_events=non_tech_events,
                           person=person,
                           workshops=workshops,
                           dexters=dexters
                           )


@app.route("/about")
def about():
    name = None
    if "student_id" in session:
        student = db.get_student_by_id(session["student_id"])
        if student:
            name = student["name"]
        else:
            session.clear()
            name = None
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.get("/register")
def register():
    if "student_id" in session:
        flash("You are already registered!", "danger")
        return redirect(url_for("myid"))
    for i in workshops:
        i["seats_filled"] = db.get_workshop_registration_count(i["event_name"])
        if i["seats_filled"] >= i["seats"]:
            i["disabled"] = True
    return render_template(
        "register.html",
        workshops=workshops,
        events=events,
        _tech_events=_tech_events,
        _non_tech_events=_non_tech_events,
        _dexturs=_dexturs)


# @app.post("/register")
# def register_post():
#     name = request.form["name"]
#     email = request.form.get("email", "").strip().lower()
#     phone = request.form["phone"]
#     workshop = request.form.get("workshop", None)
#     events = request.form.get("events", False)
#     college_name = request.form["college_name"]

#     if db.student_exists(email, phone):
#         flash("Error: Email, Phone Number already exists!", "danger")
#         return redirect(url_for("register"))

#     student_data = {
#         "name": name,
#         "email": email,
#         "phone": phone,
#         "workshop": workshop,
#         "events": False,
#         "college_name": college_name
#     }

#     db.create_student(student_data)

#     session["student_id"] = db.get_student_by_email(email)["_id"]
#     flash("Registration successful!", "success")

#     otp = emails.send_otp(email)
#     db.create_payment_entry({
#         "email": email,
#         "paid": False
#     })
#     db.create_login_otp(email, str(otp))
#     emails.send_id_mail(student_data, request.url_root + "myid")
#     if otp:
#         flash("OTP sent successfully!", "success")
#         return redirect("verify_email")
#     else:
#         flash("Error sending OTP! Try logging in.", "danger")
#     return redirect("verify_email")


@app.post("/register")
def register_post():
    try:
        name = request.form["name"]
        email = request.form.get("email", "").strip().lower()
        phone = request.form["phone"]
        workshop = request.form.get("workshop", None)
        # Changed to getlist for multiple events
        selected_events = request.form.getlist("events")
        college_name = request.form["college_name"]

        if db.student_exists(email, phone):
            flash("Error: Email, Phone already exists! Try logging in.", "danger")
            return redirect(url_for("register"))

        student_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "workshop": workshop,
            "events": selected_events,  # Now it's a list
            "college_name": college_name
        }

        db.create_student(student_data)

        session["student_id"] = db.get_student_by_email(email)["_id"]
        flash("Registration successful!", "success")

        otp = emails.send_otp(email)
        db.create_payment_entry({
            "email": email,
            "paid": False,
            "transaction_id": f'not-paid-{session["student_id"]}',
            "upi_id": None
        })
        db.create_login_otp(email, str(otp))
        payment_data = db.get_payment_by_email(email)
        if otp:
            flash("OTP sent successfully!", "success")
            return redirect("verify_email")
        else:
            flash("Error sending OTP! Try logging in.", "danger")
        return redirect("verify_email")

    except Exception as e:
        flash(f"Error registering [{e}]! Try again.", "danger")
        return redirect("register")


@app.get("/login")
def login():
    if "student_id" in session:
        flash("You are already logged in!", "success")
        return redirect(url_for("myid"))
    return render_template("login.html")


@app.post("/login")
def login_post():
    email = request.form["email"]

    # if the email does not exist
    if not db.student_exists(email):
        flash("Error: Email does not exist!", "danger")
        return redirect(url_for("login"))

    session["student_id"] = db.get_student_by_email(email)["_id"]
    otp = emails.send_otp(email)

    # if the otp was sent through the mail,
    # redirect to the verify email page
    if otp:
        if db.get_login_otp_status(email):
            db.update_otp(email, otp)
        else:
            db.create_login_otp(email, str(otp))

        # send the otp
        # unverify the user
        db.unverify_email(email)
        flash("OTP sent successfully!", "success")
        return redirect("verify_email")

    # if unable to send the otp
    flash("Error sending OTP! Try logging in.", "danger")
    return redirect("login")


@app.get("/verify_email")
def verify_email():
    if "student_id" in session:

        # if the student id is not in the database
        if not db.get_student_by_id(session["student_id"]):
            flash("Invalid session!", "danger")
            return redirect(url_for("login"))

        email = db.get_student_by_id(session["student_id"])["email"]

        # check if the email is already verified
        if db.email_is_verified(email):
            student_data = db.get_student_by_email(email)
            payment_data = db.get_payment_by_email(email)
            flash("Email already verified ", "success")
            return redirect("myid")

        # display the enter otp page
        return render_template("verify_email.html", email=email)

    # ask the user to login first.
    flash("Login to verify your email!", "danger")
    return redirect(url_for("login"))


@app.post("/verify_email")
def verify_email_post():
    # the email field should be prefilled and disabled in the html

    email = request.form["email"]
    otp = request.form["otp"]

    # if the email does not exist in the database
    if not db.student_exists(email):
        flash("Error: Email does not exist!", "danger")
        return redirect(url_for("login"))

    student_data = db.get_student_by_email(email)

    # if the email is already verified
    if db.email_is_verified(email):
        payment_data = db.get_payment_by_email(email)
        # emails.send_id_mail(student_data, payment_data,
        # request.url_root + "/admin/student/" + session["student_id"])
        flash("Email already verified! We will verify your payment and send PASS to you mail.", "success")
        return redirect("myid")

    if db.verify_email(email, otp):
        flash("Email verified successfully!", "success")
        payment_detail = db.get_payment_by_email(email)
        if payment_detail is None:
            # ask the student for payment if they are not
            # from sona college of technology
            if not (email.endswith("cse@sonatech.ac.in") or email.endswith("csd@sonatech.ac.in") or email.endswith("aiml@sonatech.ac.in")):
                db.create_payment_entry({"email": email, "paid": False})
                return redirect(url_for("payment"))

            # make the paid column true
            # if they are from sona college
            db.create_payment_entry({"email": email, "paid": False})
        else:
            if (email.endswith("cse@sonatech.ac.in") or email.endswith("csd@sonatech.ac.in") or email.endswith("aiml@sonatech.ac.in")) or payment_detail["paid"]:
                payment_data = db.get_payment_by_email(email)
                if payment_data is None:
                    if student_data["workshop"] == "none":
                        payment_data = {"email": email, "paid": True}
                    else:
                        payment_data = {"email": email, "paid": False}
                    db.create_payment_entry(payment_data)
                elif not payment_data["paid"]:
                    if student_data["workshop"] == "none":
                        payment_data["paid"] = True
                    else:
                        payment_data["paid"] = False
                    db.edit_payment(email, payment_data)
                emails.send_id_mail(
                    student_data, payment_data, request.url_root + "/admin/student/" + session["student_id"])

                if payment_data["paid"] == False and payment["transaction_id"].startswith("not-paid"):
                    return redirect(url_for("payment"))
                return redirect(url_for("myid"))
            else:
                return redirect(url_for("payment"))

        # emails.send_id_mail(student_data, request.url_root +
                # "/admin/student/" + session["student_id"])
        return redirect(url_for("myid"))

    # if the otp is invalid
    flash("Invalid OTP!", "danger")
    return render_template("verify_email.html", email=email)


# the below existing function is used to resend the otp
# it serves as an API that is to be invoked by the js side of the page
# it should not be invoked by any form or user.
@app.post("/resend_otp")
def resend_otp():
    email = request.form["email"]
    # check if the email exists in the database
    if not db.student_exists(email):
        flash("Error: Email does not exist!", "danger")
        return redirect(url_for("login"))

    otp = emails.send_otp(email)
    if not db.get_login_otp_status(email):
        db.create_login_otp(email, str(otp))
    else:
        db.update_otp(email, otp)

    if otp:
        return {
            "success": True,
            "message": "OTP sent!"
        }

    return {
        "success": False,
        "message": "Error sending OTP! Try logging in."
    }


# this page will display the student their details
# this can also be found in their email
@app.get("/myid")
def myid():
    if "student_id" not in session:
        flash("You are not logged in!", "danger")
        return redirect(url_for("login"))

    student_id = session["student_id"]
    student = db.get_student_by_id(student_id)

    # if the student id is not in the database
    if not student:
        flash("Error: Student not found!", "danger")
        session.clear()
        return redirect(url_for("register"))

    # if the student is not verified
    if not db.email_is_verified(student["email"]):
        flash("You are not verified!", "danger")
        return redirect(url_for("verify_email"))

    # if the student has paid
    # or has submitted their payment status
    # or is from sona college
    payment = db.get_payment_by_email(student["email"])
    email = student["email"].lower()


    if (payment and payment["paid"] == False and payment["transaction_id"].startswith("not-paid")) or (student["workshop"] != "none" and (email.endswith("cse@sonatech.ac.in") or email.endswith("csd@sonatech.ac.in") or email.endswith("aiml@sonatech.ac.in"))):
        return redirect(url_for("payment"))

    if (
        (email.endswith("cse@sonatech.ac.in") or email.endswith("csd@sonatech.ac.in") or email.endswith("aiml@sonatech.ac.in")) and
        (
            payment and payment["paid"]
        )
    ):
        return render_template("myid.html", student=student, payment=payment)

    if payment and payment["transaction_id"].startswith("not-paid"):
        flash("You need to enter you payment details first.", "danger")
        return redirect(url_for("payment"))

    flash("Your payment is not yet verified. We will email you once verified.", "danger")
    return redirect(url_for("index"))


@app.get("/payment")
def payment():
    if "student_id" not in session:
        flash("You are not logged in!", "danger")
        return redirect(url_for("login"))

    student_id = session["student_id"]
    student = db.get_student_by_id(student_id)

    payment_data = db.get_payment_by_email(student["email"])

    if payment_data and payment_data["paid"]:
        flash("You have already paid!", "success")
        return redirect(url_for("myid"))
    elif payment_data and not payment_data["transaction_id"].startswith("not-paid"):
        flash("Your payment details were recieved. You will recieve the PASS in mail.", "danger")
        return redirect(url_for("index"))

    # if the student id is not in the database
    if not student:
        flash("Error: Student not found!", "danger")
        return redirect(url_for("register"))

    # if the student is not verified
    if not db.email_is_verified(student["email"]):
        flash("You are not verified!", "danger")
        return redirect(url_for("verify_email"))

    # if the paid is true in the payment_and_otp collection
    if db.get_payment_by_email(student["email"])["paid"]:
        flash("You have already paid!", "danger")
        return redirect(url_for("myid"))

    amount = 0

    if (student["events"] and len(student["events"]) > 0) and (student["workshop"] and student["workshop"].lower() != "none"):
        amount = 500
    elif student["events"]:
        amount = 200
    elif student["workshop"]:
        amount = 300

    file = f"/static/{amount}_rs_threads_QR_Code.png"

    email = student["email"]

    if (student["workshop"] and student["workshop"].lower() != "none") and (
        email.endswith("cse@sonatech.ac.in") or
        email.endswith("csd@sonatech.ac.in") or
        email.endswith("aiml@sonatech.ac.in")
    ):
        file = f"/static/_sct_200_rs_threads_QR_Code.png"

    return render_template("payment.html", student=student, file=file)


@app.post("/payment")
def payment_post():
    if "student_id" not in session:
        flash("You are not logged in!", "danger")
        return redirect(url_for("login"))

    student_id = session["student_id"]
    student = db.get_student_by_id(student_id)

    if not student:
        flash("Error: Student not found!", "danger")
        return redirect(url_for("register"))

    if not db.email_is_verified(student["email"]):
        flash("You are not verified!", "danger")
        return redirect(url_for("verify_email"))

    detail = db.get_payment_by_email(student["email"])
    if detail["paid"]:
        flash("You have already paid!", "success")
        return redirect(url_for("myid"))

    transaction_id = request.form.get("transaction_id")
    upi_id = request.form.get("upi_id")

    db.update_payment_status(
        student["email"], transaction_id, upi_id
    )

    flash("Payment successful!", "success")
    return redirect(url_for("myid"))


# The admin pages are below
@app.get("/admin")
def admin():
    if "admin_username" in session and db.admin_exists(session["admin_username"]):
        return render_template("admin.html")
    else:
        return redirect(url_for("index"))


@app.get("/admin/login-pannu")
def admin_login():
    return render_template("admin_login.html")


@app.post("/admin/login-pannu")
def admin_login_post():
    username = request.form["username"]
    password = request.form["password"]
    if db.match_admin_password(username, password):
        session["admin_username"] = username
        return redirect(url_for("admin"))
    else:
        flash("Incorrect password!", "danger")
        return redirect(url_for("admin_login"))


@app.get("/admin/students")
def admin_students():
    if "admin_username" in session and db.admin_exists(session["admin_username"]):
        students = db.get_all_students()
        payments = {payment["email"]
            : payment for payment in db.get_all_payments()}
        # print(students, payments, db.get_all_payments())
        return render_template("admin_students.html", students=students, payments=payments)

    return redirect(url_for("index"))


@app.get("/admin/student/<student_id>")
def admin_student(student_id):
    if "admin_username" in session and db.admin_exists(session["admin_username"]):
        student = db.get_student_by_id(student_id)
        if student:
            payment = db.get_payment_by_email(student["email"])
            return render_template("myid.html", student=student, payment=payment)
        flash("Student not found!", "danger")
        return redirect(url_for("admin_students"))
    return redirect(url_for("admin_login"))


@app.post("/admin/student/edit/<student_id>")
def admin_student_edit(student_id):
    if "admin_username" in session and db.admin_exists(session["admin_username"]):
        student = db.get_student_by_id(student_id)
        payment_detail = db.get_payment_by_email(student["email"])
        if student:
            # Handle payment updates
            payment_detail["paid"] = request.form.get("paid") == "true"
            transaction_id = request.form.get("transaction_id")
            upi_id = request.form.get("upi_id", "none")

            payment_detail["transaction_id"] = transaction_id
            payment_detail["upi_id"] = upi_id

            if payment_detail["paid"]:
                emails.send_id_mail(
                    student, payment_detail, "https://threadscse.co.in" + "/admin/student/" + student_id)

            # Handle events update if present in form
            if "events" in request.form:
                student["events"] = request.form.getlist("events")
                db.edit_student(student_id, student)
            try:
                db.edit_payment(student["email"], payment_detail)
                return {
                    "success": True,
                    "message": "Student updated successfully!"
                }
            except ValueError as e:
                return {
                    "success": False,
                    "message": "Transaction id should not be null"
                }
        flash("Student not found!", "danger")
        return redirect(url_for("admin_students"))
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
