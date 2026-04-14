import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# 修正 1：這一行前面不能有空格，必須貼齊左邊
collection_ref = db.collection("靜宜資管2026a")

# 修正 2：Firestore 沒有 .order_get()，一般讀取是用 .get()
docs = collection_ref.get()

keyword = input("您要查詢老師的名字或關鍵字：")

for doc in docs:
    user = doc.to_dict()
    # 修正 3：邏輯判斷應該是「關鍵字是否在名字裡」，且 print 前面要縮排
    if keyword in user['name']:
        print(f"{user['name']}老師研究室在{user['lab']}")