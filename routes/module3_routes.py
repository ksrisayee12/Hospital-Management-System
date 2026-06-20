from flask import Blueprint, request
from supabase_client import supabase
from utils.response import success, error

module3_bp = Blueprint("module3_bp", __name__)


def log_activity(doctor_code, patient_id, action, details=""):
    supabase.table("doctor_activity_logs").insert({
        "doctor_code": doctor_code,
        "patient_id": patient_id,
        "action": action,
        "details": details
    }).execute()


@module3_bp.route("/doctor/<doctor_code>/dashboard", methods=["GET"])
def doctor_dashboard(doctor_code):
    try:
        patients = supabase.table("doctor_patients").select("*").eq("doctor_code", doctor_code).execute()
        appointments = supabase.table("appointments").select("*").eq("doctor_code", doctor_code).execute()
        logs = supabase.table("doctor_activity_logs").select("*").eq("doctor_code", doctor_code).execute()
        doctor_record = supabase.table("doctors").select("access_count").eq("doctor_code", doctor_code).execute()

        access_count = doctor_record.data[0].get("access_count", 0) if doctor_record.data else 0

        data = {
            "doctor_code": doctor_code,
            "total_patients": len(patients.data),
            "total_appointments": len(appointments.data),
            "total_activities": len(logs.data),
            "access_count": access_count,
            "patients": patients.data,
            "appointments": appointments.data
        }

        return success(data, "Doctor dashboard fetched successfully")

    except Exception as e:
        return error(str(e), 500)


@module3_bp.route("/doctor/<doctor_code>/patients", methods=["GET"])
def get_doctor_patients(doctor_code):
    try:
        result = (
            supabase.table("doctor_patients")
            .select("*")
            .eq("doctor_code", doctor_code)
            .execute()
        )

        return success(result.data, "Doctor patients fetched successfully")

    except Exception as e:
        return error(str(e), 500)


@module3_bp.route("/patient/<patient_id>/records", methods=["GET"])
def get_patient_records(patient_id):
    try:
        doctor_code = request.args.get("doctor_code")

        records = (
            supabase.table("patient_records")
            .select("*")
            .eq("patient_id", patient_id)
            .execute()
        )

        if doctor_code:
            log_activity(
                doctor_code,
                patient_id,
                "VIEW_RECORDS",
                f"Doctor viewed records of patient {patient_id}"
            )

        return success(records.data, "Patient records fetched successfully")

    except Exception as e:
        return error(str(e), 500)


@module3_bp.route("/appointments/<doctor_code>", methods=["GET"])
def get_doctor_appointments(doctor_code):
    try:
        result = (
            supabase.table("appointments")
            .select("*")
            .eq("doctor_code", doctor_code)
            .order("appointment_time", desc=False)
            .execute()
        )

        return success(result.data, "Appointments fetched successfully")

    except Exception as e:
        return error(str(e), 500)


@module3_bp.route("/appointments/update-status", methods=["POST"])
def update_appointment_status():
    try:
        body = request.get_json()

        appointment_id = body.get("appointment_id")
        status = body.get("status")

        if not appointment_id or not status:
            return error("appointment_id and status are required", 400)

        result = (
            supabase.table("appointments")
            .update({"status": status})
            .eq("id", appointment_id)
            .execute()
        )

        return success(result.data, "Appointment status updated successfully")

    except Exception as e:
        return error(str(e), 500)


@module3_bp.route("/clinical/validate", methods=["POST"])
def clinical_validate():
    try:
        body = request.get_json()

        medicine_name = body.get("medicine_name", "")
        dosage = body.get("dosage", "")
        allergies = body.get("allergies", [])

        alerts = []
        ai_status = "SAFE"

        if "5000" in dosage or "10000" in dosage:
            alerts.append("Possible dosage anomaly detected")
            ai_status = "WARNING"

        for allergy in allergies:
            if allergy.lower() in medicine_name.lower():
                alerts.append("Possible allergy conflict detected")
                ai_status = "CRITICAL"

        data = {
            "ai_status": ai_status,
            "alerts": alerts,
            "message": "Clinical validation completed"
        }

        return success(data, "AI clinical validation completed")

    except Exception as e:
        return error(str(e), 500)


@module3_bp.route("/prescription/create", methods=["POST"])
def create_prescription():
    try:
        body = request.get_json()

        required = ["doctor_code", "patient_id", "medicine_name", "dosage", "frequency", "duration"]

        for field in required:
            if not body.get(field):
                return error(f"{field} is required", 400)

        medicine_name = body.get("medicine_name")
        dosage = body.get("dosage")

        ai_status = "SAFE"

        if "5000" in dosage or "10000" in dosage:
            ai_status = "WARNING"

        prescription_payload = {
            "doctor_code": body.get("doctor_code"),
            "patient_id": body.get("patient_id"),
            "medicine_name": medicine_name,
            "dosage": dosage,
            "frequency": body.get("frequency"),
            "duration": body.get("duration"),
            "ai_status": ai_status,
            "doctor_confirmed": body.get("doctor_confirmed", False)
        }

        result = (
            supabase.table("prescriptions")
            .insert(prescription_payload)
            .execute()
        )

        log_activity(
            body.get("doctor_code"),
            body.get("patient_id"),
            "CREATE_PRESCRIPTION",
            f"Created prescription for {medicine_name}"
        )

        return success(result.data, "Prescription created successfully", 201)

    except Exception as e:
        return error(str(e), 500)


@module3_bp.route("/doctor/<doctor_code>/activity", methods=["GET"])
def get_doctor_activity(doctor_code):
    try:
        result = (
            supabase.table("doctor_activity_logs")
            .select("*")
            .eq("doctor_code", doctor_code)
            .order("timestamp", desc=True)
            .execute()
        )

        return success(result.data, "Doctor activity logs fetched successfully")

    except Exception as e:
        return error(str(e), 500)