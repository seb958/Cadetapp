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
from datetime import datetime, timedelta, date
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
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 heures au lieu de 30 minutes

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
    # Grades pour cadets (ordre croissant)
    CADET = "cadet"
    CADET_AIR_1RE_CLASSE = "cadet_air_1re_classe"
    CAPORAL = "caporal"
    CAPORAL_SECTION = "caporal_section"
    SERGENT = "sergent"
    SERGENT_SECTION = "sergent_section"
    ADJUDANT_2E_CLASSE = "adjudant_2e_classe"
    ADJUDANT_1RE_CLASSE = "adjudant_1re_classe"
    INSTRUCTEUR_CIVIL = "instructeur_civil"
    ELEVE_OFFICIER = "eleve_officier"
    SOUS_LIEUTENANT = "sous_lieutenant"
    LIEUTENANT = "lieutenant"
    CAPITAINE = "capitaine"
    # Grades legacy (pour compatibilité avec données existantes)
    ADJUDANT = "adjudant"  # Legacy
    COMMANDANT = "commandant"  # Legacy

class PresenceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    RETARD = "retard"

class ActivityType(str, Enum):
    UNIQUE = "unique"  # Activité ponctuelle
    RECURRING = "recurring"  # Activité récurrente

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
    has_admin_privileges: bool = False  # Privilège "cadet admin" en plus du rôle

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
    email: Optional[EmailStr] = None
    nom: str
    prenom: str
    grade: Grade
    role: UserRole
    section_id: Optional[str] = None
    has_admin_privileges: bool = False

class SetPasswordRequest(BaseModel):
    token: str
    password: str

class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[EmailStr] = None
    grade: Optional[Grade] = None
    role: Optional[UserRole] = None
    section_id: Optional[str] = None
    actif: Optional[bool] = None
    has_admin_privileges: Optional[bool] = None

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

# Modèles pour les présences
class Presence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cadet_id: str
    date: date
    status: PresenceStatus
    commentaire: Optional[str] = None
    enregistre_par: str  # ID de l'utilisateur qui a enregistré
    heure_enregistrement: datetime = Field(default_factory=datetime.utcnow)
    section_id: Optional[str] = None
    activite: Optional[str] = None  # Description de l'activité

class PresenceCreate(BaseModel):
    cadet_id: str
    status: PresenceStatus
    commentaire: Optional[str] = None

class PresenceUpdate(BaseModel):
    status: Optional[PresenceStatus] = None
    commentaire: Optional[str] = None

class PresenceBulkCreate(BaseModel):
    date: date
    activite: Optional[str] = None
    presences: List[PresenceCreate]

class PresenceResponse(BaseModel):
    id: str
    cadet_id: str
    cadet_nom: str
    cadet_prenom: str
    date: date
    status: PresenceStatus
    commentaire: Optional[str]
    enregistre_par: str
    heure_enregistrement: datetime
    section_id: Optional[str]
    section_nom: Optional[str]
    activite: Optional[str]

class PresenceStats(BaseModel):
    total_seances: int
    presences: int
    absences: int
    absences_excusees: int
    retards: int
    taux_presence: float

# Modèles pour les activités pré-définies
class Activity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    description: Optional[str] = None
    type: ActivityType
    cadet_ids: List[str]  # Liste des IDs des cadets participants
    
    # Pour les activités récurrentes
    recurrence_interval: Optional[int] = None  # ex: 14 pour toutes les 2 semaines
    recurrence_unit: Optional[str] = None  # "days", "weeks", "months"
    next_date: Optional[str] = None  # Format: YYYY-MM-DD
    
    # Pour les activités ponctuelles  
    planned_date: Optional[str] = None  # Format: YYYY-MM-DD
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True

class ActivityCreate(BaseModel):
    nom: str
    description: Optional[str] = None
    type: ActivityType
    cadet_ids: List[str]
    
    # Pour récurrence
    recurrence_interval: Optional[int] = None
    recurrence_unit: Optional[str] = None
    next_date: Optional[str] = None  # Format: YYYY-MM-DD
    
    # Pour ponctuel
    planned_date: Optional[str] = None  # Format: YYYY-MM-DD

class ActivityResponse(BaseModel):
    id: str
    nom: str
    description: Optional[str]
    type: ActivityType
    cadet_ids: List[str]
    cadet_names: List[str]  # Noms complets des cadets
    recurrence_interval: Optional[int]
    recurrence_unit: Optional[str]
    next_date: Optional[str]  # Format: YYYY-MM-DD
    planned_date: Optional[str]  # Format: YYYY-MM-DD
    created_by: str
    created_at: datetime
    active: bool

