import uuid
from src.components.core.tenant_db import init_db, SessionLocal, Company, User
from src.components.core.auth import get_password_hash

def seed_database():
    print("Initializing DB schema...")
    init_db()
    
    db = SessionLocal()
    
    print("Seeding dummy company...")
    company_id = str(uuid.uuid4())
    acme = Company(
        id=company_id,
        name="Acme Corp",
        domain="acme.com",
        linkedin_access_token="dummy_li_token_acme",
        linkedin_org_id="dummy_org_acme"
    )
    db.add(acme)
    
    print("Seeding dummy user...")
    admin_user = User(
        id=str(uuid.uuid4()),
        company_id=company_id,
        email="admin@acme.com",
        password_hash=get_password_hash("password123"),
        role="admin"
    )
    db.add(admin_user)
    
    db.commit()
    db.close()
    
    print(f"Database seeded successfully!\nTest Login -> Email: admin@acme.com | Password: password123")
    print(f"Company ID created: {company_id}")

if __name__ == "__main__":
    seed_database()
