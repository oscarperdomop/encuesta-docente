"""
Script para probar el guardado de Q16 en la base de datos.
Ejecutar desde: backend/api/
Comando: python test_q16_save.py
"""
import sys
import os
from uuid import UUID

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.models.attempt import Attempt, Response as AttemptResponse
from app.models.encuesta import Question

def test_q16_save():
    print("=" * 70)
    print("TEST DE GUARDADO DE Q16")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # 1. Buscar un attempt reciente
        print("\n1. Buscando attempts recientes...")
        recent_attempts = (
            db.query(Attempt)
            .filter(Attempt.estado == "enviado")
            .order_by(Attempt.actualizado_en.desc())
            .limit(5)
            .all()
        )
        
        if not recent_attempts:
            print("❌ No se encontraron attempts enviados")
            return
        
        print(f"✅ Encontrados {len(recent_attempts)} attempts enviados recientes\n")
        
        # 2. Buscar Q16 en la encuesta
        for att in recent_attempts:
            print(f"\n{'='*70}")
            print(f"Attempt ID: {att.id}")
            print(f"Survey ID: {att.survey_id}")
            print(f"Estado: {att.estado}")
            print(f"Actualizado: {att.actualizado_en}")
            
            # Buscar Q16
            q16 = (
                db.query(Question)
                .filter(
                    Question.survey_id == att.survey_id,
                    Question.codigo == "Q16"
                )
                .first()
            )
            
            if not q16:
                print(f"⚠️  Q16 NO encontrada para esta encuesta")
                continue
            
            print(f"\n✅ Q16 encontrada - ID: {q16.id}")
            print(f"   Código: {q16.codigo}")
            print(f"   Enunciado: {q16.enunciado[:50]}...")
            
            # Buscar respuesta Q16 para este attempt
            q16_response = (
                db.query(AttemptResponse)
                .filter(
                    AttemptResponse.attempt_id == att.id,
                    AttemptResponse.question_id == q16.id
                )
                .first()
            )
            
            if q16_response:
                print(f"\n✅ RESPUESTA Q16 ENCONTRADA:")
                print(f"   Response ID: {q16_response.id}")
                print(f"   Texto guardado: {q16_response.texto}")
            else:
                print(f"\n❌ NO SE ENCONTRÓ respuesta Q16 para este attempt")
            
            # Contar todas las respuestas de este attempt
            total_responses = (
                db.query(AttemptResponse)
                .filter(AttemptResponse.attempt_id == att.id)
                .count()
            )
            print(f"\n📊 Total respuestas guardadas: {total_responses}")
            
        # 3. Estadísticas generales
        print(f"\n{'='*70}")
        print("ESTADÍSTICAS GENERALES:")
        print(f"{'='*70}")
        
        total_q16_responses = (
            db.query(AttemptResponse)
            .join(Question, AttemptResponse.question_id == Question.id)
            .filter(Question.codigo == "Q16")
            .count()
        )
        
        total_attempts = db.query(Attempt).filter(Attempt.estado == "enviado").count()
        
        print(f"Total attempts enviados: {total_attempts}")
        print(f"Total respuestas Q16 guardadas: {total_q16_responses}")
        
        if total_attempts > 0:
            percentage = (total_q16_responses / total_attempts) * 100
            print(f"Porcentaje de Q16 completadas: {percentage:.1f}%")
        
        # 4. Mostrar una muestra de Q16 guardadas
        print(f"\n{'='*70}")
        print("MUESTRA DE RESPUESTAS Q16 GUARDADAS:")
        print(f"{'='*70}")
        
        sample_q16 = (
            db.query(AttemptResponse, Question, Attempt)
            .join(Question, AttemptResponse.question_id == Question.id)
            .join(Attempt, AttemptResponse.attempt_id == Attempt.id)
            .filter(Question.codigo == "Q16", AttemptResponse.texto.isnot(None))
            .order_by(AttemptResponse.created_at.desc())
            .limit(3)
            .all()
        )
        
        if sample_q16:
            for resp, q, att in sample_q16:
                print(f"\n--- Respuesta {resp.id} ---")
                print(f"Attempt: {att.id}")
                print(f"Fecha: {resp.created_at}")
                print(f"Texto: {resp.texto}")
        else:
            print("\n❌ NO SE ENCONTRARON respuestas Q16 en la base de datos")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print(f"\n{'='*70}")
    print("FIN DEL TEST")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    test_q16_save()