class AlertStatus(str, Enum):
    ACTIVE = "active"
    CONTACTED = "contacted"
    RESOLVED = "resolved"

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cadet_id: str
    consecutive_absences: int
    last_absence_date: date
    status: AlertStatus = AlertStatus.ACTIVE
    contacted_by: Optional[str] = None
    contacted_at: Optional[datetime] = None
    contact_comment: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AlertResponse(BaseModel):
    id: str
    cadet_id: str
    cadet_nom: str
    cadet_prenom: str
    consecutive_absences: int
    last_absence_date: date
    status: AlertStatus
    contacted_by: Optional[str] = None
    contacted_at: Optional[datetime] = None
    contact_comment: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

class AlertUpdate(BaseModel):
    status: AlertStatus
    contact_comment: Optional[str] = None

class Permission(str, Enum):
    # Permissions de base
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"
    
    # Permissions des sections
    VIEW_SECTIONS = "view_sections"
    CREATE_SECTIONS = "create_sections"
    EDIT_SECTIONS = "edit_sections"
    DELETE_SECTIONS = "delete_sections"
    
    # Permissions des activités
    VIEW_ACTIVITIES = "view_activities"
    CREATE_ACTIVITIES = "create_activities"
    EDIT_ACTIVITIES = "edit_activities"
    DELETE_ACTIVITIES = "delete_activities"
    
    # Permissions des présences
    VIEW_PRESENCES = "view_presences"
    CREATE_PRESENCES = "create_presences"
    EDIT_PRESENCES = "edit_presences"
    DELETE_PRESENCES = "delete_presences"
    
    # Permissions des alertes
    VIEW_ALERTS = "view_alerts"
    MANAGE_ALERTS = "manage_alerts"
    
    # Permissions administratives
    MANAGE_ROLES = "manage_roles"
    SYSTEM_SETTINGS = "system_settings"

class Role(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    permissions: List[Permission] = []
    is_system_role: bool = False  # Les rôles système ne peuvent pas être supprimés
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[Permission] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[Permission]] = None

class ConsecutiveAbsenceCalculation(BaseModel):
    cadet_id: str
    consecutive_absences: int
    last_absence_date: Optional[date] = None
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

