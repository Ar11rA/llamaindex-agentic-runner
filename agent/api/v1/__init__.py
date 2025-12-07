from fastapi import APIRouter

from api.v1.agent_controller import router as agent_router
from api.v1.team_controller import router as team_router
from api.v1.flow_controller import router as flow_router

router = APIRouter(prefix="/v1")
router.include_router(agent_router)
router.include_router(team_router)
router.include_router(flow_router)

__all__ = ["router"]
