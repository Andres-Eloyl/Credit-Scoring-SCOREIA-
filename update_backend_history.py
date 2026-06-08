import os
import re

db_path = r'data\scoreia.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print("Deleted scoreia.db")

models_path = r'app\models.py'
with open(models_path, 'r', encoding='utf-8') as f:
    models_content = f.read()

old_evaluation = """class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    client_id = Column(String, index=True)
    edad = Column(Integer)
    ingreso_mensual = Column(Float)
    score_buro = Column(Integer)
    monto_solicitado = Column(Float)
    plazo_meses = Column(Integer)

    pd_value = Column(Float)
    riesgo = Column(String)
    decision = Column(String)"""

new_evaluation = """class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    analyst_name = Column(String, index=True)
    client_id = Column(String, index=True)
    
    monto_solicitado = Column(Float)
    plazo_meses = Column(Integer)
    pd_value = Column(Float)
    riesgo = Column(String)
    decision = Column(String)
    
    request_data = Column(String)
    shap_data = Column(String)"""

models_content = models_content.replace(old_evaluation, new_evaluation)
with open(models_path, 'w', encoding='utf-8') as f:
    f.write(models_content)
print("Updated models.py")

api_path = r'app\main_api.py'
with open(api_path, 'r', encoding='utf-8') as f:
    api_content = f.read()

if "import json" not in api_content:
    api_content = api_content.replace("import os", "import os\nimport json")

old_db_eval = """        db_eval = models.Evaluation(
            client_id=client_id,
            edad=data.get("edad"),
            ingreso_mensual=data.get("ingreso_mensual"),
            score_buro=data.get("score_buro"),
            monto_solicitado=data.get("monto_solicitado"),
            plazo_meses=data.get("plazo_meses"),
            pd_value=pd_val,
            riesgo=riesgo,
            decision=decision_text
        )"""

new_db_eval = """        db_eval = models.Evaluation(
            analyst_name=data.get("analyst_name", "Analista"),
            client_id=client_id,
            monto_solicitado=data.get("monto_solicitado"),
            plazo_meses=data.get("plazo_meses"),
            pd_value=pd_val,
            riesgo=riesgo,
            decision=decision_text,
            request_data=json.dumps(data_dict),
            shap_data=json.dumps(shap_data)
        )"""

api_content = api_content.replace(old_db_eval, new_db_eval)

with open(api_path, 'w', encoding='utf-8') as f:
    f.write(api_content)
print("Updated main_api.py")
