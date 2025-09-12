from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Cookie
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Aura Virtual Trucking Company API")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="aura-trucking-secret-key-2024")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    DRIVER = "driver"
    MANAGER = "manager" 
    ADMIN = "admin"

class JobStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class EventType(str, Enum):
    CONVOY = "convoy"
    MEETING = "meeting"
    TRAINING = "training"
    COMPETITION = "competition"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    role: UserRole = UserRole.DRIVER
    truckers_mp_id: Optional[str] = None
    steam_id: Optional[str] = None
    experience_points: int = 0
    total_distance: float = 0.0
    total_deliveries: int = 0
    join_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class UserCreate(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None
    truckers_mp_id: Optional[str] = None
    steam_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    truckers_mp_id: Optional[str] = None
    steam_id: Optional[str] = None
    role: Optional[UserRole] = None

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    cargo: str
    origin_city: str
    destination_city: str
    distance: float
    reward: int
    difficulty: str  # Easy, Medium, Hard
    status: JobStatus = JobStatus.AVAILABLE
    assigned_driver_id: Optional[str] = None
    assigned_driver_name: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None

class JobCreate(BaseModel):
    title: str
    description: str
    cargo: str
    origin_city: str
    destination_city: str
    distance: float
    reward: int
    difficulty: str
    deadline: Optional[datetime] = None

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    event_type: EventType
    date_time: datetime
    location: str
    max_participants: Optional[int] = None
    participants: List[str] = []  # user IDs
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class EventCreate(BaseModel):
    title: str
    description: str
    event_type: EventType
    date_time: datetime
    location: str
    max_participants: Optional[int] = None

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyStats(BaseModel):
    total_drivers: int
    total_deliveries: int
    total_distance: float
    active_drivers: int
    pending_jobs: int
    upcoming_events: int

# Helper functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

async def get_current_user(session_token: Optional[str] = Cookie(None), authorization: Optional[str] = None) -> Optional[User]:
    """Get current user from session token (cookie or header)"""
    token = None
    
    if session_token:
        token = session_token
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    
    if not token:
        return None
        
    # Check session in database
    session = await db.sessions.find_one({"session_token": token})
    if not session or datetime.fromisoformat(session["expires_at"]) < datetime.now(timezone.utc):
        return None
        
    # Get user
    user_data = await db.users.find_one({"id": session["user_id"]})
    if not user_data:
        return None
        
    return User(**user_data)

async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require authentication"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user

async def require_role(allowed_roles: List[UserRole]):
    """Create dependency to require specific roles"""
    async def role_checker(current_user: User = Depends(require_auth)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Auth endpoints
@api_router.post("/auth/process-session")
async def process_session(request: Request, response: Response):
    """Process session ID from Emergent auth"""
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Get user data from Emergent auth
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            auth_response.raise_for_status()
            user_data = auth_response.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data["email"]})
    
    if existing_user:
        user = User(**existing_user)
        # Update last active
        await db.users.update_one(
            {"id": user.id},
            {"$set": {"last_active": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        # Create new user
        user = User(
            email=user_data["email"],
            name=user_data["name"],
            picture=user_data.get("picture"),
            role=UserRole.DRIVER
        )
        user_dict = prepare_for_mongo(user.dict())
        await db.users.insert_one(user_dict)
    
    # Create session
    session_token = user_data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session = Session(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at
    )
    session_dict = prepare_for_mongo(session.dict())
    await db.sessions.insert_one(session_dict)
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return {"user": user, "message": "Authentication successful"}

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(require_auth)):
    """Get current user information"""
    return current_user

@api_router.post("/auth/logout")
async def logout(response: Response, current_user: User = Depends(require_auth)):
    """Logout user"""
    # Delete session from database
    await db.sessions.delete_many({"user_id": current_user.id})
    
    # Clear cookie
    response.delete_cookie("session_token", samesite="none", secure=True)
    
    return {"message": "Logged out successfully"}

# User management endpoints
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(require_role([UserRole.MANAGER, UserRole.ADMIN]))):
    """Get all users (managers and admins only)"""
    users = await db.users.find({"is_active": True}).to_list(length=None)
    return [User(**user) for user in users]

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: User = Depends(require_auth)):
    """Get user by ID"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate, current_user: User = Depends(require_auth)):
    """Update user"""
    # Check permissions
    if current_user.id != user_id and current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Only admins can change roles
    if user_update.role and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can change user roles")
    
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"id": user_id})
    return User(**updated_user)

# Job management endpoints
@api_router.get("/jobs", response_model=List[Job])
async def get_jobs(status: Optional[JobStatus] = None, current_user: User = Depends(require_auth)):
    """Get all jobs"""
    filter_dict = {}
    if status:
        filter_dict["status"] = status
    
    jobs = await db.jobs.find(filter_dict).to_list(length=None)
    return [Job(**job) for job in jobs]

@api_router.post("/jobs", response_model=Job)
async def create_job(job_create: JobCreate, current_user: User = Depends(require_role([UserRole.MANAGER, UserRole.ADMIN]))):
    """Create new job (managers and admins only)"""
    job = Job(
        **job_create.dict(),
        created_by=current_user.id
    )
    job_dict = prepare_for_mongo(job.dict())
    await db.jobs.insert_one(job_dict)
    return job

@api_router.post("/jobs/{job_id}/assign/{driver_id}")
async def assign_job(job_id: str, driver_id: str, current_user: User = Depends(require_role([UserRole.MANAGER, UserRole.ADMIN]))):
    """Assign job to driver"""
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != JobStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Job is not available")
    
    driver = await db.users.find_one({"id": driver_id})
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    await db.jobs.update_one(
        {"id": job_id},
        {"$set": {
            "status": JobStatus.ASSIGNED,
            "assigned_driver_id": driver_id,
            "assigned_driver_name": driver["name"],
            "assigned_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Job assigned successfully"}

@api_router.post("/jobs/{job_id}/complete")
async def complete_job(job_id: str, current_user: User = Depends(require_auth)):
    """Complete job (driver or manager/admin)"""
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user can complete this job
    if job["assigned_driver_id"] != current_user.id and current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="You can only complete your own jobs")
    
    if job["status"] not in [JobStatus.ASSIGNED, JobStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="Job cannot be completed")
    
    # Update job
    await db.jobs.update_one(
        {"id": job_id},
        {"$set": {
            "status": JobStatus.DELIVERED,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update driver stats
    if job["assigned_driver_id"]:
        await db.users.update_one(
            {"id": job["assigned_driver_id"]},
            {"$inc": {
                "total_deliveries": 1,
                "total_distance": job["distance"],
                "experience_points": job["reward"]
            }}
        )
    
    return {"message": "Job completed successfully"}

# Event management endpoints
@api_router.get("/events", response_model=List[Event])
async def get_events(current_user: User = Depends(require_auth)):
    """Get all events"""
    events = await db.events.find({"is_active": True}).to_list(length=None)
    return [Event(**event) for event in events]

@api_router.post("/events", response_model=Event)
async def create_event(event_create: EventCreate, current_user: User = Depends(require_role([UserRole.MANAGER, UserRole.ADMIN]))):
    """Create new event"""
    event = Event(
        **event_create.dict(),
        created_by=current_user.id
    )
    event_dict = prepare_for_mongo(event.dict())
    await db.events.insert_one(event_dict)
    return event

@api_router.post("/events/{event_id}/join")
async def join_event(event_id: str, current_user: User = Depends(require_auth)):
    """Join event"""
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if current_user.id in event.get("participants", []):
        raise HTTPException(status_code=400, detail="Already joined this event")
    
    if event.get("max_participants") and len(event.get("participants", [])) >= event["max_participants"]:
        raise HTTPException(status_code=400, detail="Event is full")
    
    await db.events.update_one(
        {"id": event_id},
        {"$push": {"participants": current_user.id}}
    )
    
    return {"message": "Joined event successfully"}

# Company stats endpoint
@api_router.get("/company/stats", response_model=CompanyStats)
async def get_company_stats(current_user: User = Depends(require_auth)):
    """Get company statistics"""
    total_drivers = await db.users.count_documents({"is_active": True})
    active_drivers = await db.users.count_documents({
        "is_active": True,
        "last_active": {"$gte": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()}
    })
    
    # Aggregate total deliveries and distance
    pipeline = [
        {"$group": {
            "_id": None,
            "total_deliveries": {"$sum": "$total_deliveries"},
            "total_distance": {"$sum": "$total_distance"}
        }}
    ]
    stats_result = await db.users.aggregate(pipeline).to_list(1)
    total_deliveries = stats_result[0]["total_deliveries"] if stats_result else 0
    total_distance = stats_result[0]["total_distance"] if stats_result else 0
    
    pending_jobs = await db.jobs.count_documents({"status": {"$in": [JobStatus.AVAILABLE, JobStatus.ASSIGNED]}})
    upcoming_events = await db.events.count_documents({
        "is_active": True,
        "date_time": {"$gte": datetime.now(timezone.utc).isoformat()}
    })
    
    return CompanyStats(
        total_drivers=total_drivers,
        total_deliveries=total_deliveries,
        total_distance=total_distance,
        active_drivers=active_drivers,
        pending_jobs=pending_jobs,
        upcoming_events=upcoming_events
    )

# Basic endpoints
@api_router.get("/")
async def root():
    return {"message": "Aura Virtual Trucking Company API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()