async def require_presence_permissions(current_user: User = Depends(get_current_user)):
    """Vérifie les permissions pour la gestion des présences"""
    if current_user.role not in [UserRole.CADET_RESPONSIBLE, UserRole.CADET_ADMIN, UserRole.ENCADREMENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Permissions pour gestion des présences requises."
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
    # Si email fourni, vérifier qu'il n'existe pas déjà
    if invitation.email:
        existing_user = await db.users.find_one({"email": invitation.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un utilisateur avec cet email existe déjà"
            )
    
    # Créer le token d'invitation seulement si email fourni
    invitation_token = None
    invitation_expires = None
    if invitation.email:
        invitation_token = create_invitation_token(invitation.email)
        invitation_expires = datetime.utcnow() + timedelta(days=7)
    
    # Créer l'utilisateur
    user_data = UserInDB(
        nom=invitation.nom,
        prenom=invitation.prenom,
        email=invitation.email,
        grade=invitation.grade,
        role=invitation.role,
        section_id=invitation.section_id,
        has_admin_privileges=invitation.has_admin_privileges,
        invitation_token=invitation_token,
        invitation_expires=invitation_expires,
        created_by=current_user.id,
        actif=invitation.email is None  # Actif immédiatement si pas d'email
    )
    
    await db.users.insert_one(user_data.dict())
    
    # Envoyer l'email d'invitation seulement si email fourni
    if invitation.email and invitation_token:
        await send_invitation_email(
            invitation.email, 
            invitation.nom, 
            invitation.prenom, 
            invitation_token
        )
        return {"message": "Invitation envoyée avec succès", "token": invitation_token}
    else:
        return {"message": "Utilisateur créé avec succès (sans email)", "token": None}

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
async def get_users(
    grade: Optional[str] = None,
    role: Optional[str] = None,
    section_id: Optional[str] = None,
    current_user: User = Depends(require_admin_or_encadrement)
):
    # Construire le filtre de base
    filter_dict = {}
    
    # Ajouter les filtres optionnels
    if grade:
        filter_dict["grade"] = grade
    if role:
        filter_dict["role"] = role
    if section_id:
        filter_dict["section_id"] = section_id
    
    # Récupérer tous les utilisateurs (actifs et en attente) avec les filtres appliqués
    users = await db.users.find(filter_dict).to_list(1000)
    return [User(**user) for user in users]

@api_router.post("/users", response_model=dict)
async def create_user(
    user: UserCreate, 
    current_user: User = Depends(require_admin_or_encadrement)
):
    # Vérifier si l'utilisateur existe déjà
    existing_user = await db.users.find_one({"email": user.email}) if user.email else None
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Créer l'utilisateur - TOUJOURS ACTIF lors de la création par admin
    new_user = {
        "id": str(uuid.uuid4()),
        "prenom": user.prenom,
        "nom": user.nom,
        "email": user.email,
        "password_hash": None,  # Pas de mot de passe initial
        "role": user.role,
        "grade": user.grade,
        "section_id": user.section_id,
        "actif": True,  # 🔥 TOUJOURS ACTIF lors de la création par admin
        "has_admin_privileges": user.has_admin_privileges,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(new_user)
    
    # Envoyer l'invitation par email si un email est fourni
    if user.email:
        try:
            # Ici on pourrait envoyer un vrai email d'invitation
            # Pour l'instant, on simule l'envoi
            print(f"📧 Email d'invitation envoyé à {user.email}")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'envoi de l'email: {e}")
    
    return {"message": "Utilisateur créé avec succès", "user_id": new_user["id"]}

@api_router.get("/users/filters")
async def get_user_filters(current_user: User = Depends(require_admin_or_encadrement)):
    """Récupérer les options de filtres pour les utilisateurs"""
    
    # Récupérer tous les utilisateurs pour extraire les filtres
    users = await db.users.find({"actif": True}).to_list(1000)
    sections = await db.sections.find().to_list(1000)
    
    # Extraire les grades uniques
    grades = list(set([user.get("grade") for user in users if user.get("grade")]))
    grades.sort()
    
    # Extraire les rôles uniques
    roles = list(set([user.get("role") for user in users if user.get("role")]))
    roles.sort()
    
    # Formatter les sections
    section_options = [{"id": section["id"], "name": section["nom"]} for section in sections]
    section_options.sort(key=lambda x: x["name"])
    
    return {
        "grades": grades,
        "roles": roles,
        "sections": section_options
    }

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

@api_router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin_or_encadrement)
):
    # Vérifier que l'utilisateur existe
    existing_user = await db.users.find_one({"id": user_id, "actif": True})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Préparer les mises à jour (seulement les champs fournis)
    update_data = {}
    
    if user_update.nom is not None:
        update_data["nom"] = user_update.nom.strip()
    if user_update.prenom is not None:
        update_data["prenom"] = user_update.prenom.strip()
    if user_update.email is not None:
        # Vérifier que l'email n'est pas déjà utilisé par un autre utilisateur
        if user_update.email:
            existing_email = await db.users.find_one({
                "email": user_update.email,
                "id": {"$ne": user_id}
            })
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cet email est déjà utilisé par un autre utilisateur"
                )
            
            # Si l'utilisateur n'avait pas d'email avant et qu'on lui en ajoute un
            if not existing_user.get("email") and user_update.email:
                # Créer un token d'invitation et l'envoyer
                invitation_token = create_invitation_token(user_update.email)
                update_data["invitation_token"] = invitation_token
                update_data["invitation_expires"] = (datetime.utcnow() + timedelta(days=7)).isoformat()
                update_data["actif"] = False  # L'utilisateur devra confirmer par email
                
                # Envoyer l'email d'invitation
                await send_invitation_email(
                    user_update.email,
                    existing_user["nom"],
                    existing_user["prenom"],
                    invitation_token
                )
        
        update_data["email"] = user_update.email
    if user_update.grade is not None:
        update_data["grade"] = user_update.grade.value
    if user_update.role is not None:
        update_data["role"] = user_update.role.value
    if user_update.section_id is not None:
        # Vérifier que la section existe si fournie
        if user_update.section_id:
            section = await db.sections.find_one({"id": user_update.section_id})
            if not section:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Section non trouvée"
                )
        update_data["section_id"] = user_update.section_id
    if user_update.actif is not None:
        update_data["actif"] = user_update.actif
    if user_update.has_admin_privileges is not None:
        update_data["has_admin_privileges"] = user_update.has_admin_privileges
    
    # Effectuer la mise à jour
    if update_data:
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
    
    return {"message": "Utilisateur mis à jour avec succès"}

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin_or_encadrement)
):
    # Vérifier que l'utilisateur existe
    existing_user = await db.users.find_one({"id": user_id, "actif": True})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Empêcher la suppression de son propre compte
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )
    
    # Supprimer définitivement l'utilisateur et toutes ses données associées
    try:
        # Supprimer toutes les présences de cet utilisateur
        await db.presences.delete_many({"cadet_id": user_id})
        
        # Supprimer l'utilisateur des activités
        await db.activities.update_many(
            {"cadet_ids": user_id},
            {"$pull": {"cadet_ids": user_id}}
        )
        
        # Supprimer l'utilisateur
        result = await db.users.delete_one({"id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )
        
        return {"message": f"Utilisateur {existing_user['prenom']} {existing_user['nom']} supprimé définitivement avec toutes ses données"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )

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

@api_router.put("/sections/{section_id}")
async def update_section(
    section_id: str,
    section_update: SectionCreate,
    current_user: User = Depends(require_admin_or_encadrement)
):
    # Vérifier que la section existe
    existing_section = await db.sections.find_one({"id": section_id})
    if not existing_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section non trouvée"
        )
    
    # Préparer les données de mise à jour
    update_data = {
        "nom": section_update.nom,
        "description": section_update.description,
        "responsable_id": section_update.responsable_id if section_update.responsable_id else None
    }
    
    # Mettre à jour la section
    await db.sections.update_one(
        {"id": section_id},
        {"$set": update_data}
    )
    
    return {"message": "Section mise à jour avec succès"}

@api_router.delete("/sections/{section_id}")
async def delete_section(
    section_id: str,
    current_user: User = Depends(require_admin_or_encadrement)
):
    # Vérifier que la section existe
    existing_section = await db.sections.find_one({"id": section_id})
    if not existing_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section non trouvée"
        )
    
    # Supprimer définitivement la section et mettre à jour les utilisateurs
    try:
        # Retirer l'affectation de section de tous les utilisateurs
        await db.users.update_many(
            {"section_id": section_id},
            {"$unset": {"section_id": ""}}
        )
        
        # Supprimer la section
        result = await db.sections.delete_one({"id": section_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section non trouvée"
            )
        
        return {"message": f"Section {existing_section['nom']} supprimée définitivement"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )

# Routes pour les présences
@api_router.post("/presences", response_model=Presence)
async def create_presence(
    presence: PresenceCreate,
    presence_date: date = None,
    activite: Optional[str] = None,
    current_user: User = Depends(require_presence_permissions)
):
    # Utiliser la date d'aujourd'hui si non fournie
    if presence_date is None:
        presence_date = date.today()
    
    # Vérifier que le cadet existe
    cadet = await db.users.find_one({"id": presence.cadet_id, "actif": True})
    if not cadet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cadet non trouvé"
        )
    
    # Vérifier les permissions selon le rôle
    if current_user.role == UserRole.CADET_RESPONSIBLE:
        # Un cadet responsable ne peut enregistrer que pour sa section
        if cadet.get("section_id") != current_user.section_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez enregistrer les présences que pour votre section"
            )
    
    # Vérifier si une présence existe déjà pour ce cadet à cette date
    existing_presence = await db.presences.find_one({
        "cadet_id": presence.cadet_id,
        "date": presence_date.isoformat()
    })
    
    if existing_presence:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une présence existe déjà pour ce cadet à cette date"
        )
    
    # Créer la présence
    presence_data = Presence(
        cadet_id=presence.cadet_id,
        date=presence_date,
        status=presence.status,
        commentaire=presence.commentaire,
        enregistre_par=current_user.id,
        section_id=cadet.get("section_id"),
        activite=activite
    )
    
    await db.presences.insert_one(presence_data.dict())
    return presence_data

