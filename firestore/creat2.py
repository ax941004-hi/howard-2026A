import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "郭澔澄",
  "mail": "ax941004",
  "lab": 111
}

doc_ref = db.collection("靜宜資管2026a").document("Howard")
doc_ref.set(doc)
