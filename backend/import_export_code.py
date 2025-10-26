# ============================================================================
# SYSTÈME D'IMPORT/EXPORT EXCEL - Code à ajouter dans server.py
# ============================================================================

import openpyxl
from openpyxl import Workbook
import pandas as pd
from typing import List, Dict, Optional
from io import BytesIO

# Mapping des acronymes vers les grades du système
GRADE_MAPPING = {
    "Cdt": "cadet",
    "Cdt1": "cadet_air_1re_classe",
    "Cpl": "caporal",
    "Cpls": "caporal_section",
    "Sgt": "sergent",
    "Sgts": "sergent_section",
    "Ajd2": "adjudant_2e_classe",
    "Adj1": "adjudant_1re_classe",
}

# Modèles pour l'import
class ImportPreviewRequest(BaseModel):
    """Requête pour prévisualiser l'import"""
    pass  # Le fichier sera envoyé via multipart/form-data

class ImportPreviewResponse(BaseModel):
    """Réponse de prévisualisation"""
    total_rows: int
    new_cadets: List[Dict]
    updated_cadets: List[Dict]
    errors: List[Dict]
    new_sections: List[str]

class ImportConfirmRequest(BaseModel):
    """Confirmation de l'import"""
    changes: List[Dict]
    create_sections: bool = True

# Modèle pour export PDF individuel
class IndividualReportRequest(BaseModel):
    cadet_id: str
    include_presences: bool = True
    include_inspections: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# Fonction utilitaire pour générer un username unique
async def generate_unique_username(prenom: str, nom: str, db) -> str:
    """Génère un username unique basé sur prenom.nom"""
    # Nettoyer et normaliser
    base_username = f"{prenom.lower().strip()}.{nom.lower().strip()}"
    base_username = base_username.replace(" ", "").replace("'", "").replace("-", "")
    
    # Vérifier si existe déjà
    existing = await db.users.find_one({"username": base_username})
    if not existing:
        return base_username
    
    # Si existe, ajouter un numéro
    counter = 1
    while True:
        new_username = f"{base_username}{counter}"
        existing = await db.users.find_one({"username": new_username})
        if not existing:
            return new_username
        counter += 1

# Fonction pour parser le fichier Excel
async def parse_excel_file(file_content: bytes) -> List[Dict]:
    """Parse le fichier Excel et retourne une liste de cadets"""
    try:
        # Lire le fichier Excel avec pandas
        df = pd.read_excel(BytesIO(file_content))
        
        # Vérifier les colonnes nécessaires
        required_cols = ['Nom', 'Prénom', 'Grade', 'Groupe']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Colonnes manquantes: {', '.join(missing_cols)}")
        
        # Filtrer uniquement les colonnes nécessaires
        df = df[required_cols]
        
        # Supprimer les lignes avec valeurs manquantes
        df = df.dropna(subset=['Nom', 'Prénom', 'Grade', 'Groupe'])
        
        # Convertir en liste de dictionnaires
        cadets = df.to_dict('records')
        
        return cadets
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier Excel: {str(e)}")