@api_router.post("/presences/bulk")
async def create_bulk_presences(
    bulk_data: PresenceBulkCreate,
    current_user: User = Depends(require_presence_permissions)
):
    created_presences = []
    errors = []
    
    for presence_create in bulk_data.presences:
        try:
            # Vérifier que le cadet existe
            cadet = await db.users.find_one({"id": presence_create.cadet_id, "actif": True})
            if not cadet:
                errors.append(f"Cadet {presence_create.cadet_id} non trouvé")
                continue
            
            # Vérifier les permissions selon le rôle
            if current_user.role == UserRole.CADET_RESPONSIBLE:
                if cadet.get("section_id") != current_user.section_id:
                    errors.append(f"Permission refusée pour le cadet {cadet['prenom']} {cadet['nom']}")
                    continue
            
            # Vérifier si une présence existe déjà
            existing_presence = await db.presences.find_one({
                "cadet_id": presence_create.cadet_id,
                "date": bulk_data.date.isoformat()
            })
            
            if existing_presence:
                # Mettre à jour la présence existante
                await db.presences.update_one(
                    {"id": existing_presence["id"]},
                    {"$set": {
                        "status": presence_create.status.value,
                        "commentaire": presence_create.commentaire,
                        "enregistre_par": current_user.id,
                        "heure_enregistrement": datetime.utcnow().isoformat(),
                        "activite": bulk_data.activite
                    }}
                )
                created_presences.append(existing_presence["id"])
            else:
                # Créer nouvelle présence
                presence_data = {
                    "id": str(uuid.uuid4()),
                    "cadet_id": presence_create.cadet_id,
                    "date": bulk_data.date.isoformat(),
                    "status": presence_create.status.value,
                    "commentaire": presence_create.commentaire,
                    "enregistre_par": current_user.id,
                    "heure_enregistrement": datetime.utcnow().isoformat(),
                    "section_id": cadet.get("section_id"),
                    "activite": bulk_data.activite
                }
                
                await db.presences.insert_one(presence_data)
                created_presences.append(presence_data["id"])
                
        except Exception as e:
            errors.append(f"Erreur pour cadet {presence_create.cadet_id}: {str(e)}")
    
    return {
        "created_count": len(created_presences),
        "created_ids": created_presences,
        "errors": errors
    }

