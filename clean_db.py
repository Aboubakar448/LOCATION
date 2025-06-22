#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv('/app/backend/.env')

async def clean_database():
    # Connection à MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Supprimer toutes les données
    result_properties = await db.properties.delete_many({})
    result_tenants = await db.tenants.delete_many({})
    result_payments = await db.payments.delete_many({})
    result_receipts = await db.receipts.delete_many({})
    
    print("🧹 BASE DE DONNÉES NETTOYÉE !")
    print(f"✅ Propriétés supprimées: {result_properties.deleted_count}")
    print(f"✅ Locataires supprimés: {result_tenants.deleted_count}")
    print(f"✅ Paiements supprimés: {result_payments.deleted_count}")
    print(f"✅ Reçus supprimés: {result_receipts.deleted_count}")
    
    # Vérifier que tout est vide
    count_properties = await db.properties.count_documents({})
    count_tenants = await db.tenants.count_documents({})
    count_payments = await db.payments.count_documents({})
    count_receipts = await db.receipts.count_documents({})
    
    print("\n📊 ÉTAT FINAL:")
    print(f"Propriétés: {count_properties}")
    print(f"Locataires: {count_tenants}")
    print(f"Paiements: {count_payments}")
    print(f"Reçus: {count_receipts}")
    
    if count_properties == 0 and count_tenants == 0:
        print("\n🎯 PARFAIT ! Base propre - Vous pouvez maintenant enregistrer VOS données !")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clean_database())