# Endpoint: Prévisualiser l'import Excel
@api_router.post("/import/cadets/preview")
async def preview_import_cadets(
    file: UploadFile = File(...),
    current_user: User = Depends(lambda u: require_role([UserRole.CADET_ADMIN, UserRole.ENCADREMENT]))
):
    """
    Prévisualise l'import d'un fichier Excel de cadets
    Retourne les changements qui seront appliqués sans les sauvegarder
    """
    try:
        # Lire le contenu du fichier
        content = await file.read()
        
        # Parser le fichier Excel
        cadets_data = await parse_excel_file(content)
        
        # Récupérer les cadets et sections existants
        existing_users = await db.users.find().to_list(1000)
        existing_sections = await db.sections.find().to_list(100)
        
        # Créer des maps pour recherche rapide
        users_by_name = {f"{u['prenom'].lower()}.{u['nom'].lower()}": u for u in existing_users}
        sections_by_name = {s['nom'].lower(): s for s in existing_sections}
        
        new_cadets = []
        updated_cadets = []
        errors = []
        new_sections = set()
        
        for idx, cadet_data in enumerate(cadets_data, start=2):  # Start at 2 (ligne 1 = en-tête)
            try:
                nom = cadet_data['Nom'].strip()
                prenom = cadet_data['Prénom'].strip()
                grade_acronym = cadet_data['Grade'].strip()
                section_name = cadet_data['Groupe'].strip()
                
                # Valider le grade
                if grade_acronym not in GRADE_MAPPING:
                    errors.append({
                        'row': idx,
                        'nom': nom,
                        'prenom': prenom,
                        'error': f"Grade inconnu: {grade_acronym}. Grades valides: {', '.join(GRADE_MAPPING.keys())}"
                    })
                    continue
                
                grade = GRADE_MAPPING[grade_acronym]
                
                # Vérifier si la section existe
                section_lower = section_name.lower()
                section_exists = section_lower in sections_by_name
                
                if not section_exists:
                    new_sections.add(section_name)
                
                # Chercher si le cadet existe déjà
                key = f"{prenom.lower()}.{nom.lower()}"
                existing_user = users_by_name.get(key)
                
                if existing_user:
                    # Cadet existe - vérifier si mise à jour nécessaire
                    changes = []
                    
                    if existing_user['grade'] != grade:
                        changes.append(f"Grade: {existing_user['grade']} → {grade}")
                    
                    existing_section_name = None
                    if existing_user.get('section_id'):
                        existing_section = next((s for s in existing_sections if s['id'] == existing_user['section_id']), None)
                        if existing_section:
                            existing_section_name = existing_section['nom']
                    
                    if existing_section_name != section_name:
                        changes.append(f"Section: {existing_section_name or 'Aucune'} → {section_name}")
                    
                    if changes:
                        updated_cadets.append({
                            'row': idx,
                            'nom': nom,
                            'prenom': prenom,
                            'username': existing_user['username'],
                            'changes': changes,
                            'new_grade': grade,
                            'new_section': section_name
                        })
                else:
                    # Nouveau cadet
                    username = await generate_unique_username(prenom, nom, db)
                    new_cadets.append({
                        'row': idx,
                        'nom': nom,
                        'prenom': prenom,
                        'grade': grade,
                        'section': section_name,
                        'username': username
                    })
                    
            except Exception as e:
                errors.append({
                    'row': idx,
                    'error': f"Erreur: {str(e)}"
                })
        
        return {
            "total_rows": len(cadets_data),
            "new_cadets": new_cadets,
            "updated_cadets": updated_cadets,
            "errors": errors,
            "new_sections": list(new_sections)
        }
        
    except Exception as e:
        logger.error(f"Erreur prévisualisation import: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# Endpoint: Confirmer l'import Excel
@api_router.post("/import/cadets/confirm")
async def confirm_import_cadets(
    request: ImportConfirmRequest,
    current_user: User = Depends(lambda u: require_role([UserRole.CADET_ADMIN, UserRole.ENCADREMENT]))
):
    """
    Confirme et applique l'import de cadets
    """
    try:
        # Récupérer les sections existantes
        existing_sections = await db.sections.find().to_list(100)
        sections_by_name = {s['nom'].lower(): s for s in existing_sections}
        
        new_sections_created = []
        cadets_created = []
        cadets_updated = []
        
        # Créer les nouvelles sections si nécessaire
        if request.create_sections:
            new_section_names = set()
            for change in request.changes:
                if change.get('type') in ['new', 'update']:
                    section_name = change.get('section')
                    if section_name and section_name.lower() not in sections_by_name:
                        new_section_names.add(section_name)
            
            for section_name in new_section_names:
                section_id = str(uuid.uuid4())
                new_section = {
                    "id": section_id,
                    "nom": section_name,
                    "created_at": datetime.now().isoformat()
                }
                await db.sections.insert_one(new_section)
                sections_by_name[section_name.lower()] = new_section
                new_sections_created.append(section_name)
        
        # Appliquer les changements
        for change in request.changes:
            change_type = change.get('type')
            
            if change_type == 'new':
                # Créer nouveau cadet
                nom = change['nom']
                prenom = change['prenom']
                grade = change['grade']
                section_name = change['section']
                username = change['username']
                
                # Récupérer l'ID de section
                section = sections_by_name.get(section_name.lower())
                section_id = section['id'] if section else None
                
                # Créer le cadet
                user_id = str(uuid.uuid4())
                new_user = {
                    "id": user_id,
                    "username": username,
                    "email": f"{username}@cadets.local",  # Email par défaut
                    "nom": nom,
                    "prenom": prenom,
                    "grade": grade,
                    "role": "cadet",
                    "section_id": section_id,
                    "hashed_password": None,  # Pas de mot de passe - sera généré via le bouton
                    "require_password_change": True,
                    "created_at": datetime.now().isoformat()
                }
                
                await db.users.insert_one(new_user)
                cadets_created.append(username)
                
            elif change_type == 'update':
                # Mettre à jour cadet existant
                username = change['username']
                new_grade = change.get('new_grade')
                new_section = change.get('new_section')
                
                update_fields = {}
                
                if new_grade:
                    update_fields['grade'] = new_grade
                
                if new_section:
                    section = sections_by_name.get(new_section.lower())
                    if section:
                        update_fields['section_id'] = section['id']
                
                if update_fields:
                    await db.users.update_one(
                        {"username": username},
                        {"$set": update_fields}
                    )
                    cadets_updated.append(username)
        
        return {
            "success": True,
            "new_sections_created": new_sections_created,
            "cadets_created": len(cadets_created),
            "cadets_updated": len(cadets_updated),
            "details": {
                "created": cadets_created[:10],  # Premiers 10
                "updated": cadets_updated[:10]   # Premiers 10
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur confirmation import: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# Endpoint: Export PDF individuel
@api_router.post("/reports/cadet-individual")
async def generate_individual_cadet_report(
    request: IndividualReportRequest,
    current_user: User = Depends(require_inspection_permissions)
):
    """
    Génère un rapport PDF complet pour un cadet individuel
    """
    try:
        # Récupérer les données du cadet
        cadet = await db.users.find_one({"id": request.cadet_id})
        if not cadet:
            raise HTTPException(status_code=404, detail="Cadet non trouvé")
        
        # Récupérer les données associées
        sections = await db.sections.find().to_list(100)
        section_map = {s['id']: s['nom'] for s in sections}
        section_name = section_map.get(cadet.get('section_id'), 'Sans section')
        
        # Dates par défaut
        end_date = request.end_date or date.today()
        start_date = request.start_date or (end_date - timedelta(days=90))  # 3 mois par défaut
        
        report_data = {
            'cadet': {
                'nom': cadet['nom'],
                'prenom': cadet['prenom'],
                'grade': cadet['grade'],
                'section': section_name,
                'username': cadet['username']
            }
        }
        
        # Statistiques de présences
        if request.include_presences:
            presences = await db.presences.find({
                "cadet_id": request.cadet_id,
                "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
            }).to_list(1000)
            
            total_presences = len(presences)
            presents = len([p for p in presences if p.get('statut') == 'present'])
            absents = len([p for p in presences if p.get('statut') == 'absent'])
            retards = len([p for p in presences if p.get('statut') == 'retard'])
            
            taux_presence = (presents / total_presences * 100) if total_presences > 0 else 0
            
            report_data['presences'] = {
                'total': total_presences,
                'presents': presents,
                'absents': absents,
                'retards': retards,
                'taux': taux_presence
            }
        
        # Statistiques d'inspections
        if request.include_inspections:
            inspections = await db.uniform_inspections.find({
                "cadet_id": request.cadet_id,
                "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
            }).to_list(1000)
            
            if inspections:
                avg_score = sum(i['total_score'] for i in inspections) / len(inspections)
                best_score = max(i['total_score'] for i in inspections)
                worst_score = min(i['total_score'] for i in inspections)
                
                # Scores par type d'uniforme
                by_uniform = {}
                for insp in inspections:
                    uniform_type = insp['uniform_type']
                    if uniform_type not in by_uniform:
                        by_uniform[uniform_type] = []
                    by_uniform[uniform_type].append(insp['total_score'])
                
                uniform_averages = {
                    utype: sum(scores) / len(scores)
                    for utype, scores in by_uniform.items()
                }
                
                report_data['inspections'] = {
                    'total': len(inspections),
                    'average_score': avg_score,
                    'best_score': best_score,
                    'worst_score': worst_score,
                    'by_uniform': uniform_averages,
                    'details': inspections
                }
        
        # Générer le PDF
        from reports_endpoints import generate_individual_cadet_pdf
        pdf_buffer = await generate_individual_cadet_pdf(
            report_data,
            start_date.strftime('%d/%m/%Y'),
            end_date.strftime('%d/%m/%Y')
        )
        
        filename = f"fiche_cadet_{cadet['nom']}_{cadet['prenom']}_{date.today().isoformat()}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur génération rapport individuel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
