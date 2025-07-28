from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
from geopy.distance import geodesic
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = "rideshare_secret_key_2025"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# Security
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="RideShare API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class UserBase(BaseModel):
    email: str
    name: str
    phone: str
    user_type: str  # "driver" or "rider"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: str
    user_type: str
    token: str

class DriverProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    per_km_rate: float
    vehicle_type: str
    vehicle_number: str
    license_number: str
    is_available: bool = True
    current_location: Optional[Dict[str, float]] = None  # {"lat": float, "lng": float}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DriverProfileCreate(BaseModel):
    per_km_rate: float
    vehicle_type: str
    vehicle_number: str
    license_number: str

class DriverLocationUpdate(BaseModel):
    lat: float
    lng: float

class RideRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rider_id: str
    pickup_location: Dict[str, Any]  # {"lat": float, "lng": float, "address": str}
    drop_location: Dict[str, Any]   # {"lat": float, "lng": float, "address": str}
    estimated_distance: float  # in km
    estimated_fare: float
    status: str = "requested"  # requested, accepted, in_progress, completed, cancelled
    driver_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class RideRequestCreate(BaseModel):
    pickup_location: Dict[str, Any]
    drop_location: Dict[str, Any]
    estimated_distance: float
    estimated_fare: float

class RideResponse(BaseModel):
    id: str
    rider_id: str
    pickup_location: Dict[str, Any]
    drop_location: Dict[str, Any]
    estimated_distance: float
    estimated_fare: float
    status: str
    driver_id: Optional[str] = None
    driver_info: Optional[Dict[str, Any]] = None
    created_at: datetime

# Utility Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, user_type: str) -> str:
    payload = {
        "user_id": user_id,
        "user_type": user_type,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user_type = payload.get("user_type")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return {**user, "user_type": user_type}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def calculate_distance(loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
    """Calculate distance between two locations in kilometers"""
    return geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers

# Auth Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user = User(**user_data.dict(exclude={"password"}))
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create JWT token
    token = create_jwt_token(user.id, user.user_type)
    
    return UserResponse(**user.dict(), token=token)

@api_router.post("/auth/login", response_model=UserResponse)
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["id"], user["user_type"])
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        phone=user["phone"],
        user_type=user["user_type"],
        token=token
    )

# Driver Routes
@api_router.post("/driver/profile")
async def create_driver_profile(
    profile_data: DriverProfileCreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can create driver profiles")
    
    # Check if driver profile already exists
    existing_profile = await db.driver_profiles.find_one({"user_id": current_user["id"]})
    if existing_profile:
        raise HTTPException(status_code=400, detail="Driver profile already exists")
    
    profile = DriverProfile(**profile_data.dict(), user_id=current_user["id"])
    await db.driver_profiles.insert_one(profile.dict())
    
    return {"message": "Driver profile created successfully", "profile": profile.dict()}

@api_router.get("/driver/profile")
async def get_driver_profile(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can access driver profiles")
    
    profile = await db.driver_profiles.find_one({"user_id": current_user["id"]})
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    
    return profile

@api_router.put("/driver/location")
async def update_driver_location(
    location: DriverLocationUpdate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can update location")
    
    result = await db.driver_profiles.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"current_location": {"lat": location.lat, "lng": location.lng}}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    
    return {"message": "Location updated successfully"}

@api_router.put("/driver/availability/{is_available}")
async def update_driver_availability(
    is_available: bool,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can update availability")
    
    result = await db.driver_profiles.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"is_available": is_available}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    
    return {"message": f"Availability updated to {'available' if is_available else 'unavailable'}"}

@api_router.get("/driver/ride-requests")
async def get_ride_requests_for_driver(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can view ride requests")
    
    # Get driver's current location
    driver_profile = await db.driver_profiles.find_one({"user_id": current_user["id"]})
    if not driver_profile or not driver_profile.get("current_location"):
        raise HTTPException(status_code=400, detail="Driver location not set")
    
    # Find nearby ride requests within 10km radius
    ride_requests = await db.ride_requests.find({"status": "requested"}).to_list(100)
    nearby_requests = []
    
    for request in ride_requests:
        distance = calculate_distance(
            driver_profile["current_location"],
            request["pickup_location"]
        )
        if distance <= 10:  # Within 10km
            request["distance_to_pickup"] = round(distance, 2)
            nearby_requests.append(request)
    
    # Sort by distance
    nearby_requests.sort(key=lambda x: x["distance_to_pickup"])
    
    return nearby_requests

@api_router.post("/driver/accept-ride/{ride_id}")
async def accept_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can accept rides")
    
    # Check if ride exists and is available
    ride = await db.ride_requests.find_one({"id": ride_id, "status": "requested"})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride request not found or already accepted")
    
    # Update ride with driver info
    result = await db.ride_requests.update_one(
        {"id": ride_id, "status": "requested"},
        {
            "$set": {
                "driver_id": current_user["id"],
                "status": "accepted",
                "accepted_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=400, detail="Failed to accept ride")
    
    return {"message": "Ride accepted successfully"}

# Rider Routes
@api_router.post("/rider/request-ride", response_model=RideResponse)
async def request_ride(
    ride_data: RideRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can request rides")
    
    ride = RideRequest(**ride_data.dict(), rider_id=current_user["id"])
    await db.ride_requests.insert_one(ride.dict())
    
    return RideResponse(**ride.dict())

@api_router.get("/rider/rides")
async def get_rider_rides(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can view their rides")
    
    rides = await db.ride_requests.find({"rider_id": current_user["id"]}).sort("created_at", -1).to_list(50)
    
    # Add driver info for accepted rides
    for ride in rides:
        if ride.get("driver_id"):
            driver_user = await db.users.find_one({"id": ride["driver_id"]})
            driver_profile = await db.driver_profiles.find_one({"user_id": ride["driver_id"]})
            
            if driver_user and driver_profile:
                ride["driver_info"] = {
                    "name": driver_user["name"],
                    "phone": driver_user["phone"],
                    "vehicle_type": driver_profile["vehicle_type"],
                    "vehicle_number": driver_profile["vehicle_number"]
                }
    
    return rides

@api_router.get("/rider/available-drivers")
async def get_available_drivers(
    lat: float,
    lng: float,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can view available drivers")
    
    # Find available drivers within 10km radius
    drivers = await db.driver_profiles.find({
        "is_available": True,
        "current_location": {"$exists": True, "$ne": None}
    }).to_list(100)
    
    nearby_drivers = []
    rider_location = {"lat": lat, "lng": lng}
    
    for driver in drivers:
        if driver.get("current_location"):
            distance = calculate_distance(rider_location, driver["current_location"])
            if distance <= 10:  # Within 10km
                driver_user = await db.users.find_one({"id": driver["user_id"]})
                if driver_user:
                    nearby_drivers.append({
                        "driver_id": driver["user_id"],
                        "name": driver_user["name"],
                        "vehicle_type": driver["vehicle_type"],
                        "per_km_rate": driver["per_km_rate"],
                        "distance": round(distance, 2),
                        "current_location": driver["current_location"]
                    })
    
    # Sort by distance
    nearby_drivers.sort(key=lambda x: x["distance"])
    
    return nearby_drivers

# General Routes
@api_router.get("/")
async def root():
    return {"message": "RideShare API is running!"}

@api_router.get("/maps-config")
async def get_maps_config():
    return {"google_maps_api_key": os.environ.get('GOOGLE_MAPS_API_KEY')}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
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