@api_router.get("/presences", response_model=List[PresenceResponse])
async def get_presences(
    date: Optional[date] = None,
    cadet_id: Optional[str] = None,
    section_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    # Construire le filtre selon les permissions
    filter_dict = {}
    
    if current_user.role == UserRole.CADET:
        # Un cadet ne peut voir que ses propres présences
        filter_dict["cadet_id"] = current_user.id
    elif current_user.role == UserRole.CADET_RESPONSIBLE:
        # Un cadet responsable ne peut voir que sa section
        if current_user.section_id:
            filter_dict["section_id"] = current_user.section_id
        else:
            # Si pas de section assignée, ne peut rien voir
            return []
    # CADET_ADMIN et ENCADREMENT peuvent tout voir
    
    # Appliquer les filtres additionnels
    if date:
        filter_dict["date"] = date.isoformat()
    if cadet_id and current_user.role in [UserRole.CADET_ADMIN, UserRole.ENCADREMENT]:
        filter_dict["cadet_id"] = cadet_id
    if section_id and current_user.role in [UserRole.CADET_ADMIN, UserRole.ENCADREMENT]:
        filter_dict["section_id"] = section_id
    
    # Récupérer les présences
    presences_cursor = db.presences.find(filter_dict).limit(limit).sort("date", -1)
    presences = await presences_cursor.to_list(limit)
    
    # Enrichir avec les informations des cadets et sections
    enriched_presences = []
    for presence in presences:
        # Récupérer les infos du cadet
        cadet = await db.users.find_one({"id": presence["cadet_id"]})
        if not cadet:
            continue
            
        # Récupérer les infos de la section si applicable
        section_nom = None
        if presence.get("section_id"):
            section = await db.sections.find_one({"id": presence["section_id"]})
            if section:
                section_nom = section["nom"]
        
        enriched_presence = PresenceResponse(
            id=presence["id"],
            cadet_id=presence["cadet_id"],
            cadet_nom=cadet["nom"],
            cadet_prenom=cadet["prenom"],
            date=datetime.fromisoformat(presence["date"]).date(),
            status=PresenceStatus(presence["status"]),
            commentaire=presence.get("commentaire"),
            enregistre_par=presence["enregistre_par"],
            heure_enregistrement=datetime.fromisoformat(presence["heure_enregistrement"]),
            section_id=presence.get("section_id"),
            section_nom=section_nom,
            activite=presence.get("activite")
        )
        enriched_presences.append(enriched_presence)
    
    return enriched_presences

@api_router.put("/presences/{presence_id}")
async def update_presence(
    presence_id: str,
    updates: PresenceUpdate,
    current_user: User = Depends(require_presence_permissions)
):
    # Vérifier que la présence existe
    presence = await db.presences.find_one({"id": presence_id})
    if not presence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Présence non trouvée"
        )
    
    # Vérifier les permissions
    if current_user.role == UserRole.CADET_RESPONSIBLE:
        if presence.get("section_id") != current_user.section_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez modifier que les présences de votre section"
            )
    
    # Préparer les mises à jour
    update_data = {}
    if updates.status is not None:
        update_data["status"] = updates.status.value
    if updates.commentaire is not None:
        update_data["commentaire"] = updates.commentaire
    
    update_data["enregistre_par"] = current_user.id
    update_data["heure_enregistrement"] = datetime.utcnow().isoformat()
    
    # Mettre à jour
    await db.presences.update_one(
        {"id": presence_id},
        {"$set": update_data}
    )
    
    return {"message": "Présence mise à jour avec succès"}

@api_router.get("/presences/stats/{cadet_id}", response_model=PresenceStats)
async def get_presence_stats(
    cadet_id: str,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    # Vérifier les permissions
    if current_user.role == UserRole.CADET and current_user.id != cadet_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez consulter que vos propres statistiques"
        )
    
    # Construire le filtre
    filter_dict = {"cadet_id": cadet_id}
    if date_debut:
        filter_dict["date"] = {"$gte": date_debut.isoformat()}
    if date_fin:
        if "date" in filter_dict:
            filter_dict["date"]["$lte"] = date_fin.isoformat()
        else:
            filter_dict["date"] = {"$lte": date_fin.isoformat()}
    
    # Récupérer toutes les présences
    presences = await db.presences.find(filter_dict).to_list(1000)
    
    # Calculer les statistiques
    total_seances = len(presences)
    presences_count = len([p for p in presences if p["status"] == "present"])
    absences = len([p for p in presences if p["status"] == "absent"])
    absences_excusees = len([p for p in presences if p["status"] == "absent_excuse"])
    retards = len([p for p in presences if p["status"] == "retard"])
    
    taux_presence = (presences_count / total_seances * 100) if total_seances > 0 else 0
    
    return PresenceStats(
        total_seances=total_seances,
        presences=presences_count,
        absences=absences,
        absences_excusees=absences_excusees,
        retards=retards,
        taux_presence=round(taux_presence, 2)
    )

