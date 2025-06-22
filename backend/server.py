from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from enum import Enum
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Gestion Location Immobilière")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Authentication setup
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    viewer = "viewer"

class UnitType(str, Enum):
    appartement = "appartement"
    studio = "studio"
    maison = "maison"
    commerce = "commerce"

class PropertyStatus(str, Enum):
    available = "disponible"
    occupied = "occupé"
    maintenance = "maintenance"

class PaymentStatus(str, Enum):
    paid = "payé"
    pending = "en_attente"
    overdue = "en_retard"

class Currency(str, Enum):
    EUR = "EUR"
    USD = "USD"
    XOF = "XOF"
    MAD = "MAD"
    TND = "TND"
    GBP = "GBP"
    CHF = "CHF"
    CAD = "CAD"

# Currency symbols mapping
CURRENCY_SYMBOLS = {
    "EUR": "€",
    "USD": "$",
    "XOF": "CFA",
    "MAD": "DH",
    "TND": "DT",
    "GBP": "£",
    "CHF": "CHF",
    "CAD": "C$"
}

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    role: UserRole = UserRole.viewer
    is_active: bool = True
    created_by: str  # ID of admin who created this user
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: UserRole = UserRole.viewer

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

class AppSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    currency: Currency = Currency.XOF  # Default to FCFA
    app_name: str = "Gestion Location Immobilière"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AppSettingsUpdate(BaseModel):
    currency: Currency
    app_name: Optional[str] = None

# Models
class Property(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    address: str
    monthly_rent: float
    description: Optional[str] = None
    status: PropertyStatus = PropertyStatus.available
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PropertyCreate(BaseModel):
    address: str
    monthly_rent: float
    description: Optional[str] = None
    status: PropertyStatus = PropertyStatus.available

class Unit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    unit_number: str  # ex: "Apt 1", "Studio A", "RDC Gauche"
    unit_type: UnitType
    monthly_rent: float
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    surface_area: Optional[float] = None  # en m²
    description: Optional[str] = None
    status: PropertyStatus = PropertyStatus.available
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UnitCreate(BaseModel):
    property_id: str
    unit_number: str
    unit_type: UnitType
    monthly_rent: float
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    surface_area: Optional[float] = None
    description: Optional[str] = None
    status: PropertyStatus = PropertyStatus.available

class Tenant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: Optional[str] = None
    phone: str  # Obligatoire pour les reçus
    property_id: Optional[str] = None
    unit_id: Optional[str] = None  # Appartement/Studio spécifique
    start_date: Optional[str] = None
    end_date: Optional[str] = None  # Date de fin de bail
    monthly_rent: Optional[float] = None
    deposit_amount: Optional[float] = None  # Caution
    months_paid: int = 0  # Nombre de mensualités payées
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TenantCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: str
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    monthly_rent: Optional[float] = None
    deposit_amount: Optional[float] = None

class TenantHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    tenant_name: str
    property_id: str
    property_name: str
    unit_id: Optional[str] = None
    unit_number: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    monthly_rent: float
    total_paid: float
    months_paid: int
    action: str  # "moved_in", "moved_out", "rent_updated"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    property_id: str
    unit_id: Optional[str] = None
    month: int
    year: int
    amount: float
    due_date: str  # Date d'échéance
    status: PaymentStatus = PaymentStatus.pending
    paid_date: Optional[str] = None
    payment_method: Optional[str] = "Espèces"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentCreate(BaseModel):
    tenant_id: str
    property_id: str
    unit_id: Optional[str] = None
    month: int
    year: int
    amount: float
    due_date: str
    status: PaymentStatus = PaymentStatus.pending
    paid_date: Optional[str] = None
    payment_method: Optional[str] = "Espèces"
    notes: Optional[str] = None

class Receipt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    receipt_number: str
    tenant_id: str
    tenant_name: str
    tenant_phone: str
    property_id: str
    property_name: str
    unit_id: Optional[str] = None
    unit_number: Optional[str] = None
    payment_id: str
    amount: float
    currency: str
    currency_symbol: str
    payment_date: str
    due_date: str
    period_month: int
    period_year: int
    payment_method: Optional[str] = "Espèces"
    months_paid_total: int  # Nombre total de mois payés par ce locataire
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReceiptCreate(BaseModel):
    tenant_id: str
    payment_id: str
    payment_method: Optional[str] = "Espèces"
    notes: Optional[str] = None

class DashboardStats(BaseModel):
    total_properties: int
    total_units: int
    total_tenants: int
    occupied_units: int
    monthly_revenue: float
    pending_payments: int
    overdue_payments: int
    occupancy_rate: float
    currency: str
    currency_symbol: str

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Create default admin user if not exists
async def create_default_admin():
    admin_exists = await db.users.find_one({"role": "admin"})
    if not admin_exists:
        admin_user = User(
            username="admin",
            email="admin@example.com",
            full_name="Administrateur",
            role=UserRole.admin,
            created_by="system"
        )
        
        # Store user with hashed password
        user_dict = admin_user.dict()
        user_dict["hashed_password"] = get_password_hash("admin123")
        await db.users.insert_one(user_dict)
        print("Default admin user created: admin/admin123")

# Routes
@api_router.get("/")
async def root():
    return {"message": "API Gestion Location Immobilière - Authentification requise"}

@api_router.get("/health")
async def health():
    return {"status": "ok"}

# Authentication endpoints
@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    user = await db.users.find_one({"username": user_login.username})
    if not user or not verify_password(user_login.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte désactivé"
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }

@api_router.post("/auth/create-user", response_model=User)
async def create_user(user_data: UserCreate, current_admin: User = Depends(get_admin_user)):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Nom d'utilisateur déjà existant"
        )
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email déjà utilisé"
        )
    
    # Create new user
    user_dict = user_data.dict()
    password = user_dict.pop("password")
    
    new_user = User(
        **user_dict,
        created_by=current_admin.id
    )
    
    # Store user with hashed password
    user_to_store = new_user.dict()
    user_to_store["hashed_password"] = get_password_hash(password)
    
    await db.users.insert_one(user_to_store)
    return new_user

