from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_socketio import SocketIO
from depricated.database import get_students, update_student, check_admin_password, get_student_by_id, add_student, student_exists

app = Flask(__name__)
app.secret_key = "your_secret_key"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        rollno = request.form["rollno"].strip()
        interested_events = request.form.getlist("interested_events")
        
        if student_exists(email, phone, rollno):
            flash("Error: Email, Phone, or Roll Number already exists!", "danger")
            return redirect(url_for("register"))
        
        add_student(name, email, phone, rollno, interested_events)
        flash("Registration successful!", "success")
        return redirect(url_for("register"))
    return render_template("register.html", events=events)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form["password"]
        if check_admin_password(password):
            students = get_students()
            print(students)
            return render_template("admin.html", students=students)
        else:
            flash("Incorrect password!", "danger")
            return redirect(url_for("admin"))
    return render_template("admin.html", students=None)

@app.route("/admin/get_students")
def get_students_endpoint():
    students = get_students()
    return jsonify(students)

@app.route("/admin/check_password", methods=["GET", "POST"])
def check_password():
    password = request.form["password"]
    if check_admin_password(password):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})


@socketio.on("update_student")
def handle_update_student(data):
    update_student(data["id"], data["name"].strip(), data["email"].strip(), data["phone"].strip(), data["rollno"].strip(), data["interested_events"], data["attended_events"], data["paid"])
    print("got signal")
    socketio.emit("update_student", data, to="all")


@app.route("/admin/update_students", methods=["POST"])
def save_students():
    print(request.form)
    students = request.form["students"]
    for student in students:
        update_student(student["id"], student["name"], student["email"], student["phone"], student["rollno"], student["interested_events"], student["attended_events"], student["paid"])
    return jsonify({"success": True})

@app.route("/id")
def student_details():
    student_id = request.args.get("id", type=int)
    if student_id is None:
        flash("Invalid student ID!", "danger")
        return redirect(url_for("index"))

    student = get_student_by_id(student_id)
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for("index"))

    return render_template("student.html", student=student)


if __name__ == "__main__":
    socketio.run(app, debug=True)
