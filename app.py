from flask import (
    Flask, render_template, request, 
    session, redirect, url_for,
    flash, get_flashed_messages
)
import database as db
import emails 
from flask_socketio import SocketIO, emit, send, join_room


app = Flask(__name__)
app.secret_key = "your_secret_key"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# List of workshops. Should be updated.
workshops = [
    "Workshop 1",
    "Workshop 2",
    "Workshop 3"
]

@app.route("/")
def index():
    if "student_id" in session:
        name = db.get_student_by_id(session["student_id"])["name"]
        return render_template("index.html", name=name)
    return render_template("index.html")


@app.route("/about")
def about():
    if "student_id" in session:
        name = db.get_student_by_id(session["student_id"])["name"]
        return render_template("index.html", name=name)
    return render_template("about.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.get("/register")
def register():
    if "student_id" in session:
        flash("You are already registered!", "danger")
        return redirect(url_for("myid"))
    return render_template("register.html", workshops=workshops)


@app.post("/register")
def register_post():
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    rollno = request.form["rollno"]
    workshop = request.form.get("workshop", None)
    events = request.form.get("events", False)
    college_name = request.form["college_name"]

    if db.student_exists(email, phone, rollno):
        flash("Error: Email, Phone, or Roll Number already exists!", "danger")
        return redirect(url_for("register"))

    student_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "rollno": rollno,
        "workshop": workshop,
        "events": False,
        "college_name": college_name
    }

    db.create_student(student_data)
    
    session["student_id"] = db.get_student_by_email(email)["_id"]
    flash("Registration successful!", "success")

    otp = emails.send_otp(email)
    db.create_payment_entry({
        "email": email,
        "opt": str(otp),
        "verified": False
    })
    if otp:
        flash("OTP sent successfully!", "success")
        return redirect("verify_email")
    else:
        flash("Error sending OTP! Try logging in.", "danger")
    return redirect("verify_email")


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
            flash("Email already verified", "success")
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

    # if the email is already verified
    if db.email_is_verified(email):
        flash("Email already verified", "success")
        return redirect("myid")

    if db.verify_otp(email, otp):
        db.verify_email(email, otp) # change the verified field to true

        flash("Email verified successfully!", "success")
        # ask the student for payment if they are not
        # from sona college of technology 
        if not email.endswith("@sonatech.ac.in"):
            db.create_payment_entry({"email": email})
            return redirect(url_for("payment"))
        
        # make the paid column true
        # if they are from sona college
        db.create_payment_entry({"email": email, "paid": True})
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
        return redirect(url_for("register"))
    
    # if the student is not verified
    if not db.email_is_verified(student["email"]):
        flash("You are not verified!", "danger")
        return redirect(url_for("verify_email"))

    # if the student has paid
    # or has submitted their payment status
    # or is from sona college
    payment = db.get_payment_by_email(student["email"])
    if (
        student["email"].endswith("@sonatech.ac.in") or 
        (   
            payment and (
                (payment["upi_id"] and payment["transaction_id"]) 
                or payment["paid"]
            )
        )
    ):
        return render_template("myid.html", student=student, payment=payment)

    return redirect(url_for("payment"))


@app.get("/payment")
def payment_get():
    if "student_id" not in session:
        flash("You are not logged in!", "danger")
        return redirect(url_for("login"))
    
    student_id = session["student_id"]
    student = db.get_student_by_id(student_id)

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

    return render_template("payment.html", student=student)


# this page will get the transaction id and
# the upi id of the student from the payment form
@app.post("/payment")
def payment_post():
    if "student_id" not in session:
        flash("You are not logged in!", "danger")
        return redirect(url_for("login"))
    
    student_id = session["student_id"]
    student = db.get_student_by_id(student_id)

    # if the student id is not in the database
    if not student:
        flash("Error: Student not found!", "danger")

    # if the student is not verified
    if not db.email_is_verified(student["email"]):
        flash("You are not verified!", "danger")
        return redirect(url_for("verify_email"))
    
    # if the paid is true in the payment_and_otp collection
    if db.get_payment_by_email(student["email"]):
        flash("You have already paid!", "success")
        return redirect(url_for("myid"))
    
    transaction_id = request.form.get("transaction_id")
    upi_id = request.form.get("upi_id")

    db.update_payment_status(student["email"], transaction_id, upi_id)
    
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
    if db.match_admin_password(password):
        session["admin_username"] = username
        return redirect(url_for("admin"))
    else:
        flash("Incorrect password!", "danger")
        return redirect(url_for("admin_login"))


@app.get("/admin/students")
def admin_students():
    if "admin_username" in session and db.admin_exists(session["admin_username"]):
        students = db.get_all_students()  # We need to add this function
        payments = db.get_all_payments()
        return render_template("admin_students.html", students=students, payments=payments)
    
    return redirect(url_for("index"))

@app.get("/admin/student/<student_id>")
def admin_student(student_id):
    if "admin_username" in session and db.admin_exists(session["admin_username"]):
        student = db.get_student_by_id(student_id)
        if student:
            return render_template("admin_student.html", student=student)
        flash("Student not found!", "danger")
        return redirect(url_for("admin_students"))
    return redirect(url_for("admin_login"))


@app.post("/admin/student/edit/<student_id>")
def admin_student_edit(student_id):
    if "admin_username" in session and db.admin_exists(session["admin_username"]):
        student = db.get_student_by_id(student_id)
        if student:
            student["name"] = request.form.get("name")
            student["paid"] = request.form.get("paid")
            student["transaction_id"] = request.form.get("transaction_id")
            student["upi_id"] = request.form.get("upi_id")
            db.edit_student(student_id, student)
            return {
                "success": True,
                "message": "Student updated successfully!"
            }
        flash("Student not found!", "danger")
        return redirect(url_for("admin_students"))
    return redirect(url_for("index"))


if __name__ == "__main__": 
    app.run(debug=True)
