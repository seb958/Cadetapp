from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(title="Gestion Escadron Cadets", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    CADET = "cadet"
    CADET_RESPONSIBLE = "cadet_responsible" 
    CADET_ADMIN = "cadet_admin"
    ENCADREMENT = "encadrement"

class Grade(str, Enum):
    # Grades pour cadets
    CADET = "cadet"
    CAPORAL = "caporal"
    SERGENT = "sergent"
    ADJUDANT = "adjudant"
    # Grades pour encadrement
    LIEUTENANT = "lieutenant"
    CAPITAINE = "capitaine"
    COMMANDANT = "commandant"

# Models
class UserBase(BaseModel):
    nom: str
    prenom: str
    email: Optional[EmailStr] = None
    grade: Grade
    role: UserRole
    section_id: Optional[str] = None
    photo_base64: Optional[str] = None
    actif: bool = True

class UserCreate(UserBase):
    pass

class UserInDB(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hashed_password: Optional[str] = None
    invitation_token: Optional[str] = None
    invitation_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime

class UserInvitation(BaseModel):
    email: EmailStr
    nom: str
    prenom: str
    grade: Grade
    role: UserRole
    section_id: Optional[str] = None

class SetPasswordRequest(BaseModel):
    token: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Section(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    description: Optional[str] = None
    responsable_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SectionCreate(BaseModel):
    nom: str
    description: Optional[str] = None
    responsable_id: Optional[str] = None

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_invitation_token(email: str) -> str:
    data = {
        "email": email,
        "type": "invitation",
        "exp": datetime.utcnow() + timedelta(days=7)  # Token valide 7 jours
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token d'authentification invalide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

async def require_admin_or_encadrement(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.CADET_ADMIN, UserRole.ENCADREMENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Permissions administrateur requises."
        )
    return current_user

# Email service (simplified - in production use proper email service)
async def send_invitation_email(email: str, nom: str, prenom: str, token: str):
    # In production, use proper email service like SendGrid, AWS SES, etc.
    # For now, we'll just log the invitation details
    invitation_link = f"http://localhost:3000/invitation?token={token}"
    logging.info(f"INVITATION EMAIL - Destinataire: {email}")
    logging.info(f"Nom: {prenom} {nom}")
    logging.info(f"Lien d'invitation: {invitation_link}")
    logging.info("Note: Intégrer un vrai service d'email pour la production")

# Routes d'authentification
@api_router.post("/auth/login", response_model=Token)
async def login(request: LoginRequest):
    # Trouver l'utilisateur par email
    user_data = await db.users.find_one({"email": request.email})
    if not user_data or not user_data.get("hashed_password"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Vérifier le mot de passe
    if not verify_password(request.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Créer le token d'accès
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data["id"]}, expires_delta=access_token_expires
    )
    
    user = User(**user_data)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@api_router.post("/auth/invite")
async def invite_user(
    invitation: UserInvitation,
    current_user: User = Depends(require_admin_or_encadrement)
):
    # Vérifier si l'utilisateur existe déjà
    existing_user = await db.users.find_one({"email": invitation.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Créer le token d'invitation
    invitation_token = create_invitation_token(invitation.email)
    
    # Créer l'utilisateur en attente
    user_data = UserInDB(
        nom=invitation.nom,
        prenom=invitation.prenom,
        email=invitation.email,
        grade=invitation.grade,
        role=invitation.role,
        section_id=invitation.section_id,
        invitation_token=invitation_token,
        invitation_expires=datetime.utcnow() + timedelta(days=7),
        created_by=current_user.id,
        actif=False  # Sera activé après définition du mot de passe
    )
    
    await db.users.insert_one(user_data.dict())
    
    # Envoyer l'email d'invitation
    await send_invitation_email(
        invitation.email, 
        invitation.nom, 
        invitation.prenom, 
        invitation_token
    )
    
    return {"message": "Invitation envoyée avec succès", "token": invitation_token}

@api_router.post("/auth/set-password")
async def set_password(request: SetPasswordRequest):
    try:
        # Décoder le token d'invitation
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        if not email or payload.get("type") != "invitation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token d'invitation invalide"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token d'invitation expiré"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token d'invitation invalide"
        )
    
    # Trouver l'utilisateur avec ce token
    user_data = await db.users.find_one({
        "email": email,
        "invitation_token": request.token
    })
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token d'invitation invalide ou utilisateur non trouvé"
        )
    
    # Vérifier que le token n'a pas expiré
    if user_data["invitation_expires"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token d'invitation expiré"
        )
    
    # Hasher le mot de passe et activer l'utilisateur
    hashed_password = get_password_hash(request.password)
    
    await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "hashed_password": hashed_password,
                "actif": True
            },
            "$unset": {
                "invitation_token": "",
                "invitation_expires": ""
            }
        }
    )
    
    return {"message": "Mot de passe défini avec succès"}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Routes pour la gestion des utilisateurs
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(require_admin_or_encadrement)):
    users = await db.users.find({"actif": True}).to_list(1000)
    return [User(**user) for user in users]

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    # Les utilisateurs peuvent voir leur propre profil
    # Les admins/encadrement peuvent voir tous les profils
    if (current_user.id != user_id and 
        current_user.role not in [UserRole.CADET_ADMIN, UserRole.ENCADREMENT]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé"
        )
    
    user = await db.users.find_one({"id": user_id, "actif": True})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    return User(**user)

# Routes pour les sections
@api_router.post("/sections", response_model=Section)
async def create_section(
    section: SectionCreate,
    current_user: User = Depends(require_admin_or_encadrement)
):
    section_data = Section(**section.dict())
    await db.sections.insert_one(section_data.dict())
    return section_data

@api_router.get("/sections", response_model=List[Section])
async def get_sections(current_user: User = Depends(get_current_user)):
    sections = await db.sections.find().to_list(1000)
    return [Section(**section) for section in sections]

# Route de test
@api_router.get("/")
async def root():
    return {"message": "API Gestion Escadron Cadets - v1.0.0"}

# Include router
app.include_router(api_router)

# CORS middleware
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