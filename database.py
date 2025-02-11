import os
import json
from datetime import datetime
from pymongo import MongoClient, errors
from pydantic import BaseModel, EmailStr, Field
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load MongoDB URI from .env
load_dotenv()
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://cyberspace212005:68myd2wFrhLwhHfd@test-threads-1.tv8j0.mongodb.net/symposium_db?retryWrites=true&w=majority")
print(MONGO_URI)

# Connect to MongoDB with error handling
try:
    client = MongoClient(MONGO_URI, maxPoolSize=100, minPoolSize=10)
    db = client.get_database("symposium_db")
    students_collection = db.students
    payment_and_otp_collection = db.payment_and_otp
    login_otp_collection = db.login_otp  # New collection for login OTPs
    admin_collection = db.admins

    # Ensure indexes for students collection
    students_collection.create_index("email", unique=True)
    students_collection.create_index("phone", unique=True)
    students_collection.create_index("rollno", unique=True)

    # Ensure indexes for payment_and_otp collection
    payment_and_otp_collection.create_index("email", unique=True)
    payment_and_otp_collection.create_index("transaction_id", unique=True, sparse=True)

    # Ensure indexes for login_otp collection
    login_otp_collection.create_index("email", unique=True)
    login_otp_collection.create_index([("created_at", 1)], expireAfterSeconds=300)  # OTP expires after 5 minutes

    #Ensure indexes for admin collection
    admin_collection.create_index("username", unique=True)

    print("[✅] Connected to MongoDB")


except errors.ConnectionFailure as e:
    print(f"[❌] MongoDB Connection Failed: {e}")
    students_collection = None
    payment_and_otp_collection = None
    login_otp_collection = None

# Pydantic Models for Data Validation
class StudentModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    rollno: str = Field(..., min_length=4, max_length=20)
    workshop: str | None
    events: bool
    college_name: str

class PaymentAndOtpModel(BaseModel):
    email: EmailStr
    paid: bool = False
    transaction_id: str | None = None
    upi_id: str | None = None

class LoginOtpModel(BaseModel):
    email: EmailStr
    verified: bool = False
    otp: str = Field(..., min_length=6, max_length=6)

class AdminModel(BaseModel):
    username: str
    password: str

# Login OTP Collection Functions
def create_login_otp(email: str, otp: str):
    """Create or update login OTP for a user"""
    if not login_otp_collection:
        return None
    
    login_otp_data = {
        "email": email,
        "otp": otp,
    }
    
    login_otp = LoginOtpModel(**login_otp_data)
    
    # Upsert the OTP (create or update)
    result = login_otp_collection.update_one(
        {"email": email},
        {"$set": login_otp.model_dump()},
        upsert=True
    )
    
    return bool(result.modified_count or result.upserted_id)

def verify_login_otp(email: str, otp: str) -> bool:
    """Verify login OTP and handle attempts"""
    if not login_otp_collection:
        return False
    
    # Get the OTP document
    otp_doc = login_otp_collection.find_one({
        "email": email
    })
    
    if not otp_doc:
        return False
    
    return otp_doc.get("otp") == otp

def get_login_otp_status(email: str):
    """Get current login OTP status"""
    if not login_otp_collection:
        return None
    
    otp_doc = login_otp_collection.find_one({"email": email})
    return bson_to_json(otp_doc) if otp_doc else None

def delete_login_otp(email: str):
    """Delete login OTP entry"""
    if not login_otp_collection:
        return False
    
    result = login_otp_collection.delete_one({"email": email})
    return result.deleted_count > 0

def is_otp_valid(email: str):
    """Check if there's a valid OTP for the email"""
    if not login_otp_collection:
        return False
    
    otp_doc = login_otp_collection.find_one({
        "email": email
    })
    
    return bool(otp_doc)

# Pydantic Models for Data Validation
class StudentModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    rollno: str = Field(..., min_length=4, max_length=20)
    workshop: str | None
    events: bool
    college_name: str

class PaymentAndOtpModel(BaseModel):
    email: EmailStr
    opt: str  # to verify the email
    paid: bool = False
    transaction_id: str | None = None
    upi_id: str | None = None

