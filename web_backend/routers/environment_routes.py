"""环境管理 —— CRUD + 健康探测"""
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import list_environments, get_environment, create_environment, update_environment, delete_environment

router = APIRouter()


class EnvRequest(BaseModel):
    name: str
    base_url: str
    description: str = ""


@router.get("")
async def list_envs():
    return {"code": 200, "message": "success", "data": {"environments": list_environments()}}


@router.post("")
async def create_env(req: EnvRequest):
    env_id = create_environment(req.name, req.base_url, req.description)
    return {"code": 200, "message": "已创建", "data": {"id": env_id}}


@router.put("/{env_id}")
async def update_env(env_id: int, req: EnvRequest):
    if not get_environment(env_id):
        raise HTTPException(status_code=404, detail="环境不存在")
    update_environment(env_id, name=req.name, base_url=req.base_url, description=req.description)
    return {"code": 200, "message": "已更新", "data": None}


@router.delete("/{env_id}")
async def delete_env(env_id: int):
    if not get_environment(env_id):
        raise HTTPException(status_code=404, detail="环境不存在")
    delete_environment(env_id)
    return {"code": 200, "message": "已删除", "data": None}


@router.post("/{env_id}/ping")
async def ping_env(env_id: int):
    """健康探测：ping 目标环境的 base URL"""
    env = get_environment(env_id)
    if not env:
        raise HTTPException(status_code=404, detail="环境不存在")

    try:
        resp = requests.get(env["base_url"], timeout=5)
        alive = resp.status_code < 500
        return {
            "code": 200, "message": "success",
            "data": {"alive": alive, "status_code": resp.status_code, "elapsed_ms": round(resp.elapsed.total_seconds() * 1000)},
        }
    except Exception as e:
        return {"code": 200, "message": "success", "data": {"alive": False, "error": str(e)}}