# Routes pour les activités pré-définies
@api_router.post("/activities", response_model=Activity)
async def create_activity(
    activity: ActivityCreate,
    current_user: User = Depends(require_admin_or_encadrement)
):
    # Vérifier que tous les cadets existent (peu importe leur statut d'activation)
    for cadet_id in activity.cadet_ids:
        cadet = await db.users.find_one({"id": cadet_id})
        if not cadet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cadet {cadet_id} non trouvé"
            )
    
    # Créer l'activité
    activity_data = Activity(
        nom=activity.nom,
        description=activity.description,
        type=activity.type,
        cadet_ids=activity.cadet_ids,
        recurrence_interval=activity.recurrence_interval,
        recurrence_unit=activity.recurrence_unit,
        next_date=activity.next_date,
        planned_date=activity.planned_date,
        created_by=current_user.id
    )
    
    await db.activities.insert_one(activity_data.dict())
    return activity_data

@api_router.get("/activities", response_model=List[ActivityResponse])
async def get_activities(
    active_only: bool = True,
    current_user: User = Depends(require_admin_or_encadrement)
):
    filter_dict = {}
    if active_only:
        filter_dict["active"] = True
    
    activities = await db.activities.find(filter_dict).to_list(1000)
    
    # Enrichir avec les noms des cadets
    enriched_activities = []
    for activity in activities:
        # Récupérer les noms des cadets (actifs et non actifs)
        cadet_names = []
        for cadet_id in activity["cadet_ids"]:
            cadet = await db.users.find_one({"id": cadet_id})
            if cadet:
                status_indicator = "" if cadet.get("actif", False) else " (non confirmé)"
                cadet_names.append(f"{cadet['prenom']} {cadet['nom']}{status_indicator}")
        
        # Conversion des dates pour la réponse
        next_date = None
        if activity.get("next_date"):
            if isinstance(activity["next_date"], str):
                next_date = activity["next_date"]
            else:
                # Conversion date object vers string
                next_date = activity["next_date"].strftime("%Y-%m-%d")
        
        planned_date = None
        if activity.get("planned_date"):
            if isinstance(activity["planned_date"], str):
                planned_date = activity["planned_date"]
            else:
                # Conversion date object vers string
                planned_date = activity["planned_date"].strftime("%Y-%m-%d")

        # Conversion de created_at
        created_at = activity["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        enriched_activity = ActivityResponse(
            id=activity["id"],
            nom=activity["nom"],
            description=activity.get("description"),
            type=ActivityType(activity["type"]),
            cadet_ids=activity["cadet_ids"],
            cadet_names=cadet_names,
            recurrence_interval=activity.get("recurrence_interval"),
            recurrence_unit=activity.get("recurrence_unit"),
            next_date=next_date,
            planned_date=planned_date,
            created_by=activity["created_by"],
            created_at=created_at,
            active=activity["active"]
        )
        enriched_activities.append(enriched_activity)
    
    return enriched_activities

@api_router.get("/activities/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str,
    current_user: User = Depends(require_admin_or_encadrement)
):
    activity = await db.activities.find_one({"id": activity_id})
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activité non trouvée"
        )
    
    # Récupérer les noms des cadets (actifs et non actifs)
    cadet_names = []
    for cadet_id in activity["cadet_ids"]:
        cadet = await db.users.find_one({"id": cadet_id})
        if cadet:
            status_indicator = "" if cadet.get("actif", False) else " (non confirmé)"
            cadet_names.append(f"{cadet['prenom']} {cadet['nom']}{status_indicator}")
    
    # Conversion des dates pour la réponse
    next_date = None
    if activity.get("next_date"):
        if isinstance(activity["next_date"], str):
            next_date = activity["next_date"]
        else:
            # Conversion date object vers string
            next_date = activity["next_date"].strftime("%Y-%m-%d")
    
    planned_date = None
    if activity.get("planned_date"):
        if isinstance(activity["planned_date"], str):
            planned_date = activity["planned_date"]
        else:
            # Conversion date object vers string
            planned_date = activity["planned_date"].strftime("%Y-%m-%d")

    # Conversion de created_at
    created_at = activity["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    return ActivityResponse(
        id=activity["id"],
        nom=activity["nom"],
        description=activity.get("description"),
        type=ActivityType(activity["type"]),
        cadet_ids=activity["cadet_ids"],
        cadet_names=cadet_names,
        recurrence_interval=activity.get("recurrence_interval"),
        recurrence_unit=activity.get("recurrence_unit"),
        next_date=next_date,
        planned_date=planned_date,
        created_by=activity["created_by"],
        created_at=created_at,
        active=activity["active"]
    )

