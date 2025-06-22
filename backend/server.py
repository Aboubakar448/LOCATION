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
from datetime import datetime, date
from enum import Enum

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

# Enums
class PropertyStatus(str, Enum):
    available = "disponible"
    occupied = "occupé"
    maintenance = "maintenance"

class PaymentStatus(str, Enum):
    paid = "payé"
    pending = "en_attente"
    overdue = "en_retard"

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

class Tenant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    property_id: Optional[str] = None
    start_date: Optional[str] = None
    monthly_rent: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TenantCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    property_id: Optional[str] = None
    start_date: Optional[str] = None
    monthly_rent: Optional[float] = None

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    property_id: str
    month: int
    year: int
    amount: float
    status: PaymentStatus = PaymentStatus.pending
    paid_date: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentCreate(BaseModel):
    tenant_id: str
    property_id: str
    month: int
    year: int
    amount: float
    status: PaymentStatus = PaymentStatus.pending
    paid_date: Optional[date] = None

class DashboardStats(BaseModel):
    total_properties: int
    total_tenants: int
    monthly_revenue: float
    pending_payments: int
    overdue_payments: int
    occupancy_rate: float

# Routes
@api_router.get("/")
async def root():
    return {"message": "API Gestion Location Immobilière"}

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

# Tenants endpoints
@api_router.post("/tenants", response_model=Tenant)
async def create_tenant(tenant_data: TenantCreate):
    tenant_dict = tenant_data.dict()
    tenant_obj = Tenant(**tenant_dict)
    await db.tenants.insert_one(tenant_obj.dict())
    
    # Update property status if property_id is provided
    if tenant_obj.property_id:
        await db.properties.update_one(
            {"id": tenant_obj.property_id},
            {"$set": {"status": PropertyStatus.occupied}}
        )
    
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
    # Use datetime.now().strftime("%Y-%m-%d") instead of date.today()
    result = await db.payments.update_one(
        {"id": payment_id}, 
        {"$set": {"status": PaymentStatus.paid, "paid_date": datetime.now().strftime("%Y-%m-%d")}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    
    updated_payment = await db.payments.find_one({"id": payment_id})
    return Payment(**updated_payment)

@api_router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: str):
    result = await db.payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    return {"message": "Paiement supprimé"}

# Dashboard endpoint
@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
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
        occupancy_rate=round(occupancy_rate, 2)
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