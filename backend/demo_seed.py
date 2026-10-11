import datetime
import os

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["CAMPUS_DB"] = os.path.join(HERE, "demo.db")

if os.path.exists(os.environ["CAMPUS_DB"]):
    os.remove(os.environ["CAMPUS_DB"])

from database import init_db, get_connection
from security import hash_password
from appointments import book_appointment, respond_appointment
from reschedule import request_reschedule
from notifications import generate_reminders

init_db()
con = get_connection()
for name, email in (("Aarav Mehta", "aarav@campussync.com"), ("Meera Nair", "meera@campussync.com")):
    con.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,'Student')",
                (name, email, hash_password("student123")))
con.commit()
con.close()

def book(student, faculty, day, slot, topic):
    r = book_appointment({"student_id": student, "faculty_id": faculty, "day": day,
                          "time_slot": slot, "topic": topic})
    assert r["success"], r

book(3, 2, "Mon", "14:00", "ER diagram review")
book(5, 2, "Thu", "11:00", "Project viva preparation")
book(6, 2, "Tue", "15:00", "Normalization doubts")
book(3, 4, "Fri", "10:00", "AI mini-project ideas")
book(3, 2, "Wed", "10:00", "Transaction isolation levels")

for appt, fac in ((1, 2), (2, 2), (4, 4)):
    assert respond_appointment({"appointment_id": appt, "faculty_id": fac, "action": "Accepted"})["success"]

assert request_reschedule({"appointment_id": 2, "student_id": 5, "day": "Fri",
                           "time_slot": "14:00", "reason": "Clash with a lab exam"})["success"]

c = get_connection()
today = datetime.date.today()
monday = today + datetime.timedelta(days=(7 - today.weekday()) % 7 or 7)
generate_reminders(c, monday)
c.close()
print("demo.db ready. Logins: student@campussync.com / student123, faculty@campussync.com / faculty123,"
      " admin@campussync.com / admin123")