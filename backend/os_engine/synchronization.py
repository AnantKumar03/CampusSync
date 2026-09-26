import threading

slot_lock = threading.Lock()
booked_slots = []


def try_booking(slot):
    with slot_lock:
        if slot in booked_slots:
            return {
                "success": False,
                "message": "Slot is already booked"
            }

        booked_slots.append(slot)

        return {
            "success": True,
            "message": "Slot booked successfully"
        }