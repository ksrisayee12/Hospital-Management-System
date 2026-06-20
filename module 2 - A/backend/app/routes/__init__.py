# routes package
from app.routes.patient_routes import include_healthcare_routes
from app.routes.ai_routes import include_ai_routes

__all__ = ["include_healthcare_routes", "include_ai_routes"]
