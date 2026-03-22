# app/route/test.py
from fastapi import APIRouter, File, UploadFile
from app.lib.ai_receipt import extract_receipt_info

router = APIRouter()

@router.get("/test")
async def test():
    return {"message": "Test route works! version27"}

@router.post("/test-receipt")
async def test_receipt(receipt: UploadFile = File(...)):
    result = await extract_receipt_info(receipt)
    if result is None:
        return {
            "status": False,
            "cashflow": None,
            "description": None,
        }

    return {
        "status": True,
        "date": result.get("date"),
        "cashflow": result.get("cashflow"),
        "description": result.get("description"),
    }