@api_router.get("/auth/users", response_model=List[User])
async def get_users(current_admin: User = Depends(get_admin_user)):
    users = await db.users.find().to_list(1000)
    return [User(**{k: v for k, v in user.items() if k != "hashed_password"}) for user in users]

@api_router.put("/auth/users/{user_id}/toggle-status")
async def toggle_user_status(user_id: str, current_admin: User = Depends(get_admin_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    new_status = not user["is_active"]
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": new_status}}
    )
    
    return {"message": f"Utilisateur {'activé' if new_status else 'désactivé'}"}

@api_router.delete("/auth/users/{user_id}")
async def delete_user(user_id: str, current_admin: User = Depends(get_admin_user)):
    # Don't allow deleting yourself
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=400,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"message": "Utilisateur supprimé"}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Settings endpoints
@api_router.get("/settings", response_model=AppSettings)
async def get_settings():
    settings = await db.settings.find_one({})
    if not settings:
        # Create default settings
        default_settings = AppSettings()
        await db.settings.insert_one(default_settings.dict())
        return default_settings
    return AppSettings(**settings)

@api_router.put("/settings", response_model=AppSettings)
async def update_settings(settings_data: AppSettingsUpdate):
    current_settings = await db.settings.find_one({})
    if not current_settings:
        # Create new settings
        new_settings = AppSettings(**settings_data.dict())
        await db.settings.insert_one(new_settings.dict())
        return new_settings
    
    # Update existing settings
    update_data = settings_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.settings.update_one(
        {"id": current_settings["id"]},
        {"$set": update_data}
    )
    
    updated_settings = await db.settings.find_one({"id": current_settings["id"]})
    return AppSettings(**updated_settings)

@api_router.get("/currencies")
async def get_available_currencies():
    return {
        "currencies": [
            {"code": "EUR", "name": "Euro", "symbol": "€"},
            {"code": "USD", "name": "Dollar US", "symbol": "$"},
            {"code": "XOF", "name": "Franc CFA", "symbol": "CFA"},
            {"code": "MAD", "name": "Dirham Marocain", "symbol": "DH"},
            {"code": "TND", "name": "Dinar Tunisien", "symbol": "DT"},
            {"code": "GBP", "name": "Livre Sterling", "symbol": "£"},
            {"code": "CHF", "name": "Franc Suisse", "symbol": "CHF"},
            {"code": "CAD", "name": "Dollar Canadien", "symbol": "C$"}
        ]
    }