@api_router.put("/activities/{activity_id}")
async def update_activity(
    activity_id: str,
    activity_update: ActivityCreate,
    current_user: User = Depends(require_admin_or_encadrement)
):
    # Vérifier que l'activité existe
    existing_activity = await db.activities.find_one({"id": activity_id})
    if not existing_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activité non trouvée"
        )
    
    # Vérifier que tous les cadets existent
    for cadet_id in activity_update.cadet_ids:
        cadet = await db.users.find_one({"id": cadet_id, "actif": True})
        if not cadet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cadet {cadet_id} non trouvé"
            )
    
    # Mettre à jour
    update_data = {
        "nom": activity_update.nom,
        "description": activity_update.description,
        "type": activity_update.type.value,
        "cadet_ids": activity_update.cadet_ids,
        "recurrence_interval": activity_update.recurrence_interval,
        "recurrence_unit": activity_update.recurrence_unit,
        "next_date": activity_update.next_date if activity_update.next_date else None,
        "planned_date": activity_update.planned_date if activity_update.planned_date else None
    }
    
    await db.activities.update_one(
        {"id": activity_id},
        {"$set": update_data}
    )
    
    return {"message": "Activité mise à jour avec succès"}

@api_router.delete("/activities/{activity_id}")
async def delete_activity(
    activity_id: str,
    current_user: User = Depends(require_admin_or_encadrement)
):
    result = await db.activities.update_one(
        {"id": activity_id},
        {"$set": {"active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activité non trouvée"
        )
    
    return {"message": "Activité désactivée avec succès"}

# Routes pour la gestion des rôles
@api_router.get("/roles", response_model=List[Role])
async def get_roles(current_user: User = Depends(require_admin_or_encadrement)):
    """Récupérer tous les rôles"""
    roles = await db.roles.find().to_list(1000)
    return [Role(**role) for role in roles]

@api_router.post("/roles", response_model=Role)
async def create_role(
    role: RoleCreate,
    current_user: User = Depends(require_admin_or_encadrement)
):
    """Créer un nouveau rôle"""
    # Vérifier que le nom du rôle n'existe pas déjà
    existing_role = await db.roles.find_one({"name": role.name})
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un rôle avec ce nom existe déjà"
        )
    
    role_data = Role(**role.dict())
    await db.roles.insert_one(role_data.dict())
    return role_data

@api_router.put("/roles/{role_id}")
async def update_role(
    role_id: str,
    role_update: RoleUpdate,
    current_user: User = Depends(require_admin_or_encadrement)
):
    """Mettre à jour un rôle"""
    # Vérifier que le rôle existe
    existing_role = await db.roles.find_one({"id": role_id})
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rôle non trouvé"
        )
    
    # Empêcher la modification des rôles système
    if existing_role.get("is_system_role", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les rôles système ne peuvent pas être modifiés"
        )
    
    # Préparer les mises à jour
    update_data = {}
    if role_update.name is not None:
        # Vérifier que le nouveau nom n'existe pas déjà
        name_exists = await db.roles.find_one({
            "name": role_update.name,
            "id": {"$ne": role_id}
        })
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un rôle avec ce nom existe déjà"
            )
        update_data["name"] = role_update.name
    
    if role_update.description is not None:
        update_data["description"] = role_update.description
    
    if role_update.permissions is not None:
        update_data["permissions"] = [perm.value for perm in role_update.permissions]
    
    # Effectuer la mise à jour
    if update_data:
        await db.roles.update_one(
            {"id": role_id},
            {"$set": update_data}
        )
    
    return {"message": "Rôle mis à jour avec succès"}

@api_router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    current_user: User = Depends(require_admin_or_encadrement)
):
    """Supprimer un rôle"""
    # Vérifier que le rôle existe
    existing_role = await db.roles.find_one({"id": role_id})
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rôle non trouvé"
        )
    
    # Empêcher la suppression des rôles système
    if existing_role.get("is_system_role", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les rôles système ne peuvent pas être supprimés"
        )
    
    # Vérifier qu'aucun utilisateur n'utilise ce rôle
    users_with_role = await db.users.find({"custom_role_id": role_id}).to_list(1)
    if users_with_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer un rôle utilisé par des utilisateurs"
        )
    
    # Supprimer le rôle
    result = await db.roles.delete_one({"id": role_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rôle non trouvé"
        )
    
    return {"message": "Rôle supprimé avec succès"}

# Routes pour les alertes d'absences consécutives
@api_router.get("/alerts/consecutive-absences")
async def calculate_consecutive_absences(
    threshold: int = 3,
    current_user: User = Depends(require_admin_or_encadrement)
):
    """Calculer les absences consécutives pour tous les cadets"""
    
    # Récupérer tous les cadets
    cadets = await db.users.find({"role": {"$in": ["cadet", "cadet_responsible"]}, "actif": True}).to_list(1000)
    
    consecutive_absences_list = []
    
    for cadet in cadets:
        # Récupérer les présences du cadet triées par date décroissante
        presences = await db.presences.find(
            {"cadet_id": cadet["id"]}
        ).sort("date", -1).to_list(1000)
        
        consecutive_count = 0
        last_absence_date = None
        
        for presence in presences:
            presence_date = datetime.fromisoformat(presence["date"]).date()
            
            if presence["status"] in ["absent", "absent_excuse"]:
                consecutive_count += 1
                if last_absence_date is None:
                    last_absence_date = presence_date
            else:
                # Dès qu'on trouve une présence, on arrête le comptage
                break
        
        if consecutive_count >= threshold:
            consecutive_absences_list.append(ConsecutiveAbsenceCalculation(
                cadet_id=cadet["id"],
                consecutive_absences=consecutive_count,
                last_absence_date=last_absence_date
            ))
    
    return consecutive_absences_list

@api_router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    current_user: User = Depends(require_admin_or_encadrement)
):
    """Récupérer toutes les alertes actives"""
    
    # Récupérer les alertes depuis la base de données
    alerts = await db.alerts.find().sort("created_at", -1).to_list(1000)
    
    enriched_alerts = []
    for alert in alerts:
        # Récupérer les informations du cadet
        cadet = await db.users.find_one({"id": alert["cadet_id"]})
        if not cadet:
            continue
        
        enriched_alert = AlertResponse(
            id=alert["id"],
            cadet_id=alert["cadet_id"],
            cadet_nom=cadet["nom"],
            cadet_prenom=cadet["prenom"],
            consecutive_absences=alert["consecutive_absences"],
            last_absence_date=datetime.fromisoformat(alert["last_absence_date"]).date() if alert.get("last_absence_date") else None,
            status=AlertStatus(alert["status"]),
            contacted_by=alert.get("contacted_by"),
            contacted_at=datetime.fromisoformat(alert["contacted_at"]) if alert.get("contacted_at") else None,
            contact_comment=alert.get("contact_comment"),
            resolved_by=alert.get("resolved_by"),
            resolved_at=datetime.fromisoformat(alert["resolved_at"]) if alert.get("resolved_at") else None,
            created_at=datetime.fromisoformat(alert["created_at"])
        )
        enriched_alerts.append(enriched_alert)
    
    return enriched_alerts

