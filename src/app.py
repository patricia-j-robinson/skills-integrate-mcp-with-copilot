"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
import json
from pathlib import Path
import uuid

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Load teacher credentials
def load_teachers():
    teachers_file = Path(__file__).parent / "teachers.json"
    with open(teachers_file, 'r') as f:
        return json.load(f)

# In-memory session storage (stores logged-in users)
teacher_sessions = {}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# In-memory user database and session store
users = {
    "michael@mergington.edu": {
        "password": "student123",
        "role": "student",
        "full_name": "Michael Johnson"
    },
    "emma@mergington.edu": {
        "password": "student123",
        "role": "student",
        "full_name": "Emma Williams"
    },
    "organizer@mergington.edu": {
        "password": "organizer123",
        "role": "organizer",
        "full_name": "Ms. Blair"
    }
}

sessions = {}


class User(BaseModel):
    email: str
    role: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


def create_session(email: str) -> str:
    session_id = str(uuid.uuid4())
    sessions[session_id] = email
    return session_id


def get_current_user(request: Request) -> User:
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Authentication required")

    email = sessions[session_id]
    user_data = users.get(email)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    return User(email=email, role=user_data["role"], full_name=user_data["full_name"])


@app.post("/login")
def login(login_request: LoginRequest, response: Response):
    user = users.get(login_request.email)
    if not user or user["password"] != login_request.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_id = create_session(login_request.email)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
    )

    return {
        "message": "Logged in successfully",
        "email": login_request.email,
        "role": user["role"],
        "full_name": user["full_name"],
    }


@app.post("/logout")
def logout(request: Request, response: Response, current_user: User = Depends(get_current_user)):
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]

    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}


@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, current_user: User = Depends(get_current_user)):
    """Sign up a student for an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    email = current_user.email

    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, current_user: User = Depends(get_current_user)):
    """Unregister a student from an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    email = current_user.email

    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.post("/login")
def login(username: str, password: str):
    """Authenticate a teacher"""
    teachers_data = load_teachers()
    
    # Check credentials
    for teacher in teachers_data["teachers"]:
        if teacher["username"] == username and teacher["password"] == password:
            # Generate a simple session ID (in production, use proper JWT)
            session_id = f"{username}_{hash(username + password)}"
            teacher_sessions[session_id] = username
            return {"success": True, "session_id": session_id, "username": username}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/logout")
def logout(session_id: str):
    """Logout a teacher"""
    if session_id in teacher_sessions:
        del teacher_sessions[session_id]
    return {"message": "Logged out successfully"}


@app.get("/verify-session")
def verify_session(session_id: str):
    """Verify if a session is valid"""
    if session_id in teacher_sessions:
        return {"valid": True, "username": teacher_sessions[session_id]}
    return {"valid": False}


@app.post("/admin/register-student")
def admin_register_student(activity_name: str, email: str, session_id: str):
    """Register a student for an activity (admin only)"""
    # Verify session
    if session_id not in teacher_sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    activity = activities[activity_name]
    
    # Check capacity
    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")
    
    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")
    
    # Add student
    activity["participants"].append(email)
    return {"message": f"Admin registered {email} for {activity_name}"}


@app.delete("/admin/unregister-student")
def admin_unregister_student(activity_name: str, email: str, session_id: str):
    """Unregister a student from an activity (admin only)"""
    # Verify session
    if session_id not in teacher_sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    activity = activities[activity_name]
    
    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")
    
    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Admin unregistered {email} from {activity_name}"}
