
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "student-registration-dev-key"

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "students.db"


# Database connection
def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# Create database table if it does not exist
def initialize_database():
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                course TEXT NOT NULL
            )
        """)


# Register students and display/search records
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()

        if not name or not email or not course:
            flash("Please complete all fields.", "error")
            return redirect(url_for("index"))

        try:
            with get_db_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO students (name, email, course)
                    VALUES (?, ?, ?)
                    """,
                    (name, email, course)
                )

            flash("Student registered successfully!", "success")

        except sqlite3.IntegrityError:
            flash("This email is already registered.", "error")

        return redirect(url_for("index"))

    search = request.args.get("q", "").strip()

    with get_db_connection() as connection:
        if search:
            students = connection.execute(
                """
                SELECT * FROM students
                WHERE name LIKE ?
                   OR email LIKE ?
                   OR course LIKE ?
                ORDER BY id DESC
                """,
                (
                    f"%{search}%",
                    f"%{search}%",
                    f"%{search}%"
                )
            ).fetchall()
        else:
            students = connection.execute(
                "SELECT * FROM students ORDER BY id DESC"
            ).fetchall()

    return render_template(
        "index.html",
        students=students,
        search=search
    )


# Edit an existing student
@app.route("/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    with get_db_connection() as connection:
        student = connection.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        ).fetchone()

        if student is None:
            flash("Student record not found.", "error")
            return redirect(url_for("index"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            course = request.form.get("course", "").strip()

            if not name or not email or not course:
                flash("Please complete all fields.", "error")
                return render_template(
                    "edit.html",
                    student=student
                )

            try:
                connection.execute(
                    """
                    UPDATE students
                    SET name = ?, email = ?, course = ?
                    WHERE id = ?
                    """,
                    (name, email, course, student_id)
                )

                flash("Student updated successfully!", "success")
                return redirect(url_for("index"))

            except sqlite3.IntegrityError:
                updated_student = {
                    "id": student_id,
                    "name": name,
                    "email": email,
                    "course": course
                }

                flash(
                    "That email is already registered to another student.",
                    "error"
                )

                return render_template(
                    "edit.html",
                    student=updated_student
                )

    return render_template("edit.html", student=student)


# Delete a student
@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    with get_db_connection() as connection:
        connection.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )

    flash("Student record deleted.", "success")
    return redirect(url_for("index"))


# Start the application
if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