@api_router.post("/alerts/generate")
async def generate_alerts(
    threshold: int = 3,
    current_user: User = Depends(require_admin_or_encadrement)
):
    """Générer de nouvelles alertes basées sur les absences consécutives"""
    
    # Calculer les absences consécutives
    consecutive_absences = await calculate_consecutive_absences(threshold, current_user)
    
    new_alerts_count = 0
    
    for absence_calc in consecutive_absences:
        # Vérifier si une alerte active existe déjà pour ce cadet
        existing_alert = await db.alerts.find_one({
            "cadet_id": absence_calc.cadet_id,
            "status": {"$in": ["active", "contacted"]}
        })
        
        if not existing_alert:
            # Créer une nouvelle alerte
            alert_data = Alert(
                cadet_id=absence_calc.cadet_id,
                consecutive_absences=absence_calc.consecutive_absences,
                last_absence_date=absence_calc.last_absence_date,
                status=AlertStatus.ACTIVE
            )
            
            # Convertir les dates en string pour MongoDB
            alert_dict = alert_data.dict()
            if alert_dict.get("last_absence_date"):
                alert_dict["last_absence_date"] = alert_dict["last_absence_date"].isoformat()
            if alert_dict.get("created_at"):
                alert_dict["created_at"] = alert_dict["created_at"].isoformat()
            
            await db.alerts.insert_one(alert_dict)
            new_alerts_count += 1
        else:
            # Mettre à jour l'alerte existante si le nombre d'absences a augmenté
            if absence_calc.consecutive_absences > existing_alert["consecutive_absences"]:
                await db.alerts.update_one(
                    {"id": existing_alert["id"]},
                    {"$set": {
                        "consecutive_absences": absence_calc.consecutive_absences,
                        "last_absence_date": absence_calc.last_absence_date.isoformat() if absence_calc.last_absence_date else None
                    }}
                )
    
    return {"message": f"{new_alerts_count} nouvelles alertes générées"}

@api_router.put("/alerts/{alert_id}")
async def update_alert(
    alert_id: str,
    alert_update: AlertUpdate,
    current_user: User = Depends(require_admin_or_encadrement)
):
    """Mettre à jour le statut d'une alerte"""
    
    # Vérifier que l'alerte existe
    existing_alert = await db.alerts.find_one({"id": alert_id})
    if not existing_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte non trouvée"
        )
    
    update_data = {"status": alert_update.status.value}
    
    if alert_update.status == AlertStatus.CONTACTED:
        update_data.update({
            "contacted_by": current_user.id,
            "contacted_at": datetime.utcnow().isoformat(),
            "contact_comment": alert_update.contact_comment
        })
    elif alert_update.status == AlertStatus.RESOLVED:
        update_data.update({
            "resolved_by": current_user.id,
            "resolved_at": datetime.utcnow().isoformat()
        })
    
    await db.alerts.update_one(
        {"id": alert_id},
        {"$set": update_data}
    )
    
    return {"message": "Alerte mise à jour avec succès"}

@api_router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: User = Depends(require_admin_or_encadrement)
):
    """Supprimer une alerte"""
    
    result = await db.alerts.delete_one({"id": alert_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte non trouvée"
        )
    
    return {"message": "Alerte supprimée avec succès"}

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