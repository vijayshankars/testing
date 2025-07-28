from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
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
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import razorpay
import hmac
import hashlib
from twilio.rest import Client
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Initialize Stripe
stripe_api_key = os.environ.get('STRIPE_API_KEY')
if not stripe_api_key:
    logging.warning("STRIPE_API_KEY not found in environment variables")
    stripe_checkout = None
else:
    stripe_checkout = None  # Will be initialized per request

# Initialize Razorpay
razorpay_key_id = os.environ.get('RAZORPAY_KEY_ID')
razorpay_key_secret = os.environ.get('RAZORPAY_KEY_SECRET')
razorpay_webhook_secret = os.environ.get('RAZORPAY_WEBHOOK_SECRET')

if razorpay_key_id and razorpay_key_secret:
    razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
else:
    logging.warning("Razorpay credentials not found in environment variables")
    razorpay_client = None

# Initialize Twilio
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_verify_service = os.environ.get('TWILIO_VERIFY_SERVICE')

if twilio_account_sid and twilio_auth_token:
    # For demo mode, we'll simulate Twilio functionality
    if twilio_account_sid.startswith('AC_demo'):
        twilio_client = None  # Demo mode
        logging.info("Running in Twilio demo mode")
    else:
        twilio_client = Client(twilio_account_sid, twilio_auth_token)
        logging.info("Twilio initialized successfully")
else:
    logging.warning("Twilio credentials not found in environment variables")
    twilio_client = None

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
    license_document: Optional[Dict[str, Any]] = None  # Store document info
    registration_document: Optional[Dict[str, Any]] = None  # Store document info
    is_available: bool = True
    current_location: Optional[Dict[str, float]] = None  # {"lat": float, "lng": float}
    document_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DriverProfileCreate(BaseModel):
    per_km_rate: float
    vehicle_type: str
    vehicle_number: str
    license_number: str
    license_document: Optional[Dict[str, Any]] = None
    registration_document: Optional[Dict[str, Any]] = None

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

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ride_id: str
    rider_id: str
    driver_id: Optional[str] = None
    amount: float
    currency: str = "inr"
    session_id: Optional[str] = None
    payment_id: Optional[str] = None
    payment_status: str = "pending"  # pending, paid, failed, cancelled
    status: str = "initiated"  # initiated, processing, completed, failed
    stripe_session_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentRequest(BaseModel):
    ride_id: str
    origin_url: str

class PaymentStatusResponse(BaseModel):
    payment_id: str
    status: str
    payment_status: str
    amount: float
    currency: str
    ride_info: Optional[Dict[str, Any]] = None

class RazorpayOrderRequest(BaseModel):
    ride_id: str

class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str
    ride_info: Dict[str, Any]

class RazorpayPaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

# OTP Authentication Models
class PhoneNumberRequest(BaseModel):
    phone_number: str
    user_type: str  # "driver" or "rider"

class OTPVerificationRequest(BaseModel):
    phone_number: str
    otp_code: str
    user_type: str
    name: Optional[str] = None  # For new user registration

class OTPSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone_number: str
    user_type: str
    otp_code: str
    is_verified: bool = False
    attempts: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_data: Optional[Dict[str, Any]] = None
    token: Optional[str] = None
    is_new_user: bool = False

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
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def calculate_distance(loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
    """Calculate distance between two locations in kilometers"""
    return geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers

def validate_document(document_data: Dict[str, Any]) -> bool:
    """Validate uploaded document"""
    if not document_data:
        return False
    
    required_fields = ['name', 'type', 'size', 'data']
    if not all(field in document_data for field in required_fields):
        return False
    
    # Check file type
    allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
    if document_data['type'] not in allowed_types:
        return False
    
    # Check file size (5MB limit)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if document_data['size'] > max_size:
        return False
    
    return True

def process_document(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process and store document data"""
    if not validate_document(document_data):
        return None
    
    # Store document metadata (without the actual base64 data for logging)
    processed_doc = {
        'name': document_data['name'],
        'type': document_data['type'],
        'size': document_data['size'],
        'uploaded_at': datetime.utcnow().isoformat(),
        'data': document_data['data']  # Store base64 data
    }
    
    return processed_doc

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
    
    # Validate and process documents
    license_doc = None
    registration_doc = None
    
    if profile_data.license_document:
        license_doc = process_document(profile_data.license_document)
        if not license_doc:
            raise HTTPException(status_code=400, detail="Invalid license document. Please ensure it's a JPG, PNG, or PDF file under 5MB.")
    
    if profile_data.registration_document:
        registration_doc = process_document(profile_data.registration_document)
        if not registration_doc:
            raise HTTPException(status_code=400, detail="Invalid registration document. Please ensure it's a JPG, PNG, or PDF file under 5MB.")
    
    # Create profile with documents
    profile_dict = profile_data.dict()
    profile_dict["user_id"] = current_user["id"]
    profile_dict["license_document"] = license_doc
    profile_dict["registration_document"] = registration_doc
    profile_dict["document_verified"] = False  # Will be verified manually
    
    profile = DriverProfile(**profile_dict)
    await db.driver_profiles.insert_one(profile.dict())
    
    response_data = profile.dict()
    # Remove document data from response for security
    if response_data.get("license_document"):
        response_data["license_document"] = {
            k: v for k, v in response_data["license_document"].items() 
            if k != "data"
        }
    if response_data.get("registration_document"):
        response_data["registration_document"] = {
            k: v for k, v in response_data["registration_document"].items() 
            if k != "data"
        }
    
    return {
        "message": "Driver profile created successfully. Documents will be verified within 24 hours.", 
        "profile": response_data
    }

@api_router.get("/driver/profile")
async def get_driver_profile(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can access driver profiles")
    
    profile = await db.driver_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
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
    driver_profile = await db.driver_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not driver_profile or not driver_profile.get("current_location"):
        raise HTTPException(status_code=400, detail="Driver location not set")
    
    # Find nearby ride requests within 10km radius
    ride_requests = await db.ride_requests.find({"status": "requested"}, {"_id": 0}).to_list(100)
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
    
    rides = await db.ride_requests.find({"rider_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    # Add driver info for accepted rides
    for ride in rides:
        if ride.get("driver_id"):
            driver_user = await db.users.find_one({"id": ride["driver_id"]}, {"_id": 0})
            driver_profile = await db.driver_profiles.find_one({"user_id": ride["driver_id"]}, {"_id": 0})
            
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
    }, {"_id": 0}).to_list(100)
    
    nearby_drivers = []
    rider_location = {"lat": lat, "lng": lng}
    
    for driver in drivers:
        if driver.get("current_location"):
            distance = calculate_distance(rider_location, driver["current_location"])
            if distance <= 10:  # Within 10km
                driver_user = await db.users.find_one({"id": driver["user_id"]}, {"_id": 0})
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

# Payment Routes - Razorpay UPI Integration
@api_router.post("/payment/razorpay/create-order", response_model=RazorpayOrderResponse)
async def create_razorpay_order(
    order_request: RazorpayOrderRequest,
    current_user: dict = Depends(get_current_user)
):
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Razorpay not configured")
    
    # Get ride details
    ride = await db.ride_requests.find_one({"id": order_request.ride_id}, {"_id": 0})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Verify user is the rider for this ride
    if ride["rider_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized to pay for this ride")
    
    # Check if ride is accepted (has driver)
    if not ride.get("driver_id") or ride.get("status") != "accepted":
        raise HTTPException(status_code=400, detail="Ride must be accepted by driver before payment")
    
    # Convert fare to paise (multiply by 100)
    amount_paise = int(ride["estimated_fare"] * 100)
    
    # Create Razorpay order
    try:
        razorpay_order = razorpay_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "ride_id": ride["id"],
                "rider_id": current_user["id"],
                "driver_id": ride["driver_id"]
            }
        })
        
        # Create payment transaction record
        payment_transaction = PaymentTransaction(
            ride_id=ride["id"],
            rider_id=current_user["id"],
            driver_id=ride["driver_id"],
            amount=ride["estimated_fare"],
            currency="INR",
            session_id=razorpay_order["id"],
            payment_status="pending",
            status="initiated",
            metadata={
                "payment_method": "razorpay_upi",
                "razorpay_order_id": razorpay_order["id"]
            }
        )
        
        await db.payment_transactions.insert_one(payment_transaction.dict())
        
        # Get driver info for payment
        driver_user = await db.users.find_one({"id": ride["driver_id"]}, {"_id": 0})
        
        return RazorpayOrderResponse(
            order_id=razorpay_order["id"],
            amount=amount_paise,
            currency="INR",
            key_id=razorpay_key_id,
            ride_info={
                "ride_id": ride["id"],
                "pickup": ride["pickup_location"]["address"],
                "drop": ride["drop_location"]["address"],
                "fare": ride["estimated_fare"],
                "driver_name": driver_user["name"] if driver_user else "Unknown",
                "distance": ride["estimated_distance"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")

@api_router.post("/payment/razorpay/verify")
async def verify_razorpay_payment(
    verification: RazorpayPaymentVerification,
    current_user: dict = Depends(get_current_user)
):
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Razorpay not configured")
    
    # Verify payment signature
    try:
        params_dict = {
            'razorpay_order_id': verification.razorpay_order_id,
            'razorpay_payment_id': verification.razorpay_payment_id,
            'razorpay_signature': verification.razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Update payment transaction
        payment_update = await db.payment_transactions.update_one(
            {"session_id": verification.razorpay_order_id, "rider_id": current_user["id"]},
            {
                "$set": {
                    "payment_id": verification.razorpay_payment_id,
                    "payment_status": "paid",
                    "status": "completed",
                    "updated_at": datetime.utcnow(),
                    "metadata.razorpay_payment_id": verification.razorpay_payment_id,
                    "metadata.signature_verified": True
                }
            }
        )
        
        if payment_update.matched_count == 0:
            raise HTTPException(status_code=404, detail="Payment transaction not found")
        
        # Update ride status to in_progress
        await db.ride_requests.update_one(
            {"id": (await db.payment_transactions.find_one({"session_id": verification.razorpay_order_id}))["ride_id"]},
            {"$set": {"status": "in_progress", "payment_status": "paid"}}
        )
        
        return {"status": "success", "message": "Payment verified successfully"}
        
    except razorpay.errors.SignatureVerificationError:
        # Update payment as failed
        await db.payment_transactions.update_one(
            {"session_id": verification.razorpay_order_id, "rider_id": current_user["id"]},
            {
                "$set": {
                    "payment_status": "failed",
                    "status": "failed",
                    "updated_at": datetime.utcnow(),
                    "metadata.signature_verified": False
                }
            }
        )
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        raise HTTPException(status_code=500, detail="Payment verification failed")

@api_router.get("/payment/status/{ride_id}")
async def get_payment_status(
    ride_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Get payment transaction
    payment = await db.payment_transactions.find_one(
        {"ride_id": ride_id, "rider_id": current_user["id"]}, 
        {"_id": 0}
    )
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Get ride info
    ride = await db.ride_requests.find_one({"id": ride_id}, {"_id": 0})
    
    return PaymentStatusResponse(
        payment_id=payment.get("payment_id", payment["id"]),
        status=payment["status"],
        payment_status=payment["payment_status"],
        amount=payment["amount"],
        currency=payment["currency"],
        ride_info={
            "pickup": ride["pickup_location"]["address"] if ride else "Unknown",
            "drop": ride["drop_location"]["address"] if ride else "Unknown",
            "ride_status": ride["status"] if ride else "Unknown"
        }
    )

@api_router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhook events"""
    if not razorpay_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    try:
        # Get webhook payload and signature
        payload = await request.body()
        signature = request.headers.get('X-Razorpay-Signature', '')
        
        # Verify webhook signature
        expected_signature = hmac.new(
            razorpay_webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        # Process webhook event
        import json
        webhook_data = json.loads(payload.decode())
        
        event = webhook_data.get('event')
        payment_data = webhook_data.get('payload', {}).get('payment', {})
        
        if event == 'payment.captured':
            # Update payment status
            order_id = payment_data.get('order_id')
            payment_id = payment_data.get('id')
            
            if order_id:
                await db.payment_transactions.update_one(
                    {"session_id": order_id},
                    {
                        "$set": {
                            "payment_id": payment_id,
                            "payment_status": "paid",
                            "status": "completed",
                            "updated_at": datetime.utcnow(),
                            "metadata.webhook_processed": True
                        }
                    }
                )
        
        elif event == 'payment.failed':
            # Update payment as failed
            order_id = payment_data.get('order_id')
            
            if order_id:
                await db.payment_transactions.update_one(
                    {"session_id": order_id},
                    {
                        "$set": {
                            "payment_status": "failed",
                            "status": "failed",
                            "updated_at": datetime.utcnow(),
                            "metadata.webhook_processed": True
                        }
                    }
                )
        
        return {"status": "processed"}
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for invalid signature)
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

# General Routes
@api_router.get("/")
async def root():
    return {"message": "RideShare API is running!"}

@api_router.get("/maps-config")
async def get_maps_config():
    return {"google_maps_api_key": os.environ.get('GOOGLE_MAPS_API_KEY')}

@api_router.get("/payment-config")
async def get_payment_config():
    return {
        "razorpay_key_id": razorpay_key_id if razorpay_key_id else None,
        "stripe_enabled": bool(stripe_api_key),
        "razorpay_enabled": bool(razorpay_key_id and razorpay_key_secret)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()