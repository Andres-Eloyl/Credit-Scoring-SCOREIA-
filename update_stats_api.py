import os
import re

api_path = r'app\main_api.py'
with open(api_path, 'r', encoding='utf-8') as f:
    api = f.read()

# Replace the current /api/stats endpoint
old_stats = """@app.get("/api/stats")
async def get_stats(db: Session = Depends(database.get_db)):

    total = db.query(models.Evaluation).count()
    if total == 0:
        return {"total": 0, "aprobados": 0, "rechazados": 0, "monto_total": 0, "pd_promedio": 0, "history_dates": [], "history_aprobados": [], "history_rechazados": []}

    aprobados = db.query(models.Evaluation).filter(models.Evaluation.decision == "Aprobado").count()
    rechazados = total - aprobados

    monto_total = db.query(func.sum(models.Evaluation.monto_solicitado)).scalar() or 0

    pd_promedio = db.query(func.avg(models.Evaluation.pd_value)).scalar() or 0

    return {
        "total": total,
        "aprobados": aprobados,
        "rechazados": rechazados,
        "monto_total": monto_total,
        "pd_promedio": pd_promedio
    }"""

new_stats = """@app.get("/api/stats")
async def get_stats(db: Session = Depends(database.get_db)):

    total = db.query(models.Evaluation).count()
    if total == 0:
        return {"total": 0, "aprobados": 0, "rechazados": 0, "monto_total": 0, "pd_promedio": 0, "history_dates": [], "history_aprobados": [], "history_rechazados": []}

    aprobados = db.query(models.Evaluation).filter(models.Evaluation.decision == "Aprobado").count()
    rechazados = total - aprobados

    monto_total = db.query(func.sum(models.Evaluation.monto_solicitado)).scalar() or 0

    pd_promedio = db.query(func.avg(models.Evaluation.pd_value)).scalar() or 0

    # Trend logic (Group by date)
    # Using SQLite date() function
    from sqlalchemy import func
    
    daily_stats = db.query(
        func.date(models.Evaluation.created_at).label('eval_date'),
        func.sum(case((models.Evaluation.decision == 'Aprobado', 1), else_=0)).label('aprobados'),
        func.sum(case((models.Evaluation.decision == 'Rechazado', 1), else_=0)).label('rechazados')
    ).group_by(func.date(models.Evaluation.created_at)).order_by(func.date(models.Evaluation.created_at).asc()).limit(14).all()

    dates = [row.eval_date for row in daily_stats]
    trend_aprobados = [row.aprobados for row in daily_stats]
    trend_rechazados = [row.rechazados for row in daily_stats]

    return {
        "total": total,
        "aprobados": aprobados,
        "rechazados": rechazados,
        "monto_total": monto_total,
        "pd_promedio": pd_promedio,
        "history_dates": dates,
        "history_aprobados": trend_aprobados,
        "history_rechazados": trend_rechazados
    }"""

# Add case to imports if needed
if "from sqlalchemy import case" not in api and "case" in new_stats:
    api = api.replace("from sqlalchemy.orm import Session", "from sqlalchemy.orm import Session\nfrom sqlalchemy import case")

if old_stats in api:
    api = api.replace(old_stats, new_stats)
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write(api)
    print("Updated main_api.py with trend logic")
else:
    print("Could not find old stats endpoint")
