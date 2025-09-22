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

class PresenceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    ABSENT_EXCUSE = "absent_excuse"
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
    next_date: Optional[date] = None
    
    # Pour les activités ponctuelles  
    planned_date: Optional[date] = None
    
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
    next_date: Optional[date] = None
    
    # Pour ponctuel
    planned_date: Optional[date] = None

class ActivityResponse(BaseModel):
    id: str
    nom: str
    description: Optional[str]
    type: ActivityType
    cadet_ids: List[str]
    cadet_names: List[str]  # Noms complets des cadets
    recurrence_interval: Optional[int]
    recurrence_unit: Optional[str]
    next_date: Optional[date]
    planned_date: Optional[date]
    created_by: str
    created_at: datetime
    active: bool

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