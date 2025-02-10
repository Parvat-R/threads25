import os
import json
from pymongo import MongoClient, errors
from pydantic import BaseModel, EmailStr, Field
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load MongoDB URI from .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/symposium_db")  # Fallback to localhost

print(MONGO_URI)
# Connect to MongoDB with error handling
try:
    client = MongoClient(MONGO_URI, maxPoolSize=100, minPoolSize=10)
    db = client.get_database("symposium_db")
    students_collection = db.students

    # Ensure indexes for fast lookups
    students_collection.create_index("email", unique=True)
    students_collection.create_index("phone", unique=True)
    students_collection.create_index("rollno", unique=True)

    # add the payment transaction id also
    students_collection.create_index("payment_transaction_id", unique=True)

    print("[✅] Connected to MongoDB")
except errors.ConnectionFailure as e:
    print(f"[❌] MongoDB Connection Failed: {e}")
    students_collection = None  # Prevent operations if DB is unavailable

# Pydantic Model for Data Validation
class StudentModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    rollno: str = Field(..., min_length=4, max_length=20)
    registered_events: dict[str, bool] = {}
    paid: bool = False
    transaction_id: str  # Changed from payment_transaction_id
    upi_id: str         # Changed from upid

# Convert BSON to JSON (for MongoDB ObjectId handling)
def bson_to_json(data):
    if data and "_id" in data:
        data["_id"] = str(data["_id"])  # Convert ObjectId to string
    return json.loads(json.dumps(data)) if data else None

# Create Student
def create_student(student_data: dict):
    if not students_collection:
        return None  # Prevent DB operations if not connected
    student = StudentModel(**student_data)  # Validate with Pydantic
    inserted_id = students_collection.insert_one(student.model_dump()).inserted_id
    return str(inserted_id)

# Get Student by ID
def get_student_by_id(student_id: str):
    if not students_collection:
        return None
    student = students_collection.find_one({"_id": ObjectId(student_id)})
    return bson_to_json(student)

# Get Student by Roll Number
def get_student_by_rollno(rollno: str):
    if not students_collection:
        return None
    student = students_collection.find_one({"rollno": rollno})
    return bson_to_json(student)

# Get Student by Phone Number
def get_student_by_phone(phone: str):
    if not students_collection:
        return None
    student = students_collection.find_one({"phone": phone})
    return bson_to_json(student)

# Edit Student
def edit_student(student_id: str, update_data: dict):
    if not students_collection:
        return None
    students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": update_data})
    return get_student_by_id(student_id)

# Check if Student Exists (by Email, Phone, or Roll Number)
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