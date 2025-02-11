from flask import (
    Flask, render_template, request, 
    session, redirect, url_for,
    flash, get_flashed_messages
)
import database as db
from emails import send_id_mail
# import socketio to establish realtime editing in the admin/students page
from flask_socketio import SocketIO, emit, send, join_room

socketio = SocketIO()

events = [
    "Event 1",
    "Event 2",
    "Event 3",
    "Event 4",
    "Event 5",
    "Event 6",
    "Event 7",
    "Event 8",
    "Event 9",
    "Event 10"
]

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/")
def index():
    return render_template("index.html")


@app.get("/register")
def register():
    return render_template("register.html", events=events)


@app.post("/register")
def register_post():
    print("at register")
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    rollno = request.form["rollno"]
    interested_events = request.form.getlist("interested_events")
    transaction_id = request.form["transaction_id"]
    upi_id = request.form["upi_id"]

    if db.student_exists(email, phone, rollno):
        flash("Error: Email, Phone, or Roll Number already exists!", "danger")
        return redirect(url_for("register"))
    
    registered_events = {event: False for event in interested_events}
    student_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "rollno": rollno,
        "registered_events": registered_events,
        "paid": False,
        "transaction_id": transaction_id,
        "upi_id": upi_id
    }
    db.create_student(student_data)
    send_id_mail(student_data)
    
    session["student_id"] = db.get_student_by_email(email)["id"]
    flash("Registration successful!", "success")

    return redirect("myid")


@app.get("/myid")
def myid():
    if "student_id" in session:
        student_id = session["student_id"]
        student = db.get_student_by_id(student_id)
        return render_template("student.html", student=student)
    else:
        return redirect(url_for("register"))
    

@app.get("/admin")
def admin():
    if "isadmin" in session and session["isadmin"]:
        return render_template("admin.html")
    else:
        return redirect(url_for("index"))


@app.get("/admin/login")
def admin_login():
    return render_template("admin_login.html")


@app.post("/admin/login")
def admin_login_post():
    password = request.form["password"]
    if db.check_admin_password(password):
        session["isadmin"] = True
        return redirect(url_for("admin"))
    else:
        flash("Incorrect password!", "danger")
        return redirect(url_for("admin_login"))


# handle the realtime editing in the admin/students page
@socketio.on("edit_student")
def handle_edit_student(data):
    # get the student id, and use the edit_student in db
    db.edit_student(data["id"], {
        "name": data["name"], 
        "email": data["email"], 
        "phone": data["phone"], 
        "rollno": data["rollno"], 
        "registered_events": data["registered_events"], 
        "paid": data["paid"], 
        "transaction_id": data["transaction_id"],
        "upi_id": data["upi_id"]
    })
    print("got signal")
    emit("student_updated", data, to="all")


@socketio.on("join_room")
def handle_join_room(student_id):
    """Join a room specific to a student for individual updates"""
    join_room(f"student_{student_id}")

@socketio.on("individual_edit_student")
def handle_individual_edit(data):
    student_id = data.pop("id")
    updated_student = db.edit_student(student_id, data)
    if updated_student:
        emit("student_updated", updated_student, 
             to=f"student_{student_id}")


@app.get("/admin/students")
def admin_students():
    if "isadmin" in session and session["isadmin"]:
        students = db.get_all_students()  # We need to add this function
        return render_template("admin_students.html", students=students)
    return redirect(url_for("admin_login"))


@app.get("/admin/student/<student_id>")
def admin_student(student_id):
    if "isadmin" in session and session["isadmin"]:
        student = db.get_student_by_id(student_id)
        if student:
            return render_template("admin_student.html", student=student)
        flash("Student not found!", "danger")
        return redirect(url_for("admin_students"))
    return redirect(url_for("admin_login"))




if __name__ == "__main__":
    # use socketio
    socketio.init_app(app)
    socketio.run(app, port=5050, debug=True)
