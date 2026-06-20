from flask import Blueprint, request
from supabase_client import supabase
from utils.response import success, error

nfc_bp = Blueprint("nfc_bp", __name__)


@nfc_bp.route("/nfc/scan", methods=["GET", "POST"])
def nfc_scan():
    try:
        if request.method == "POST":
            body = request.get_json()
        else:
            body = request.args

        if not body:
            return error("Missing data (JSON body or query params)", 400)

        doctor_code = body.get("doctor_code")
        nfc_uid = body.get("nfc_uid")
        patient_id = body.get("patient_id")
        action = body.get("action", "CHECK_IN")
        scanned_from = body.get("scanned_from", "mobile")

        if not doctor_code:
            return error("doctor_code is required", 400)

        if not nfc_uid:
            return error("nfc_uid is required", 400)

        doctor_result = (
            supabase.table("doctors")
            .select("*")
            .eq("doctor_code", doctor_code)
            .execute()
        )

        if not doctor_result.data or len(doctor_result.data) == 0:
            return error("Doctor not found", 404)

        doctor = doctor_result.data[0]
        new_count = doctor.get("access_count", 0) + 1

        supabase.table("doctors").update({
            "access_count": new_count
        }).eq("doctor_code", doctor_code).execute()

        log_payload = {
            "doctor_code": doctor_code,
            "nfc_uid": nfc_uid,
            "patient_id": patient_id,
            "action": action,
            "scanned_from": scanned_from
        }

        log_result = (
            supabase.table("nfc_access_logs")
            .insert(log_payload)
            .execute()
        )

        response_data = {
            "doctor_code": doctor_code,
            "doctor_name": doctor.get("name"),
            "specialization": doctor.get("specialization"),
            "access_count": new_count,
            "latest_log": log_result.data[0] if log_result.data else None
        }

        return success(response_data, "NFC scan recorded successfully", 201)

    except Exception as e:
        return error(str(e), 500)


@nfc_bp.route("/nfc/latest", methods=["GET"])
def latest_nfc_scan():
    try:
        result = (
            supabase.table("nfc_access_logs")
            .select("*")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )

        latest = result.data[0] if result.data else None
        return success(latest, "Latest NFC scan fetched successfully")

    except Exception as e:
        return error(str(e), 500)


@nfc_bp.route("/nfc/tap/<doctor_code>", methods=["GET"])
def nfc_tap(doctor_code):
    try:
        nfc_uid = request.args.get("nfc_uid", "NFC_TAG")
        patient_id = request.args.get("patient_id", "PAT001")

        doctor_result = (
            supabase.table("doctors")
            .select("*")
            .eq("doctor_code", doctor_code)
            .execute()
        )

        if not doctor_result.data or len(doctor_result.data) == 0:
            return {
                "success": False,
                "message": "Doctor not found"
            }, 404

        doctor = doctor_result.data[0]
        new_count = doctor.get("access_count", 0) + 1

        supabase.table("doctors").update({
            "access_count": new_count
        }).eq("doctor_code", doctor_code).execute()

        supabase.table("nfc_access_logs").insert({
            "doctor_code": doctor_code,
            "nfc_uid": nfc_uid,
            "patient_id": patient_id,
            "action": "CHECK_IN",
            "scanned_from": "mobile_nfc_url"
        }).execute()

        return {
            "success": True,
            "message": "NFC doctor tap recorded",
            "doctor_code": doctor_code,
            "access_count": new_count
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }, 500