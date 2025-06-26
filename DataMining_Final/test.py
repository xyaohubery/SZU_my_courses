import firebase_admin
from firebase_admin import credentials, firestore
import time
import os
import requests # 新增导入 requests 库

# --- 配置项 ---
# 请替换为你的服务账号密钥路径
SERVICE_ACCOUNT_KEY_PATH = './final-5b652-firebase-adminsdk-fbsvc-b8796c05bb.json'
# 请替换为你的Firebase项目ID
FIRESTORE_PROJECT_ID = 'final-5b652'

def test_firebase_connection():
    print("--- 正在测试 Firebase Admin SDK 连接 ---")

    if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
        print(f"错误: 服务账号密钥文件 '{SERVICE_ACCOUNT_KEY_PATH}' 不存在。请检查路径。")
        return

    # --- 第一步：直接测试到 Google API 的网络连通性 ---
    print("\n--- 深入网络连通性测试 (直接请求 Google API 端点) ---")
    google_api_test_url = "https://firestore.googleapis.com/" # 这是一个 Firebase Firestore 服务的公共 API 端点
    try:
        # 设置一个短的超时时间，强制快速失败如果连接被阻塞
        response = requests.get(google_api_test_url, timeout=5) 
        response.raise_for_status() # 如果状态码不是2xx，则抛出HTTPError
        print(f"成功直接连接到 {google_api_test_url}。状态码: {response.status_code}")
        print("这表明您的Python程序可以直接访问Google服务。")
    except requests.exceptions.ConnectTimeout:
        print(f"**致命错误:** 连接到 {google_api_test_url} 超时 (5秒)。这意味着您的网络或防火墙正在阻止Python建立出站连接。")
        print("请检查网络连接、防火墙设置或代理配置。")
        return # 如果这一步失败，后面的Firebase测试也会失败，直接返回
    except requests.exceptions.ConnectionError as e:
        print(f"**致命错误:** 无法连接到 {google_api_test_url}。连接错误: {e}")
        print("这通常是DNS解析失败、网络不通、或防火墙阻止。")
        return # 如果这一步失败，后面的Firebase测试也会失败，直接返回
    except requests.exceptions.RequestException as e:
        print(f"**警告:** 请求 {google_api_test_url} 时发生其他错误: {e}")
        print("这可能是SSL证书问题或服务器响应异常，但网络连接本身可能成功。继续尝试Firebase SDK初始化。")
    print("--------------------------------------------------\n")


    # --- 第二步：尝试初始化 Firebase Admin SDK ---
    try:
        print("尝试初始化 Firebase Admin SDK...")
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred, {
            'projectId': FIRESTORE_PROJECT_ID,
        })
        db = firestore.client()
        print("Firebase Admin SDK 初始化成功！")

        # --- 第三步：尝试从 Firestore 读取数据 ---
        print("\n尝试从 Firestore 读取文档...")
        
        # 假设您的知识库集合名为 'knowledge_base'
        docs_ref = db.collection('knowledge_base').limit(3) 
        
        print("正在发送 Firestore 文档获取请求...")
        # 使用 get() 进行单次明确的获取。Firebase SDK 内部有自己的超时机制，这里不再显式设置requests的timeout
        docs = docs_ref.get() 
        print("Firestore 文档获取请求已完成。")

        found_docs = False
        for doc_item in docs:
            print(f"成功读取文档: {doc_item.id} => {doc_item.to_dict().get('title', '无标题')}")
            found_docs = True
        
        if not found_docs:
            print("Firestore 'knowledge_base' 集合中没有找到文档，或者集合为空。但连接 Firestore 成功。")
        
        print("\nFirebase 连接测试完成。")

    except Exception as e:
        # 这个except块会捕获Firebase SDK内部可能抛出的异常，例如权限问题、API限制、或SDK内部网络错误等
        print(f"\n--- Firebase SDK 操作测试失败！---")
        print(f"错误类型: {type(e).__name__}")
        print(f"详细错误信息: {e}")
        print("这通常是由于 Firebase 服务账号权限不足、Firestore 安全规则限制、或在成功连接Google服务后SDK内部发生的其他问题。")
        print("如果上面 '深入网络连通性测试' 成功，请重点检查 Firebase 项目配置和安全规则。")

if __name__ == "__main__":
    test_firebase_connection()

