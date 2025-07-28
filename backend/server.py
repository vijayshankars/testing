from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
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
    vehicle_type: str
    vehicle_number: str
    license_number: str
    license_document: Optional[Dict[str, Any]] = None
    registration_document: Optional[Dict[str, Any]] = None

class LicenseVerificationRequest(BaseModel):
    license_number: str

class VehicleVerificationRequest(BaseModel):
    vehicle_number: str
    vehicle_type: Optional[str] = None

class DiscountCode(BaseModel):
    code: str
    discount_type: str  # 'percentage', 'fixed_amount', 'first_ride'
    discount_value: float
    min_fare_amount: Optional[float] = 0
    max_discount_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ApplyDiscountRequest(BaseModel):
    promo_code: str
    ride_fare: float

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
    ride_otp: Optional[str] = None  # 4-digit OTP for ride verification
    otp_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None  # When OTP is verified
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

class RideRequestCreate(BaseModel):
    pickup_location: Dict[str, Any]
    drop_location: Dict[str, Any]
    estimated_distance: float
    estimated_fare: float
    promo_code: Optional[str] = None

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

class AdminDashboardData(BaseModel):
    total_users: int
    total_drivers: int
    total_riders: int
    total_rides: int
    active_rides: int
    pending_verifications: int
    recent_users: List[Dict[str, Any]]
    recent_rides: List[Dict[str, Any]]

class UserManagementAction(BaseModel):
    user_id: str
    action: str  # "activate", "deactivate", "verify_driver", "reject_driver"

class RideCancellationRequest(BaseModel):
    ride_id: str
    reason: Optional[str] = "User cancelled"

class RideOTPVerification(BaseModel):
    ride_id: str
    otp_code: str

class RideStatusUpdate(BaseModel):
    ride_id: str
    status: str  # "completed"
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

def validate_phone_number(phone: str) -> str:
    """Validate and format phone number to E.164 format"""
    # Remove all non-digit characters except +
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Basic validation - must have some digits
    if not re.search(r'\d', clean_phone):
        raise ValueError("Invalid phone number format")
    
    # If doesn't start with +, assume it's Indian number
    if not clean_phone.startswith('+'):
        if clean_phone.startswith('91') and len(clean_phone) == 12:
            clean_phone = '+' + clean_phone
        elif len(clean_phone) == 10:
            clean_phone = '+91' + clean_phone
        else:
            # Invalid format for auto-formatting
            raise ValueError("Invalid phone number format")
    
    # Validate the format - must be E.164 format
    if not re.match(r'^\+[1-9]\d{1,14}$', clean_phone):
        raise ValueError("Invalid phone number format")
    
    # Additional validation - minimum length check
    if len(clean_phone) < 8:  # Minimum reasonable phone number length
        raise ValueError("Invalid phone number format")
    
    return clean_phone

def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    import random
    return str(random.randint(100000, 999999))

def generate_ride_otp() -> str:
    """Generate a 4-digit ride verification OTP"""
    import random
    return str(random.randint(1000, 9999))

async def send_otp_via_twilio(phone_number: str) -> Dict[str, Any]:
    """Send OTP via Twilio or simulate in demo mode"""
    if twilio_client and twilio_verify_service and not twilio_account_sid.startswith('AC_demo'):
        try:
            verification = twilio_client.verify.services(twilio_verify_service)\
                .verifications.create(to=phone_number, channel="sms")
            return {"status": "sent", "service": "twilio", "sid": verification.sid}
        except Exception as e:
            logger.error(f"Twilio error: {e}")
            # Fall back to demo mode
            return {"status": "demo", "service": "demo", "message": "Demo mode - OTP not sent"}
    else:
        # Demo mode - generate and log OTP
        otp = generate_otp()
        logger.info(f"DEMO OTP for {phone_number}: {otp}")
        return {"status": "demo", "service": "demo", "otp": otp, "message": f"Demo OTP: {otp}"}

