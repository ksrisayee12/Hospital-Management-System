def success(data=None, message="Success", status=200):
    return {
        "success": True,
        "message": message,
        "data": data
    }, status


def error(message="Something went wrong", status=400):
    return {
        "success": False,
        "message": message
    }, status