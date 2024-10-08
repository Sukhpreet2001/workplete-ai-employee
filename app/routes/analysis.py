from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query,Form
from fastapi.responses import FileResponse,JSONResponse
from app.utils.file_handler import read_file
from app.services.data_processing import clean_data, preprocess_data
from app.services.analysis_engine import AnalysisEngine
from app.services.report_generator import ReportGenerator
import io
from pydantic import BaseModel
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import LabelEncoder
import os
import uuid
from datetime import datetime


router = APIRouter()

# Existing data processing endpoint
@router.post("/process/")
async def process_file(file: UploadFile = File(...)):
    # Read the file contents
    contents = await file.read()
    file_like_object = io.BytesIO(contents)

    # Read the file using the read_file function, passing the filename
    df = read_file(file_like_object, file.filename)

    # Clean the data
    df_cleaned = clean_data(df)

    # Preprocess the data
    df_preprocessed = preprocess_data(df_cleaned)

    return {"status": "success", "columns": df_preprocessed.columns.tolist()}

# Analysis Engine Endpoints

# Request models
class LinearRegressionRequest(BaseModel):
    target_column: str

class DecisionTreeRequest(BaseModel):
    target_column: str
    feature_columns: str
    max_depth: int = None

class CLICommand(BaseModel):
    command: str

@router.post("/descriptive/")
async def get_descriptive_statistics(file: UploadFile = File(...)):
    contents = await file.read()
    file_like_object = io.BytesIO(contents)
    df = read_file(file_like_object, file.filename)
    
    analysis_engine = AnalysisEngine(df)
    result = analysis_engine.descriptive_statistics()
    return {"descriptive_statistics": result}

@router.post("/linear_regression/")
async def linear_regression(
    file: UploadFile = File(...),
    x_column: str = Query(..., alias="x"),
    y_column: str = Query(..., alias="y")
):
    # Read the CSV file
    df = pd.read_csv(file.file)

    if x_column not in df.columns or y_column not in df.columns:
        raise HTTPException(status_code=400, detail="Invalid column names.")

    # Encode categorical data if necessary
    if df[x_column].dtype == 'object':
        le = LabelEncoder()
        df[x_column] = le.fit_transform(df[x_column])
    
    if df[y_column].dtype == 'object':
        le = LabelEncoder()
        df[y_column] = le.fit_transform(df[y_column])

    # Extracting the x and y values
    X = df[[x_column]].values
    y = df[y_column].values

    # Perform linear regression
    model = LinearRegression()
    model.fit(X, y)
    
    # Return the slope and intercept
    return {"slope": model.coef_[0], "intercept": model.intercept_}

@router.post("/decision_tree/")
async def decision_tree_regression(
    file: UploadFile = File(...),
    target_column: str = Query(...),
    feature_columns: str = Query(...)
):
    contents = await file.read()
    file_like_object = io.BytesIO(contents)
    df = pd.read_csv(file_like_object)

    feature_columns = feature_columns.split(",")

    if target_column not in df.columns or any(col not in df.columns for col in feature_columns):
        raise HTTPException(status_code=400, detail="Invalid column names.")

    analysis_engine = AnalysisEngine(df)
    result = analysis_engine.decision_tree_regression(target_column, feature_columns)
    
    return result
@router.post("/generate_report/")
async def generate_report(file: UploadFile = File(...)):
    # Load the uploaded file into a pandas DataFrame
    df = pd.read_csv(file.file)

    # Create a report generator
    report_generator = ReportGenerator(df)

    # Generate a unique filename for the report
    if not os.path.exists("generated_reports/"):
        os.makedirs("generated_reports/")
    
    report_id = f"report_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    output_pdf_path = f"generated_reports/{report_id}"

    # Generate the report
    report_generator.create_report(output_pdf_path)

    # Return the generated report ID and filename
    return {"message": "Report generated successfully.", "report_id": report_id}
@router.post("/cli/")
async def execute_command(cli_command: CLICommand):
    command = cli_command.command.strip()
    
    if command == "help":
        return {"response": "Available commands:\n  upload - Upload files\n  analyze --type [descriptive|linear|tree] - Perform analysis\n  report - Generate report"}
    
    # For simplicity, we just simulate command execution
    # In a real-world scenario, you'd implement actual logic for each command
    if command.startswith("upload"):
        # Handle upload command
        return {"response": "File upload functionality is not implemented yet."}
    elif command.startswith("analyze"):
        # Handle analyze command
        return {"response": "Analysis functionality is not implemented yet."}
    elif command.startswith("report"):
        # Handle report command
        return {"response": "Report generation functionality is not implemented yet."}
    else:
        raise HTTPException(status_code=400, detail=f"Command '{command}' not recognized.")