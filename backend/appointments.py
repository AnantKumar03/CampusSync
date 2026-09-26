import sqlite3
import threading
from database import get_connection

booking_lock = threading.Lock()

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
TIME_SLOTS = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]
ACTIVE = "('Pending', 'Accepted', 'Rescheduled')"   # statuses that occupy a slot


def slot_problem(con, faculty_id, day, time_slot, ignore_id=None):
    """Return a message if the slot cannot be used, otherwise None."""
    if day not in DAYS or time_slot not in TIME_SLOTS:
        return "Invalid day or time slot"

    if con.execute("""
        SELECT 1 FROM timetable
        WHERE faculty_id=? AND day=? AND time_slot=?
    """, (faculty_id, day, time_slot)).fetchone():
        return "Faculty is teaching at this time"

    if con.execute("""
        SELECT 1 FROM appointments
        WHERE faculty_id=? AND day=? AND time_slot=?
        AND status IN """ + ACTIVE + """
        AND appointment_id IS NOT ?
    """, (faculty_id, day, time_slot, ignore_id)).fetchone():
        return "Appointment slot already booked"

    return None


def book_appointment(data):
    try:
        student_id = data["student_id"]
        faculty_id = data["faculty_id"]
        day = data["day"]
        time_slot = data["time_slot"]
    except KeyError:
        return {"success": False, "message": "Missing booking details"}

    topic = (data.get("topic") or "").strip()

    # Critical section:
    # only one thread should check and book a slot at a time.
    with booking_lock:
        con = get_connection()

        try:
            problem = slot_problem(con, faculty_id, day, time_slot)
            if problem:
                return {"success": False, "message": problem}

            con.execute("""
                INSERT INTO appointments
                (student_id, faculty_id, day, time_slot, topic)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, faculty_id, day, time_slot, topic))

            con.commit()
            return {"success": True, "message": "Request sent to faculty"}

        except sqlite3.IntegrityError:
            # Database constraint is the last line of defence against double booking.
            con.rollback()
            return {"success": False, "message": "Appointment slot already booked"}

        except Exception as e:
            con.rollback()
            return {"success": False, "message": str(e)}

        finally:
            con.close()


def get_appointments(params=None):
    params = params or {}
    sql = """
        SELECT a.appointment_id, a.student_id, a.faculty_id,
               s.name AS student, f.name AS faculty,
               a.day, a.time_slot, a.topic, a.status
        FROM appointments a
        JOIN users s ON a.student_id = s.user_id
        JOIN users f ON a.faculty_id = f.user_id
        WHERE 1=1
    """
    args = []

    for key in ("student_id", "faculty_id"):
        if params.get(key):
            sql += " AND a." + key + "=?"
            args.append(params[key])

    sql += " ORDER BY a.appointment_id DESC"

    con = get_connection()
    rows = con.execute(sql, args).fetchall()
    con.close()

    return [dict(row) for row in rows]


def get_availability(params):
    """Free slots of one faculty for the whole week (no class, no active booking)."""
    faculty_id = params.get("faculty_id")

    con = get_connection()
    rows = con.execute("""
        SELECT day, time_slot FROM timetable WHERE faculty_id=?
        UNION
        SELECT day, time_slot FROM appointments
        WHERE faculty_id=? AND status IN """ + ACTIVE, (faculty_id, faculty_id)).fetchall()
    con.close()

    busy = {(r["day"], r["time_slot"]) for r in rows}

    return {
        "success": True,
        "slots": {d: [t for t in TIME_SLOTS if (d, t) not in busy] for d in DAYS}
    }


def respond_appointment(data):
    action = data.get("action")

    if action not in ("Accepted", "Rejected"):
        return {"success": False, "message": "Action must be Accepted or Rejected"}

    with booking_lock:
        con = get_connection()
        cur = con.execute("""
            UPDATE appointments SET status=?
            WHERE appointment_id=? AND faculty_id=? AND status='Pending'
        """, (action, data.get("appointment_id"), data.get("faculty_id")))
        con.commit()
        changed = cur.rowcount
        con.close()

    if not changed:
        return {"success": False, "message": "Request not found or already handled"}

    return {"success": True, "message": "Booking " + action.lower()}


def reschedule_appointment(data):
    appointment_id = data.get("appointment_id")
    faculty_id = data.get("faculty_id")

    with booking_lock:
        con = get_connection()

        try:
            row = con.execute("""
                SELECT 1 FROM appointments
                WHERE appointment_id=? AND faculty_id=? AND status IN """ + ACTIVE,
                (appointment_id, faculty_id)).fetchone()

            if row is None:
                return {"success": False, "message": "Appointment not found"}

            problem = slot_problem(con, faculty_id, data.get("day"),
                                   data.get("time_slot"), ignore_id=appointment_id)
            if problem:
                return {"success": False, "message": problem}

            con.execute("""
                UPDATE appointments
                SET day=?, time_slot=?, status='Rescheduled'
                WHERE appointment_id=?
            """, (data["day"], data["time_slot"], appointment_id))

            con.commit()
            return {"success": True, "message": "Booking rescheduled"}

        except sqlite3.IntegrityError:
            con.rollback()
            return {"success": False, "message": "Appointment slot already booked"}

        finally:
            con.close()


def cancel_appointment(data):
    con = get_connection()

    cur = con.execute("""
        UPDATE appointments
        SET status='Cancelled'
        WHERE appointment_id=? AND (student_id=? OR faculty_id=?)
        AND status IN """ + ACTIVE,
        (data.get("appointment_id"), data.get("user_id"), data.get("user_id")))

    con.commit()
    changed = cur.rowcount
    con.close()

    if not changed:
        return {"success": False, "message": "Appointment cannot be cancelled"}

    return {"success": True, "message": "Appointment cancelled"}