async def verify_otp_via_twilio(phone_number: str, code: str) -> bool:
    """Verify OTP via Twilio or simulate in demo mode"""
    if twilio_client and twilio_verify_service and not twilio_account_sid.startswith('AC_demo'):
        try:
            check = twilio_client.verify.services(twilio_verify_service)\
                .verification_checks.create(to=phone_number, code=code)
            return check.status == "approved"
        except Exception:
            return False
    else:
        # Demo mode - accept specific demo OTPs
        demo_otps = ["123456", "000000"]  # Demo OTPs for testing
        return code in demo_otps

# OTP Authentication Routes
@api_router.post("/auth/send-otp", response_model=Dict[str, Any])
async def send_otp(request: PhoneNumberRequest):
    try:
        # Validate phone number
        formatted_phone = validate_phone_number(request.phone_number)
        
        # Check if user exists
        existing_user = await db.users.find_one({"phone": formatted_phone})
        
        # Generate OTP session
        otp_code = generate_otp()
        otp_session = OTPSession(
            phone_number=formatted_phone,
            user_type=request.user_type,
            otp_code=otp_code
        )
        
        # Store OTP session
        await db.otp_sessions.insert_one(otp_session.dict())
        
        # Send OTP
        if twilio_account_sid and twilio_account_sid.startswith('AC_demo'):
            # Demo mode
            return {
                "success": True,
                "message": f"Demo OTP sent to {formatted_phone}",
                "demo_otp": otp_code,  # Only for demo
                "is_existing_user": bool(existing_user),
                "demo_mode": True
            }
        else:
            # Real Twilio mode
            sms_result = await send_otp_via_twilio(formatted_phone)
            return {
                "success": True,
                "message": f"OTP sent to {formatted_phone}",
                "is_existing_user": bool(existing_user),
                "demo_mode": False
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@api_router.post("/auth/verify-otp", response_model=AuthResponse)
async def verify_otp(request: OTPVerificationRequest):
    try:
        # Validate phone number
        formatted_phone = validate_phone_number(request.phone_number)
        
        # Find active OTP session
        otp_session = await db.otp_sessions.find_one({
            "phone_number": formatted_phone,
            "user_type": request.user_type,
            "is_verified": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not otp_session:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP session")
        
        # Check attempts limit
        if otp_session["attempts"] >= 3:
            raise HTTPException(status_code=400, detail="Too many OTP attempts. Please request a new OTP.")
        
        # Verify OTP
        is_valid = False
        if twilio_account_sid and twilio_account_sid.startswith('AC_demo'):
            # Demo mode - check against stored OTP first, then fallback to demo OTPs
            if request.otp_code == otp_session["otp_code"]:
                is_valid = True
            else:
                # Also accept standard demo OTPs for testing
                demo_otps = ["123456", "000000"]
                is_valid = request.otp_code in demo_otps
        else:
            # Real Twilio mode
            is_valid = await verify_otp_via_twilio(formatted_phone, request.otp_code)
        
        # Update attempts
        await db.otp_sessions.update_one(
            {"_id": otp_session["_id"]},
            {"$inc": {"attempts": 1}}
        )
        
        if not is_valid:
            return AuthResponse(
                success=False,
                message="Invalid OTP. Please try again."
            )
        
        # Mark OTP as verified
        await db.otp_sessions.update_one(
            {"_id": otp_session["_id"]},
            {"$set": {"is_verified": True}}
        )
        
        # Check if user exists
        existing_user = await db.users.find_one({"phone": formatted_phone})
        
        if existing_user:
            # Existing user login
            # Verify user type matches
            if existing_user["user_type"] != request.user_type:
                raise HTTPException(
                    status_code=400, 
                    detail=f"This number is registered as {existing_user['user_type']}, not {request.user_type}"
                )
            
            # Generate JWT token
            token = create_jwt_token(existing_user["id"], existing_user["user_type"])
            
            return AuthResponse(
                success=True,
                message="Login successful",
                user_data={
                    "id": existing_user["id"],
                    "phone": existing_user["phone"],
                    "name": existing_user["name"],
                    "email": existing_user.get("email", ""),
                    "user_type": existing_user["user_type"]
                },
                token=token,
                is_new_user=False
            )
        
        else:
            # New user registration
            if not request.name or len(request.name.strip()) < 2:
                raise HTTPException(status_code=400, detail="Name is required for new user registration")
            
            # Create new user
            new_user = User(
                phone=formatted_phone,
                email=f"{formatted_phone.replace('+', '')}@rideshare.app",  # Generate email
                name=request.name.strip(),
                user_type=request.user_type
            )
            
            user_dict = new_user.dict()
            user_dict["password"] = hash_password("mobile_auth")  # Dummy password for mobile auth users
            user_dict["is_mobile_verified"] = True
            user_dict["created_via"] = "mobile_otp"
            
            await db.users.insert_one(user_dict)
            
            # Generate JWT token
            token = create_jwt_token(new_user.id, new_user.user_type)
            
            return AuthResponse(
                success=True,
                message="Registration successful",
                user_data={
                    "id": new_user.id,
                    "phone": new_user.phone,
                    "name": new_user.name,
                    "email": new_user.email,
                    "user_type": new_user.user_type
                },
                token=token,
                is_new_user=True
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        raise HTTPException(status_code=500, detail="OTP verification failed")

# Legacy Auth Routes (keep for backward compatibility)
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
    user_dict["created_via"] = "email_password"
    
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
@api_router.post("/driver/verify-license")
async def verify_license_with_vahan(request: LicenseVerificationRequest, current_user: dict = Depends(get_current_user)):
    """Verify driving license with VAHAN system"""
    try:
        # Validate license number format (basic validation)
        license_number = request.license_number.upper().strip()
        
        if not license_number or len(license_number) < 10:
            return {"success": False, "message": "Invalid license number format"}
        
        # For demo purposes, we'll simulate VAHAN verification
        # In production, you would integrate with actual VAHAN API
        # using the VAHAN integration playbook provided earlier
        
        # Simulate different license validation scenarios
        if license_number.startswith("DL"):
            # Valid license simulation
            license_data = {
                "name": "Test Driver Name",
                "dob": "1990-01-15",
                "issue_date": "2018-02-01", 
                "expiry_date": "2038-02-01",
                "address": "123 Test Address, Delhi",
                "status": "VALID"
            }
            
            # Store verification record (optional)
            verification_record = {
                "license_number": license_number,
                "user_id": current_user["id"],
                "verification_status": "VERIFIED",
                "license_data": license_data,
                "verified_at": datetime.utcnow()
            }
            
            # You can store this in a separate collection for audit purposes
            # await db.license_verifications.insert_one(verification_record)
            
            return {
                "success": True,
                "message": "License verified successfully with VAHAN system",
                "license_data": license_data,
                "verification_id": str(ObjectId())
            }
        else:
            return {
                "success": False,
                "message": "License number not found in VAHAN database"
            }
    
    except Exception as e:
        print(f"VAHAN verification error: {str(e)}")
        return {
            "success": False,
            "message": "VAHAN verification service unavailable. Please try again later."
        }

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
    
    # Set default per_km_rate based on vehicle type for backward compatibility
    vehicle_rates = {
        "bike": 5.0,
        "auto": 8.0, 
        "car": 12.0,
        "suv": 15.0
    }
    
    per_km_rate = vehicle_rates.get(profile_data.vehicle_type.lower(), 10.0)
    
    # Create profile with documents
    profile_dict = profile_data.dict()
    profile_dict["user_id"] = current_user["id"]
    profile_dict["per_km_rate"] = per_km_rate  # Auto-assigned based on vehicle type
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
    
    # Find nearby ride requests within 25km radius
    ride_requests = await db.ride_requests.find({"status": "requested"}, {"_id": 0}).to_list(100)
    nearby_requests = []
    
    for request in ride_requests:
        distance = calculate_distance(
            driver_profile["current_location"],
            request["pickup_location"]
        )
        if distance <= 25:  # Increased to 25km for better coverage
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
    
    # Generate ride OTP for verification
    ride_otp = generate_ride_otp()
    
    # Update ride with driver info and OTP
    result = await db.ride_requests.update_one(
        {"id": ride_id, "status": "requested"},
        {
            "$set": {
                "driver_id": current_user["id"],
                "status": "accepted",
                "accepted_at": datetime.utcnow(),
                "ride_otp": ride_otp,
                "otp_verified": False
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=400, detail="Failed to accept ride")
    
    return {
        "message": "Ride accepted successfully", 
        "ride_otp": ride_otp,
        "instructions": "Share the OTP with the rider for verification"
    }

@api_router.post("/driver/verify-ride-otp")
async def verify_ride_otp(
    verification: RideOTPVerification,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can verify ride OTP")
    
    # Find the ride
    ride = await db.ride_requests.find_one({
        "id": verification.ride_id,
        "driver_id": current_user["id"],
        "status": "accepted"
    })
    
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found or not assigned to you")
    
    # Verify OTP
    if ride.get("ride_otp") != verification.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Update ride status to in_progress
    result = await db.ride_requests.update_one(
        {"id": verification.ride_id},
        {
            "$set": {
                "status": "in_progress",
                "otp_verified": True,
                "started_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=400, detail="Failed to start ride")
    
    return {"message": "Ride started successfully", "status": "in_progress"}

@api_router.post("/driver/complete-ride")
async def complete_ride(
    ride_update: RideStatusUpdate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can complete rides")
    
    # Find the ride
    ride = await db.ride_requests.find_one({
        "id": ride_update.ride_id,
        "driver_id": current_user["id"],
        "status": "in_progress"
    })
    
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found or not in progress")
    
    # Update ride status to completed
    result = await db.ride_requests.update_one(
        {"id": ride_update.ride_id},
        {
            "$set": {
                "status": "completed",
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=400, detail="Failed to complete ride")
    
    return {"message": "Ride completed successfully", "status": "completed"}

# Rider Routes
@api_router.post("/rider/cancel-ride")
async def cancel_ride(
    cancellation: RideCancellationRequest,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can cancel their rides")
    
    # Find the ride
    ride = await db.ride_requests.find_one({
        "id": cancellation.ride_id,
        "rider_id": current_user["id"],
        "status": {"$in": ["requested", "accepted"]}
    })
    
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found or cannot be cancelled")
    
    # Update ride status to cancelled
    result = await db.ride_requests.update_one(
        {"id": cancellation.ride_id},
        {
            "$set": {
                "status": "cancelled",
                "cancelled_at": datetime.utcnow(),
                "cancellation_reason": cancellation.reason
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=400, detail="Failed to cancel ride")
    
    return {"message": "Ride cancelled successfully", "status": "cancelled"}

@api_router.get("/rider/ride-history")
async def get_rider_ride_history(
    limit: int = 20,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can view their ride history")
    
    query = {"rider_id": current_user["id"]}
    if status:
        query["status"] = status
    
    rides = await db.ride_requests.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Add driver info for accepted/completed rides
    for ride in rides:
        ride.pop("_id", None)
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
    
    return {"rides": rides, "total": len(rides)}

@api_router.get("/driver/ride-history")
async def get_driver_ride_history(
    limit: int = 20,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can view their ride history")
    
    query = {"driver_id": current_user["id"]}
    if status:
        query["status"] = status
    
    rides = await db.ride_requests.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Add rider info
    for ride in rides:
        ride.pop("_id", None)
        rider_user = await db.users.find_one({"id": ride["rider_id"]})
        if rider_user:
            ride["rider_info"] = {
                "name": rider_user["name"],
                "phone": rider_user["phone"]
            }
    
    return {"rides": rides, "total": len(rides)}
@api_router.post("/rider/request-ride")
async def request_ride(
    ride_data: RideRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    """Request a new ride with optional discount application"""
    if current_user["user_type"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can request rides")
    
    # Calculate final fare (with discount if provided)
    final_fare = ride_data.estimated_fare
    discount_applied = None
    
    if ride_data.promo_code:
        # Apply discount code
        discount_request = ApplyDiscountRequest(
            promo_code=ride_data.promo_code,
            ride_fare=ride_data.estimated_fare
        )
        
        try:
            # Reuse the discount application logic
            discount = await db.discount_codes.find_one({
                "code": ride_data.promo_code.upper(),
                "is_active": True,
                "valid_from": {"$lte": datetime.utcnow()},
                "valid_until": {"$gte": datetime.utcnow()}
            })
            
            if discount:
                # Check minimum fare requirement
                if ride_data.estimated_fare >= discount.get("min_fare_amount", 0):
                    # Check usage limit
                    usage_limit_ok = True
                    if discount.get("usage_limit"):
                        usage_count = await db.discount_usage.count_documents({
                            "discount_code": ride_data.promo_code.upper(),
                            "user_id": current_user["id"]
                        })
                        usage_limit_ok = usage_count < discount["usage_limit"]
                    
                    if usage_limit_ok:
                        # Calculate discount amount
                        discount_amount = 0
                        if discount["discount_type"] == "percentage":
                            discount_amount = (ride_data.estimated_fare * discount["discount_value"]) / 100
                        elif discount["discount_type"] == "fixed_amount":
                            discount_amount = discount["discount_value"]
                        elif discount["discount_type"] == "first_ride":
                            # Check if this is user's first ride
                            first_ride_count = await db.rides.count_documents({
                                "rider_id": current_user["id"],
                                "status": "completed"
                            })
                            if first_ride_count == 0:
                                discount_amount = (ride_data.estimated_fare * discount["discount_value"]) / 100
                        
                        # Apply maximum discount limit
                        if discount.get("max_discount_amount"):
                            discount_amount = min(discount_amount, discount["max_discount_amount"])
                        
                        # Ensure discount doesn't exceed ride fare
                        discount_amount = min(discount_amount, ride_data.estimated_fare)
                        
                        final_fare = ride_data.estimated_fare - discount_amount
                        discount_applied = {
                            "code": discount["code"],
                            "type": discount["discount_type"],
                            "discount_amount": round(discount_amount, 2),
                            "original_fare": ride_data.estimated_fare,
                            "final_fare": round(final_fare, 2)
                        }
        except Exception as e:
            print(f"Discount application during ride request failed: {str(e)}")
            # Continue without discount if there's an error
    
    # Create ride request
    ride_dict = {
        "id": str(uuid.uuid4()),  # Add UUID for ride
        "rider_id": current_user["id"],
        "pickup_location": ride_data.pickup_location,
        "drop_location": ride_data.drop_location,
        "estimated_distance": ride_data.estimated_distance,
        "estimated_fare": ride_data.estimated_fare,
        "final_fare": round(final_fare, 2),
        "promo_code": ride_data.promo_code,
        "discount_applied": discount_applied,
        "status": "requested",
        "created_at": datetime.utcnow(),
        "driver_id": None,
        "driver_info": None,
        "ride_otp": None
    }
    
    result = await db.rides.insert_one(ride_dict)
    
    # Store discount usage if discount was applied
    if discount_applied:
        usage_record = {
            "user_id": current_user["id"],
            "discount_code": ride_data.promo_code.upper(),
            "ride_id": ride_dict["id"],
            "discount_amount": discount_applied["discount_amount"],
            "used_at": datetime.utcnow()
        }
        await db.discount_usage.insert_one(usage_record)
    
    # Remove MongoDB _id from response
    ride_dict.pop("_id", None)
    return ride_dict

@api_router.post("/rider/apply-discount")
async def apply_discount_code(request: ApplyDiscountRequest, current_user: dict = Depends(get_current_user)):
    """Apply discount code to ride fare"""
    try:
        if current_user["user_type"] != "rider":
            raise HTTPException(status_code=403, detail="Only riders can apply discount codes")
        
        # Find the discount code
        discount = await db.discount_codes.find_one({
            "code": request.promo_code.upper(),
            "is_active": True,
            "valid_from": {"$lte": datetime.utcnow()},
            "valid_until": {"$gte": datetime.utcnow()}
        })
        
        if not discount:
            return {
                "success": False,
                "message": "Invalid or expired promo code"
            }
        
        # Check minimum fare requirement
        if request.ride_fare < discount.get("min_fare_amount", 0):
            return {
                "success": False,
                "message": f"Minimum fare of ₹{discount['min_fare_amount']} required for this promo code"
            }
        
        # Check usage limit
        if discount.get("usage_limit"):
            usage_count = await db.discount_usage.count_documents({
                "discount_code": request.promo_code.upper(),
                "user_id": current_user["id"]
            })
            if usage_count >= discount["usage_limit"]:
                return {
                    "success": False,
                    "message": "Promo code usage limit exceeded"
                }
        
        # Calculate discount amount
        discount_amount = 0
        if discount["discount_type"] == "percentage":
            discount_amount = (request.ride_fare * discount["discount_value"]) / 100
        elif discount["discount_type"] == "fixed_amount":
            discount_amount = discount["discount_value"]
        elif discount["discount_type"] == "first_ride":
            # Check if this is user's first ride
            first_ride_count = await db.rides.count_documents({
                "rider_id": current_user["id"],
                "status": "completed"
            })
            if first_ride_count > 0:
                return {
                    "success": False,
                    "message": "First ride discount is only valid for new users"
                }
            discount_amount = (request.ride_fare * discount["discount_value"]) / 100
        
        # Apply maximum discount limit
        if discount.get("max_discount_amount"):
            discount_amount = min(discount_amount, discount["max_discount_amount"])
        
        # Ensure discount doesn't exceed ride fare
        discount_amount = min(discount_amount, request.ride_fare)
        
        final_fare = request.ride_fare - discount_amount
        
        return {
            "success": True,
            "message": "Discount applied successfully!",
            "discount_details": {
                "code": discount["code"],
                "type": discount["discount_type"],
                "original_fare": request.ride_fare,
                "discount_amount": round(discount_amount, 2),
                "final_fare": round(final_fare, 2),
                "savings": round(discount_amount, 2)
            }
        }
        
    except Exception as e:
        print(f"Apply discount error: {str(e)}")
        return {
            "success": False,
            "message": "Failed to apply discount code"
        }

@api_router.get("/rider/available-discounts")
async def get_available_discounts(current_user: dict = Depends(get_current_user)):
    """Get available discount codes for the rider"""
    try:
        if current_user["user_type"] != "rider":
            raise HTTPException(status_code=403, detail="Only riders can view discount codes")
        
        # Get active discount codes
        discounts = await db.discount_codes.find({
            "is_active": True,
            "valid_from": {"$lte": datetime.utcnow()},
            "valid_until": {"$gte": datetime.utcnow()}
        }).to_list(20)
        
        available_discounts = []
        for discount in discounts:
            # Check if user has already used this discount (if usage limit exists)
            can_use = True
            if discount.get("usage_limit"):
                usage_count = await db.discount_usage.count_documents({
                    "discount_code": discount["code"],
                    "user_id": current_user["id"]
                })
                can_use = usage_count < discount["usage_limit"]
            
            if can_use:
                available_discounts.append({
                    "code": discount["code"],
                    "discount_type": discount["discount_type"],
                    "discount_value": discount["discount_value"],
                    "min_fare_amount": discount.get("min_fare_amount", 0),
                    "max_discount_amount": discount.get("max_discount_amount"),
                    "description": discount.get("description", ""),
                    "valid_until": discount["valid_until"].isoformat()
                })
        
        return {
            "success": True,
            "discounts": available_discounts
        }
        
    except Exception as e:
        print(f"Get available discounts error: {str(e)}")
        return {
            "success": False,
            "message": "Failed to fetch available discounts"
        }

# Admin endpoint to create discount codes
@api_router.post("/admin/create-discount")
async def create_discount_code(discount_data: DiscountCode, current_user: dict = Depends(get_current_user)):
    """Create a new discount code (Admin only)"""
    try:
        if current_user["user_type"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can create discount codes")
        
        # Check if discount code already exists
        existing_discount = await db.discount_codes.find_one({"code": discount_data.code.upper()})
        if existing_discount:
            raise HTTPException(status_code=400, detail="Discount code already exists")
        
        # Create discount code
        discount_dict = discount_data.dict()
        discount_dict["code"] = discount_data.code.upper()
        discount_dict["created_by"] = current_user["id"]
        
        result = await db.discount_codes.insert_one(discount_dict)
        
        return {
            "success": True,
            "message": "Discount code created successfully",
            "discount_id": str(result.inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create discount error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create discount code")

@api_router.post("/rider/rides")
async def request_ride_post(
    ride_data: RideRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can request rides")
    
    ride = RideRequest(**ride_data.dict(), rider_id=current_user["id"])
    await db.ride_requests.insert_one(ride.dict())
    
    return RideResponse(**ride.dict())

@api_router.post("/admin/init-sample-discounts")
async def initialize_sample_discounts():
    """Initialize sample discount codes for demo purposes"""
    try:
        # Check if discount codes already exist
        existing_count = await db.discount_codes.count_documents({})
        if existing_count > 0:
            return {"message": "Sample discount codes already exist"}
        
        # Sample discount codes
        sample_discounts = [
            {
                "code": "FIRST20",
                "discount_type": "first_ride",
                "discount_value": 20.0,
                "min_fare_amount": 50.0,
                "max_discount_amount": 100.0,
                "usage_limit": 1,
                "valid_from": datetime.utcnow(),
                "valid_until": datetime.utcnow() + timedelta(days=30),
                "is_active": True,
                "description": "20% off on your first ride",
                "created_at": datetime.utcnow()
            },
            {
                "code": "SAVE10",
                "discount_type": "percentage",
                "discount_value": 10.0,
                "min_fare_amount": 100.0,
                "max_discount_amount": 50.0,
                "usage_limit": 5,
                "valid_from": datetime.utcnow(),
                "valid_until": datetime.utcnow() + timedelta(days=15),
                "is_active": True,
                "description": "10% off up to ₹50",
                "created_at": datetime.utcnow()
            },
            {
                "code": "FLAT50",
                "discount_type": "fixed_amount",
                "discount_value": 50.0,
                "min_fare_amount": 200.0,
                "max_discount_amount": 50.0,
                "usage_limit": 3,
                "valid_from": datetime.utcnow(),
                "valid_until": datetime.utcnow() + timedelta(days=7),
                "is_active": True,
                "description": "Flat ₹50 off on rides above ₹200",
                "created_at": datetime.utcnow()
            },
            {
                "code": "WEEKEND25",
                "discount_type": "percentage",
                "discount_value": 25.0,
                "min_fare_amount": 80.0,
                "max_discount_amount": 75.0,
                "usage_limit": 2,
                "valid_from": datetime.utcnow(),
                "valid_until": datetime.utcnow() + timedelta(days=10),
                "is_active": True,
                "description": "25% off weekend rides",
                "created_at": datetime.utcnow()
            }
        ]
        
        # Insert sample discount codes
        result = await db.discount_codes.insert_many(sample_discounts)
        
        return {
            "message": f"Successfully created {len(result.inserted_ids)} sample discount codes",
            "codes": [discount["code"] for discount in sample_discounts]
        }
        
    except Exception as e:
        print(f"Error initializing sample discounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize sample discounts")

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
    
    # Find available drivers within 25km radius
    drivers = await db.driver_profiles.find({
        "is_available": True,
        "current_location": {"$exists": True, "$ne": None}
    }, {"_id": 0}).to_list(100)
    
    nearby_drivers = []
    rider_location = {"lat": lat, "lng": lng}
    
    for driver in drivers:
        if driver.get("current_location"):
            distance = calculate_distance(rider_location, driver["current_location"])
            if distance <= 25:  # Increased to 25km for better coverage
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

# Admin Routes
@api_router.get("/admin/dashboard", response_model=AdminDashboardData)
async def get_admin_dashboard(current_user: dict = Depends(get_current_user)):
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get statistics
    total_users = await db.users.count_documents({})
    total_drivers = await db.users.count_documents({"user_type": "driver"})
    total_riders = await db.users.count_documents({"user_type": "rider"})
    total_rides = await db.ride_requests.count_documents({})
    active_rides = await db.ride_requests.count_documents({"status": {"$in": ["requested", "accepted", "in_progress"]}})
    pending_verifications = await db.driver_profiles.count_documents({"document_verified": False})
    
    # Get recent users
    recent_users_cursor = db.users.find({}).sort("created_at", -1).limit(10)
    recent_users = await recent_users_cursor.to_list(10)
    
    # Get recent rides
    recent_rides_cursor = db.ride_requests.find({}).sort("created_at", -1).limit(10)
    recent_rides = await recent_rides_cursor.to_list(10)
    
    # Clean data for response
    for user in recent_users:
        user.pop("password", None)
        user.pop("_id", None)
    
    for ride in recent_rides:
        ride.pop("_id", None)
    
    return AdminDashboardData(
        total_users=total_users,
        total_drivers=total_drivers,
        total_riders=total_riders,
        total_rides=total_rides,
        active_rides=active_rides,
        pending_verifications=pending_verifications,
        recent_users=recent_users,
        recent_rides=recent_rides
    )

@api_router.get("/admin/users")
async def get_all_users(
    user_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if user_type:
        query["user_type"] = user_type
    
    users_cursor = db.users.find(query, {"password": 0}).skip(skip).limit(limit)
    users = await users_cursor.to_list(limit)
    
    # Add driver profile info for drivers
    for user in users:
        user.pop("_id", None)
        if user["user_type"] == "driver":
            driver_profile = await db.driver_profiles.find_one({"user_id": user["id"]})
            if driver_profile:
                driver_profile.pop("_id", None)
                # Remove document data for privacy
                if driver_profile.get("license_document"):
                    driver_profile["license_document"] = {
                        k: v for k, v in driver_profile["license_document"].items() 
                        if k != "data"
                    }
                if driver_profile.get("registration_document"):
                    driver_profile["registration_document"] = {
                        k: v for k, v in driver_profile["registration_document"].items() 
                        if k != "data"
                    }
                user["driver_profile"] = driver_profile
    
    return {"users": users, "total": await db.users.count_documents(query)}

@api_router.post("/admin/user-action")
async def admin_user_action(
    action_data: UserManagementAction,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": action_data.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if action_data.action == "activate":
        await db.users.update_one(
            {"id": action_data.user_id},
            {"$set": {"is_active": True}}
        )
        return {"message": "User activated successfully"}
    
    elif action_data.action == "deactivate":
        await db.users.update_one(
            {"id": action_data.user_id},
            {"$set": {"is_active": False}}
        )
        return {"message": "User deactivated successfully"}
    
    elif action_data.action == "verify_driver":
        if user["user_type"] != "driver":
            raise HTTPException(status_code=400, detail="User is not a driver")
        
        await db.driver_profiles.update_one(
            {"user_id": action_data.user_id},
            {"$set": {"document_verified": True}}
        )
        return {"message": "Driver verified successfully"}
    
    elif action_data.action == "reject_driver":
        if user["user_type"] != "driver":
            raise HTTPException(status_code=400, detail="User is not a driver")
        
        await db.driver_profiles.update_one(
            {"user_id": action_data.user_id},
            {"$set": {"document_verified": False}}
        )
        return {"message": "Driver verification rejected"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@api_router.get("/admin/driver-documents/{user_id}")
async def get_driver_documents(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    driver_profile = await db.driver_profiles.find_one({"user_id": user_id})
    if not driver_profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    
    documents = {}
    if driver_profile.get("license_document"):
        documents["license_document"] = driver_profile["license_document"]
    if driver_profile.get("registration_document"):
        documents["registration_document"] = driver_profile["registration_document"]
    
    return documents

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