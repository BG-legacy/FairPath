"""
Routes package - combining all route modules
"""
from fastapi import APIRouter
from routes.example import router as example_router
from routes.data import router as data_router
from routes.recommendations import router as recommendations_router
from routes.recommendations_guarded import router as recommendations_guarded_router
from routes.career_switch import router as career_switch_router
from routes.outlook import router as outlook_router
from routes.intake import router as intake_router
from routes.paths import router as paths_router
from routes.certs import router as certs_router
from routes.resume import router as resume_router
from routes.coach import router as coach_router
from routes.feedback_routes import router as feedback_router

# main API router
api_router = APIRouter()

# including route modules
api_router.include_router(example_router, prefix="/example", tags=["example"])
api_router.include_router(data_router, prefix="/data", tags=["data"])
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(recommendations_guarded_router, prefix="/recommendations-guarded", tags=["recommendations-guarded"])
api_router.include_router(career_switch_router, prefix="/career-switch", tags=["career-switch"])
api_router.include_router(outlook_router, prefix="/outlook", tags=["outlook"])
api_router.include_router(intake_router, prefix="/intake", tags=["intake"])
api_router.include_router(paths_router, prefix="/paths", tags=["paths"])
api_router.include_router(certs_router, prefix="/certs", tags=["certs"])
api_router.include_router(resume_router, prefix="/resume", tags=["resume"])
api_router.include_router(coach_router, prefix="/coach", tags=["coach"])
api_router.include_router(feedback_router)  # Feedback routes (already have /api/feedback prefix)

# add more routers here as you create them

