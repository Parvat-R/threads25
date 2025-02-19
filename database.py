import os
import json
import uuid
from bson import ObjectId
from datetime import datetime
from pymongo import MongoClient, errors
from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator, validator
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load MongoDB URI from .env
load_dotenv()
uri = "mongodb+srv://threads25cse:aAlBJxpockulLRWh@threads-1.nlete.mongodb.net/?retryWrites=true&w=majority&appName=threads-1"
# uri = "mongodb://localhost:27017/"
MONGO_URI = os.environ.get("MONGO_URI", uri)
print(MONGO_URI)

# Connect to MongoDB with error handling
try:
    client = MongoClient(uri, maxPoolSize=100, minPoolSize=10)
    db = client.get_database("symposium_db")
    students_collection = db.students
    payment_and_otp_collection = db.payment_and_otp
    login_otp_collection = db.login_otp  # New collection for login OTPs
    admin_collection = db.admins
    bot_verified_payment = db.bot_verified_payment

    # Ensure indexes for students collection
    students_collection.create_index("email", unique=True)
    students_collection.create_index("phone", unique=True)

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
    workshop: str | None
    events: list[str]  # Changed from bool to list of strings
    college_name: str

class PaymentModel(BaseModel):
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

class BotVerifiedPaymentModel(BaseModel):
    email: EmailStr
    verified: bool

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



# Convert BSON to JSON
def bson_to_json(data):
    if data and "_id" in data:
        data["_id"] = str(data["_id"])
    return json.loads(json.dumps(data)) if data else None

# Student Collection Functions
def create_student(student_data: dict):
    if not students_collection:
        return None
    
    # Ensure events is a list
    if isinstance(student_data.get('events'), bool):
        student_data['events'] = []
    elif not isinstance(student_data.get('events'), list):
        student_data['events'] = [student_data.get('events')] if student_data.get('events') else []
    
    student = StudentModel(**student_data)
    inserted_id = students_collection.insert_one(student.model_dump()).inserted_id
    return str(inserted_id)

def get_student_by_id(student_id: str):
    
    if not students_collection:
        return None
    student = students_collection.find_one({"_id": ObjectId(student_id)})
    return bson_to_json(student)


def get_student_by_phone(phone: str):
    if not students_collection:
        return None
    student = students_collection.find_one({"phone": phone})
    return bson_to_json(student)

def edit_student(student_id: str, update_data: dict):
    if not students_collection:
        return None
    
    # Ensure events is a list
    if 'events' in update_data:
        if isinstance(update_data['events'], bool):
            update_data['events'] = []
        elif not isinstance(update_data['events'], list):
            update_data['events'] = [update_data['events']] if update_data['events'] else []
    
    print(students_collection.update_one({"email": update_data["email"]}, {"$set": update_data}).modified_count)
    return get_student_by_id(student_id)

def student_exists(email: str = None, phone: str = None):
    if not students_collection:
        return False
    query = {"$or": []}
    if email:
        query["$or"].append({"email": email})
    if phone:
        query["$or"].append({"phone": phone})
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

    payment = PaymentModel(**payment_data)
    inserted_id = payment_and_otp_collection.insert_one(payment.model_dump()).inserted_id
    return str(inserted_id)

def get_payment_by_email(email: str):
    if not payment_and_otp_collection:
        return None
    payment = payment_and_otp_collection.find_one({"email": email})
    return bson_to_json(payment)

def update_payment_status(email: str, transaction_id: str, upi_id: str):
    if not payment_and_otp_collection:
        return None
    
    update_data = {
        "paid": False,
        "transaction_id": transaction_id,
        "upi_id": upi_id
    }
    payment_and_otp_collection.update_one(
        {"email": email},
        {"$set": update_data}
    )
    return get_payment_by_email(email)

def update_otp(email: str, new_otp: str):
    # update the otp in the login and otp collection
    if not login_otp_collection:
        return False
    login_otp_collection.update_one(
        {"email": email},
        {"$set": {"otp": new_otp}}
    )
    return True

def verify_email(email: str, otp: str):
    # change the verified status in the login and otp collection
    if not login_otp_collection:
        return False
    
    if not verify_login_otp(email, otp):
        return False

    login_otp_collection.update_one(
        {"email": email},
        {"$set": {"verified": True}}
    )
    return True

def email_is_verified(email: str):
    # check the verification from the LoginAndOtp class
    if not login_otp_collection:
        return False
    otp_doc = login_otp_collection.find_one({"email": email})
    if not otp_doc:
        create_login_otp(email, "123456")
    otp_doc = login_otp_collection.find_one({"email": email})
    return otp_doc.get("verified")
    
    
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


def unverify_email(email: str):
    # make the user unverified in the login and otp class
    if not login_otp_collection:
        return False
    login_otp_collection.update_one(
        {"email": email},
        {"$set": {"verified": False}}
    )
    return True


def create_admin(username, password):
    if not admin_collection:
        return False
    admin = AdminModel(username=username, password=password)
    inserted_id = admin_collection.insert_one(admin.model_dump()).inserted_id
    return str(inserted_id)


def delete_admin(username):
    if not admin_collection:
        return False
    result = admin_collection.delete_one({"username": username})
    return result.deleted_count > 0

def edit_payment(email: str, payment_data: dict):
    if not payment_and_otp_collection:
        return None

    # Remove _id if present
    if "_id" in payment_data:
        del payment_data["_id"]


    # check if the email belongs to sona tech domain:
    # it: @sonatech.ac.in
    if email.endswith("@sonatech.ac.in"):
        payment_data['transaction_id'] = f"sona-{str(ObjectId())}"
        payment_data['upi_id'] = None

    # Convert to Pydantic model for validation
    if not isinstance(payment_data, PaymentModel):
        payment_data = PaymentModel(**payment_data)
        payment_data = payment_data.model_dump()

    res = payment_and_otp_collection.update_one(
        {"email": email},
        {"$set": payment_data}
    )

    print(f"Matched: {res.matched_count}, Modified: {res.modified_count}")
    return res.modified_count > 0

# create_admin("admin", "admin")