# Convert BSON to JSON
def bson_to_json(data):
    if data and "_id" in data:
        data["_id"] = str(data["_id"])
    return json.loads(json.dumps(data)) if data else None

# Student Collection Functions
def create_student(student_data: dict):
    if not students_collection:
        return None
    student = StudentModel(**student_data)
    inserted_id = students_collection.insert_one(student.model_dump()).inserted_id
    return str(inserted_id)

def get_student_by_id(student_id: str):
    if not students_collection:
        return None
    student = students_collection.find_one({"_id": ObjectId(student_id)})
    return bson_to_json(student)

def get_student_by_rollno(rollno: str):
    if not students_collection:
        return None
    student = students_collection.find_one({"rollno": rollno})
    return bson_to_json(student)

def get_student_by_phone(phone: str):
    if not students_collection:
        return None
    student = students_collection.find_one({"phone": phone})
    return bson_to_json(student)

def edit_student(student_id: str, update_data: dict):
    if not students_collection:
        return None
    students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": update_data})
    return get_student_by_id(student_id)

def student_exists(email: str = None, phone: str = None, rollno: str = None):
    if not students_collection:
        return False
    query = {"$or": []}
    if email:
        query["$or"].append({"email": email})
    if phone:
        query["$or"].append({"phone": phone})
    if rollno:
        query["$or"].append({"rollno": rollno})
    return students_collection.find_one(query) is not None if query["$or"] else False

def get_all_students():
    if not students_collection:
        return []
    students = list(students_collection.find())
    return [bson_to_json(student) for student in students]

def get_student_by_email(email: str):
    if not students_collection:
        return None
    student = students_collection.find_one({"email": email})
    return bson_to_json(student)

# Payment and OTP Collection Functions
def create_payment_entry(payment_data: dict):
    if not payment_and_otp_collection:
        return None
    payment = PaymentAndOtpModel(**payment_data)
    inserted_id = payment_and_otp_collection.insert_one(payment.model_dump()).inserted_id
    return str(inserted_id)

def get_payment_by_email(email: str):
    if not payment_and_otp_collection:
        return None
    payment = payment_and_otp_collection.find_one({"email": email})
    return bson_to_json(payment)

def update_payment_status(email: str, transaction_id: str, upi_id: str | None = None):
    if not payment_and_otp_collection:
        return None
    update_data = {
        "paid": True,
        "transaction_id": transaction_id,
        "upi_id": upi_id
    }
    payment_and_otp_collection.update_one(
        {"email": email},
        {"$set": update_data}
    )
    return get_payment_by_email(email)

def verify_otp(email: str, otp: str):
    if not payment_and_otp_collection:
        return False
    payment = payment_and_otp_collection.find_one({
        "email": email,
        "opt": otp
    })
    return payment is not None

def update_otp(email: str, new_otp: str):
    if not payment_and_otp_collection:
        return None
    payment_and_otp_collection.update_one(
        {"email": email},
        {"$set": {"opt": new_otp}}
    )
    return get_payment_by_email(email)

def verify_email(email: str, otp: str):
    if not payment_and_otp_collection:
        return False
    payment = payment_and_otp_collection.find_one({
        "email": email,
        "opt": otp        
    })
    if payment is not None:
        # set the verified param to true
        payment_and_otp_collection.update_one(
            {"email": email},
            {"$set": {"verified": True}}
        )
        return True
    return False

def email_is_verified(email: str):
    if not payment_and_otp_collection:
        return False
    payment = payment_and_otp_collection.find_one({
        "email": email,
        "verified": True
    })
    return payment is not None

def delete_payment_entry(email: str):
    if not payment_and_otp_collection:
        return False
    result = payment_and_otp_collection.delete_one({"email": email})
    return result.deleted_count > 0

def get_all_payments():
    if not payment_and_otp_collection:
        return []
    payments = list(payment_and_otp_collection.find())
    return [bson_to_json(payment) for payment in payments]


def admin_exists(username):
    if not admin_collection:
        return False
    admin = admin_collection.find_one({"username": username})
    return admin is not None

def match_admin_password(username, password):
    if not admin_collection:
        return False
    admin = admin_collection.find_one({"username": username})
    if admin is None:
        return False
    return admin["password"] == password
