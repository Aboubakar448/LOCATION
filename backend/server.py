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
from datetime import datetime
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

# Enums
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

class AppSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    currency: Currency = Currency.EUR
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
    paid_date: Optional[str] = None

class Receipt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    receipt_number: str
    tenant_id: str
    tenant_name: str
    property_address: str
    payment_id: str
    amount: float
    currency: str
    currency_symbol: str
    payment_date: str
    period_month: int
    period_year: int
    payment_method: Optional[str] = "Espèces"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReceiptCreate(BaseModel):
    tenant_id: str
    payment_id: str
    payment_method: Optional[str] = "Espèces"
    notes: Optional[str] = None

class DashboardStats(BaseModel):
    total_properties: int
    total_tenants: int
    monthly_revenue: float
    pending_payments: int
    overdue_payments: int
    occupancy_rate: float
    currency: str
    currency_symbol: str

# Routes
@api_router.get("/")
async def root():
    return {"message": "API Gestion Location Immobilière"}

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
    
    # Get app settings for currency
    settings = await db.settings.find_one({})
    if not settings:
        settings = {"currency": "EUR"}
    
    currency = settings.get("currency", "EUR")
    currency_symbol = CURRENCY_SYMBOLS.get(currency, "€")
    
    # Generate receipt number
    current_date = datetime.now()
    receipt_count = await db.receipts.count_documents({}) + 1
    receipt_number = f"REC-{current_date.year}{current_date.month:02d}-{receipt_count:04d}"
    
    # Create receipt
    receipt_dict = {
        "receipt_number": receipt_number,
        "tenant_id": receipt_data.tenant_id,
        "tenant_name": tenant["name"],
        "property_address": property_data["address"],
        "payment_id": receipt_data.payment_id,
        "amount": payment["amount"],
        "currency": currency,
        "currency_symbol": currency_symbol,
        "payment_date": payment.get("paid_date", datetime.now().strftime("%Y-%m-%d")),
        "period_month": payment["month"],
        "period_year": payment["year"],
        "payment_method": receipt_data.payment_method or "Espèces",
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