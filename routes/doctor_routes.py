from flask import Blueprint
from supabase_client import supabase
from utils.response import success, error

doctor_bp = Blueprint("doctor_bp", __name__)


@doctor_bp.route("/doctors", methods=["GET"])
def get_all_doctors():
    try:
        result = supabase.table("doctors").select("*").execute()
        return success(result.data, "Doctors fetched successfully")
    except Exception as e:
        return error(str(e), 500)


@doctor_bp.route("/doctors/<doctor_code>", methods=["GET"])
def get_doctor_by_code(doctor_code):
    try:
        result = (
            supabase.table("doctors")
            .select("*")
            .eq("doctor_code", doctor_code)
            .single()
            .execute()
        )

        if not result.data:
            return error("Doctor not found", 404)

        return success(result.data, "Doctor details fetched successfully")

    except Exception as e:
        return error(str(e), 500)


@doctor_bp.route("/doctors/<doctor_code>/logs", methods=["GET"])
def get_doctor_logs(doctor_code):
    try:
        result = (
            supabase.table("nfc_access_logs")
            .select("*")
            .eq("doctor_code", doctor_code)
            .order("timestamp", desc=True)
            .execute()
        )

        return success(result.data, "Doctor NFC logs fetched successfully")

    except Exception as e:
        return error(str(e), 500)