# Properties endpoints
@api_router.post("/properties", response_model=Property)
async def create_property(property_data: PropertyCreate):
    property_dict = property_data.dict()
    property_obj = Property(**property_dict)
    await db.properties.insert_one(property_obj.dict())
    return property_obj

@api_router.get("/properties", response_model=List[Property])
async def get_properties():
    properties = await db.properties.find().to_list(1000)
    return [Property(**prop) for prop in properties]

@api_router.get("/properties/{property_id}", response_model=Property)
async def get_property(property_id: str):
    property_data = await db.properties.find_one({"id": property_id})
    if not property_data:
        raise HTTPException(status_code=404, detail="Propriété non trouvée")
    return Property(**property_data)

@api_router.put("/properties/{property_id}", response_model=Property)
async def update_property(property_id: str, property_data: PropertyCreate):
    update_data = property_data.dict()
    result = await db.properties.update_one(
        {"id": property_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Propriété non trouvée")
    
    updated_property = await db.properties.find_one({"id": property_id})
    return Property(**updated_property)

@api_router.delete("/properties/{property_id}")
async def delete_property(property_id: str):
    result = await db.properties.delete_one({"id": property_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Propriété non trouvée")
    return {"message": "Propriété supprimée"}

# Units endpoints (Appartements/Studios)
@api_router.post("/units", response_model=Unit)
async def create_unit(unit_data: UnitCreate):
    unit_dict = unit_data.dict()
    unit_obj = Unit(**unit_dict)
    await db.units.insert_one(unit_obj.dict())
    return unit_obj

@api_router.get("/units", response_model=List[Unit])
async def get_units():
    units = await db.units.find().to_list(1000)
    return [Unit(**unit) for unit in units]

@api_router.get("/units/property/{property_id}", response_model=List[Unit])
async def get_property_units(property_id: str):
    units = await db.units.find({"property_id": property_id}).to_list(1000)
    return [Unit(**unit) for unit in units]

@api_router.get("/units/{unit_id}", response_model=Unit)
async def get_unit(unit_id: str):
    unit_data = await db.units.find_one({"id": unit_id})
    if not unit_data:
        raise HTTPException(status_code=404, detail="Unité non trouvée")
    return Unit(**unit_data)

@api_router.put("/units/{unit_id}", response_model=Unit)
async def update_unit(unit_id: str, unit_data: UnitCreate):
    update_data = unit_data.dict()
    result = await db.units.update_one(
        {"id": unit_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unité non trouvée")
    
    updated_unit = await db.units.find_one({"id": unit_id})
    return Unit(**updated_unit)

@api_router.delete("/units/{unit_id}")
async def delete_unit(unit_id: str):
    result = await db.units.delete_one({"id": unit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Unité non trouvée")
    return {"message": "Unité supprimée"}

# Tenants endpoints
@api_router.post("/tenants", response_model=Tenant)
async def create_tenant(tenant_data: TenantCreate):
    tenant_dict = tenant_data.dict()
    tenant_obj = Tenant(**tenant_dict)
    await db.tenants.insert_one(tenant_obj.dict())
    
    # Update unit status if unit_id is provided
    if tenant_obj.unit_id:
        await db.units.update_one(
            {"id": tenant_obj.unit_id},
            {"$set": {"status": PropertyStatus.occupied}}
        )
    elif tenant_obj.property_id:
        await db.properties.update_one(
            {"id": tenant_obj.property_id},
            {"$set": {"status": PropertyStatus.occupied}}
        )
    
    # Create history entry
    if tenant_obj.property_id:
        property_data = await db.properties.find_one({"id": tenant_obj.property_id})
        unit_data = None
        if tenant_obj.unit_id:
            unit_data = await db.units.find_one({"id": tenant_obj.unit_id})
        
        history_entry = TenantHistory(
            tenant_id=tenant_obj.id,
            tenant_name=tenant_obj.name,
            property_id=tenant_obj.property_id,
            property_name=property_data["address"] if property_data else "Inconnue",
            unit_id=tenant_obj.unit_id,
            unit_number=unit_data["unit_number"] if unit_data else None,
            start_date=tenant_obj.start_date or datetime.now().strftime("%Y-%m-%d"),
            end_date=tenant_obj.end_date,
            monthly_rent=tenant_obj.monthly_rent or 0,
            total_paid=0,
            months_paid=0,
            action="moved_in"
        )
        await db.tenant_history.insert_one(history_entry.dict())
    
    return tenant_obj

@api_router.get("/tenants", response_model=List[Tenant])
async def get_tenants():
    tenants = await db.tenants.find().to_list(1000)
    return [Tenant(**tenant) for tenant in tenants]

@api_router.get("/tenants/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str):
    tenant_data = await db.tenants.find_one({"id": tenant_id})
    if not tenant_data:
        raise HTTPException(status_code=404, detail="Locataire non trouvé")
    return Tenant(**tenant_data)

@api_router.put("/tenants/{tenant_id}", response_model=Tenant)
async def update_tenant(tenant_id: str, tenant_data: TenantCreate):
    update_data = tenant_data.dict()
    result = await db.tenants.update_one(
        {"id": tenant_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Locataire non trouvé")
    
    updated_tenant = await db.tenants.find_one({"id": tenant_id})
    return Tenant(**updated_tenant)

@api_router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
    result = await db.tenants.delete_one({"id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Locataire non trouvé")
    return {"message": "Locataire supprimé"}

# Payments endpoints
@api_router.post("/payments", response_model=Payment)
async def create_payment(payment_data: PaymentCreate):
    payment_dict = payment_data.dict()
    payment_obj = Payment(**payment_dict)
    await db.payments.insert_one(payment_obj.dict())
    return payment_obj

@api_router.get("/payments", response_model=List[Payment])
async def get_payments():
    payments = await db.payments.find().to_list(1000)
    return [Payment(**payment) for payment in payments]

@api_router.get("/payments/tenant/{tenant_id}", response_model=List[Payment])
async def get_tenant_payments(tenant_id: str):
    payments = await db.payments.find({"tenant_id": tenant_id}).to_list(1000)
    return [Payment(**payment) for payment in payments]

@api_router.put("/payments/{payment_id}", response_model=Payment)
async def update_payment(payment_id: str, payment_data: PaymentCreate):
    update_data = payment_data.dict()
    result = await db.payments.update_one(
        {"id": payment_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    
    updated_payment = await db.payments.find_one({"id": payment_id})
    return Payment(**updated_payment)

@api_router.put("/payments/{payment_id}/mark-paid")
async def mark_payment_paid(payment_id: str):
    from datetime import date
    result = await db.payments.update_one(
        {"id": payment_id}, 
        {"$set": {"status": PaymentStatus.paid, "paid_date": date.today().strftime("%Y-%m-%d")}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    
    # Update tenant's months_paid count
    payment = await db.payments.find_one({"id": payment_id})
    if payment:
        await db.tenants.update_one(
            {"id": payment["tenant_id"]},
            {"$inc": {"months_paid": 1}}
        )
    
    updated_payment = await db.payments.find_one({"id": payment_id})
    return Payment(**updated_payment)

@api_router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: str):
    result = await db.payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    return {"message": "Paiement supprimé"}

# Receipts endpoints
@api_router.post("/receipts", response_model=Receipt)
async def create_receipt(receipt_data: ReceiptCreate):
    # Get payment details
    payment = await db.payments.find_one({"id": receipt_data.payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    
    # Get tenant details
    tenant = await db.tenants.find_one({"id": receipt_data.tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Locataire non trouvé")
    
    # Get property details
    property_data = await db.properties.find_one({"id": payment["property_id"]})
    if not property_data:
        raise HTTPException(status_code=404, detail="Propriété non trouvée")
    
    # Get unit details if exists
    unit_data = None
    if payment.get("unit_id"):
        unit_data = await db.units.find_one({"id": payment["unit_id"]})
    
    # Get app settings for currency
    settings = await db.settings.find_one({})
    if not settings:
        settings = {"currency": "XOF"}
    
    currency = settings.get("currency", "XOF")
    currency_symbol = CURRENCY_SYMBOLS.get(currency, "CFA")
    
    # Generate receipt number
    current_date = datetime.now()
    receipt_count = await db.receipts.count_documents({}) + 1
    receipt_number = f"REC-{current_date.year}{current_date.month:02d}-{receipt_count:04d}"
    
    # Create receipt
    receipt_dict = {
        "receipt_number": receipt_number,
        "tenant_id": receipt_data.tenant_id,
        "tenant_name": tenant["name"],
        "tenant_phone": tenant.get("phone", "Non renseigné"),
        "property_id": payment["property_id"],
        "property_name": property_data["address"],
        "unit_id": payment.get("unit_id"),
        "unit_number": unit_data["unit_number"] if unit_data else None,
        "payment_id": receipt_data.payment_id,
        "amount": payment["amount"],
        "currency": currency,
        "currency_symbol": currency_symbol,
        "payment_date": payment.get("paid_date", datetime.now().strftime("%Y-%m-%d")),
        "due_date": payment.get("due_date", datetime.now().strftime("%Y-%m-%d")),
        "period_month": payment["month"],
        "period_year": payment["year"],
        "payment_method": payment.get("payment_method", "Espèces"),
        "months_paid_total": tenant.get("months_paid", 0),
        "notes": receipt_data.notes
    }
    
    receipt_obj = Receipt(**receipt_dict)
    await db.receipts.insert_one(receipt_obj.dict())
    return receipt_obj

@api_router.get("/receipts", response_model=List[Receipt])
async def get_receipts():
    receipts = await db.receipts.find().sort("created_at", -1).to_list(1000)
    return [Receipt(**receipt) for receipt in receipts]

@api_router.get("/receipts/tenant/{tenant_id}", response_model=List[Receipt])
async def get_tenant_receipts(tenant_id: str):
    receipts = await db.receipts.find({"tenant_id": tenant_id}).sort("created_at", -1).to_list(1000)
    return [Receipt(**receipt) for receipt in receipts]

@api_router.get("/receipts/{receipt_id}", response_model=Receipt)
async def get_receipt(receipt_id: str):
    receipt_data = await db.receipts.find_one({"id": receipt_id})
    if not receipt_data:
        raise HTTPException(status_code=404, detail="Reçu non trouvé")
    return Receipt(**receipt_data)

@api_router.delete("/receipts/{receipt_id}")
async def delete_receipt(receipt_id: str):
    result = await db.receipts.delete_one({"id": receipt_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reçu non trouvé")
    return {"message": "Reçu supprimé"}

# History and Search endpoints
@api_router.get("/history/tenant/{tenant_id}", response_model=List[TenantHistory])
async def get_tenant_history(tenant_id: str):
    history = await db.tenant_history.find({"tenant_id": tenant_id}).sort("created_at", -1).to_list(1000)
    return [TenantHistory(**h) for h in history]

@api_router.get("/search/occupancy")
async def search_occupancy_by_date(date: str):
    """Rechercher qui occupait quoi à une date donnée"""
    try:
        # Trouver tous les locataires actifs à cette date
        active_tenants = await db.tenants.find({
            "$and": [
                {"start_date": {"$lte": date}},
                {
                    "$or": [
                        {"end_date": {"$gte": date}},
                        {"end_date": None},
                        {"end_date": ""}
                    ]
                }
            ]
        }).to_list(1000)
        
        result = []
        for tenant in active_tenants:
            # Get property info
            property_data = await db.properties.find_one({"id": tenant.get("property_id")})
            
            # Get unit info if exists
            unit_data = None
            if tenant.get("unit_id"):
                unit_data = await db.units.find_one({"id": tenant["unit_id"]})
            
            result.append({
                "tenant_id": tenant["id"],
                "tenant_name": tenant["name"],
                "tenant_phone": tenant.get("phone", "Non renseigné"),
                "property_name": property_data["address"] if property_data else "Inconnue",
                "unit_number": unit_data["unit_number"] if unit_data else "Non spécifié",
                "unit_type": unit_data["unit_type"] if unit_data else "Non spécifié",
                "start_date": tenant.get("start_date"),
                "end_date": tenant.get("end_date"),
                "monthly_rent": tenant.get("monthly_rent", 0),
                "months_paid": tenant.get("months_paid", 0)
            })
        
        return {"date": date, "occupants": result}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Format de date invalide: {str(e)}")

@api_router.get("/search/unit-history/{unit_id}")
async def get_unit_occupancy_history(unit_id: str):
    """Historique des occupants d'une unité spécifique"""
    history = await db.tenant_history.find({"unit_id": unit_id}).sort("start_date", -1).to_list(1000)
    return [TenantHistory(**h) for h in history]

# Backup/Restore endpoints
@api_router.get("/backup")
async def backup_data():
    """Export all application data as JSON"""
    try:
        # Get all data
        properties = await db.properties.find().to_list(1000)
        tenants = await db.tenants.find().to_list(1000)
        payments = await db.payments.find().to_list(1000)
        receipts = await db.receipts.find().to_list(1000)
        settings = await db.settings.find_one({})
        
        # Create backup data
        backup_data = {
            "backup_date": datetime.now().isoformat(),
            "app_version": "1.0",
            "properties": properties,
            "tenants": tenants,
            "payments": payments,
            "receipts": receipts,
            "settings": settings or {},
            "total_records": {
                "properties": len(properties),
                "tenants": len(tenants),
                "payments": len(payments),
                "receipts": len(receipts)
            }
        }
        
        return backup_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde: {str(e)}")

@api_router.post("/restore")
async def restore_data(backup_data: dict):
    """Restore all application data from JSON backup"""
    try:
        # Clear existing data (optional - can be made configurable)
        # await db.properties.delete_many({})
        # await db.tenants.delete_many({})
        # await db.payments.delete_many({})
        # await db.receipts.delete_many({})
        
        # Restore properties
        if "properties" in backup_data and backup_data["properties"]:
            for prop in backup_data["properties"]:
                # Remove MongoDB _id if present
                prop.pop("_id", None)
                existing = await db.properties.find_one({"id": prop["id"]})
                if not existing:
                    await db.properties.insert_one(prop)
        
        # Restore tenants
        if "tenants" in backup_data and backup_data["tenants"]:
            for tenant in backup_data["tenants"]:
                tenant.pop("_id", None)
                existing = await db.tenants.find_one({"id": tenant["id"]})
                if not existing:
                    await db.tenants.insert_one(tenant)
        
        # Restore payments
        if "payments" in backup_data and backup_data["payments"]:
            for payment in backup_data["payments"]:
                payment.pop("_id", None)
                existing = await db.payments.find_one({"id": payment["id"]})
                if not existing:
                    await db.payments.insert_one(payment)
        
        # Restore receipts
        if "receipts" in backup_data and backup_data["receipts"]:
            for receipt in backup_data["receipts"]:
                receipt.pop("_id", None)
                existing = await db.receipts.find_one({"id": receipt["id"]})
                if not existing:
                    await db.receipts.insert_one(receipt)
        
        # Restore settings
        if "settings" in backup_data and backup_data["settings"]:
            settings = backup_data["settings"]
            settings.pop("_id", None)
            if settings:
                existing = await db.settings.find_one({})
                if existing:
                    await db.settings.update_one(
                        {"id": existing["id"]},
                        {"$set": settings}
                    )
                else:
                    await db.settings.insert_one(settings)
        
        return {
            "message": "Données restaurées avec succès",
            "restored_records": backup_data.get("total_records", {}),
            "restore_date": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la restauration: {str(e)}")

# Dashboard endpoint
@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
    # Get app settings for currency
    settings = await db.settings.find_one({})
    if not settings:
        settings = AppSettings().dict()
        await db.settings.insert_one(settings)
    
    currency = settings.get("currency", "EUR")
    currency_symbol = CURRENCY_SYMBOLS.get(currency, "€")
    
    # Get counts
    total_properties = await db.properties.count_documents({})
    total_tenants = await db.tenants.count_documents({})
    
    # Get current month/year
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Get payments for current month
    current_month_payments = await db.payments.find({
        "month": current_month,
        "year": current_year
    }).to_list(1000)
    
    # Calculate stats
    monthly_revenue = sum(p.get("amount", 0) for p in current_month_payments if p.get("status") == "payé")
    pending_payments = len([p for p in current_month_payments if p.get("status") == "en_attente"])
    overdue_payments = len([p for p in current_month_payments if p.get("status") == "en_retard"])
    
    # Calculate occupancy rate
    occupied_properties = await db.properties.count_documents({"status": "occupé"})
    occupancy_rate = (occupied_properties / total_properties * 100) if total_properties > 0 else 0
    
    return DashboardStats(
        total_properties=total_properties,
        total_tenants=total_tenants,
        monthly_revenue=monthly_revenue,
        pending_payments=pending_payments,
        overdue_payments=overdue_payments,
        occupancy_rate=round(occupancy_rate, 2),
        currency=currency,
        currency_symbol=currency_symbol
    )

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