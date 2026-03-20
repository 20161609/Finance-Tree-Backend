# app/firebase/init.py

import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials

load_dotenv()


def initialize_firebase():
    if firebase_admin._apps:
        return

    private_key = (os.getenv("FIREBASE_PRIVATE_KEY") or "").replace("\\n", "\n")
    service_account_key = {
        "type": os.getenv("FIREBASE_TYPE"),
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": private_key,
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
    }

    cred = credentials.Certificate(service_account_key)

    firebase_admin.initialize_app(
        cred,
        {
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        },
    )