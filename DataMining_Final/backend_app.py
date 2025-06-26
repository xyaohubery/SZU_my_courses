import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
import faiss 
import numpy as np
import json
import time
import requests 
from bs4 import BeautifulSoup # 用于HTML文件处理，尽管前端不再直接上传HTML，但后端可以处理

# --- 配置项 ---
# 本地知识库文档存储目录
# 请确保此目录存在，或者您的应用有权限创建它
LOCAL_KB_DIR = 'local_knowledge_base_docs' 
os.makedirs(LOCAL_KB_DIR, exist_ok=True) # 如果目录不存在则创建

# RAG模型配置
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
FAISS_INDEX_PATH = 'knowledge_base.bin'
DOC_METADATA_PATH = 'knowledge_base_metadata.json'

# --- Flask 应用初始化 ---
app = Flask(__name__)
# 允许所有来源的请求，开发阶段方便，生产环境应限制为您的前端域名
CORS(app) 

# --- 向量模型和向量数据库初始化 ---
embedding_model = None 
faiss_index = None     
doc_metadata = []      

def load_embedding_model():
    """加载 SentenceTransformer 嵌入模型。"""
    global embedding_model
    if embedding_model is None:
        print(f"正在加载嵌入模型: {EMBEDDING_MODEL_NAME}...")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("嵌入模型加载完成。")
    return embedding_model

def load_faiss_index():
    """加载或创建 FAISS 索引和对应的元数据。"""
    global faiss_index, doc_metadata
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(DOC_METADATA_PATH):
        print("正在加载现有 FAISS 索引和元数据...")
        faiss_index = faiss.read_index(FAISS_INDEX_PATH) 
        with open(DOC_METADATA_PATH, 'r', encoding='utf-8') as f:
            doc_metadata = json.load(f) 
        print(f"加载了 {len(doc_metadata)} 个文本块。")
    else:
        print("未找到现有 FAISS 索引或元数据，将创建一个新的。")
        embedding_dim = load_embedding_model().get_sentence_embedding_dimension()
        faiss_index = faiss.IndexFlatL2(embedding_dim)
        doc_metadata = []
    return faiss_index

with app.app_context(): 
    load_embedding_model()
    load_faiss_index()

def chunk_text(text, chunk_size=500, overlap=50):
    """
    将长文本分割成较小的文本块，并支持重叠。
    Args:
        text (str): 待分块的原始文本。
        chunk_size (int): 每个文本块的最大字符数。
        overlap (int): 文本块之间的重叠字符数。
    Returns:
        list: 包含文本块字符串的列表。
    """
    chunks = []
    # 简单按字符计数分块，支持中文
    words = list(text) 
    current_chunk = []
    current_len = 0

    for i, char in enumerate(words):
        current_chunk.append(char)
        current_len += 1 

        if current_len >= chunk_size:
            chunk_content = "".join(current_chunk)
            chunks.append(chunk_content)

            overlap_start_index = max(0, len(current_chunk) - overlap)
            current_chunk = current_chunk[overlap_start_index:]
            current_len = len(current_chunk)

    if current_chunk: 
        chunks.append("".join(current_chunk))
    return chunks


# --- API 端点 ---

# 新增端点：上传并保存文档到本地知识库
@app.route('/upload_local_doc', methods=['POST'])
def upload_local_doc():
    """
    接收前端上传的JSON格式文档数据，并保存到本地知识库目录。
    支持单个文档的上传。
    """
    if not request.json:
        return jsonify({"success": False, "message": "请求必须是JSON格式。"}), 400

    title = request.json.get('title')
    content = request.json.get('content')

    if not title or not content:
        return jsonify({"success": False, "message": "文档标题和内容不能为空。"}), 400

    # 生成唯一的文件名
    filename = f"{int(time.time())}_{title.replace(' ', '_').replace('/', '_')[:50]}.json"
    filepath = os.path.join(LOCAL_KB_DIR, filename)

    doc_data = {
        "title": title,
        "content": content,
        "createdAt": time.time()
    }

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=4)
        print(f"成功保存本地文档: {filename}")
        return jsonify({"success": True, "message": f"文档 '{title}' 已成功保存到本地知识库。", "doc_id": filename}), 200
    except Exception as e:
        print(f"保存本地文档失败: {e}")
        return jsonify({"success": False, "message": f"保存文档失败: {str(e)}"}), 500

# 新增端点：批量上传JSON文件到本地知识库
@app.route('/upload_local_json_files', methods=['POST'])
def upload_local_json_files():
    """
    接收前端批量上传的JSON文件，并保存到本地知识库目录。
    """
    if not request.files:
        return jsonify({"success": False, "message": "没有接收到文件。"}), 400

    successful_uploads = 0
    failed_uploads = 0
    
    for key in request.files:
        file = request.files[key]
        if file.filename.endswith('.json'):
            try:
                json_content = json.loads(file.read().decode('utf-8'))
                title = json_content.get('title')
                content = json_content.get('content')

                if not title or not content:
                    print(f"文件 {file.filename} 格式不正确，缺少标题或内容。")
                    failed_uploads += 1
                    continue

                filename = f"{int(time.time())}_{title.replace(' ', '_').replace('/', '_')[:50]}.json"
                filepath = os.path.join(LOCAL_KB_DIR, filename)

                doc_data = {
                    "title": title,
                    "content": content,
                    "createdAt": time.time()
                }

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(doc_data, f, ensure_ascii=False, indent=4)
                
                print(f"成功保存本地文件: {filename}")
                successful_uploads += 1
            except Exception as e:
                print(f"处理文件 {file.filename} 失败: {e}")
                failed_uploads += 1
        else:
            print(f"文件 {file.filename} 不是JSON文件。")
            failed_uploads += 1

    message = f"成功上传 {successful_uploads} 个文件，失败 {failed_uploads} 个。"
    return jsonify({"success": True, "message": message, "successful": successful_uploads, "failed": failed_uploads}), 200


# 新增端点：列出本地知识库中的所有文档
@app.route('/list_local_docs', methods=['GET'])
def list_local_docs():
    """
    列出本地知识库目录中的所有文档（文件）。
    返回文档ID（文件名）和标题。
    """
    docs_list = []
    try:
        for filename in os.listdir(LOCAL_KB_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(LOCAL_KB_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        docs_list.append({
                            "id": filename, # 使用文件名作为文档ID
                            "title": doc_data.get('title', '无标题文档'),
                            "createdAt": doc_data.get('createdAt', 0) # 方便排序
                        })
                except Exception as e:
                    print(f"读取本地文件 {filename} 失败: {e}")
        # 按创建时间倒序排序
        docs_list.sort(key=lambda x: x['createdAt'], reverse=True)
        return jsonify({"success": True, "docs": docs_list}), 200
    except Exception as e:
        print(f"列出本地文档失败: {e}")
        return jsonify({"success": False, "message": f"列出文档失败: {str(e)}"}), 500

# 新增端点：删除本地知识库中的文档
@app.route('/delete_local_doc/<string:doc_id>', methods=['DELETE'])
def delete_local_doc(doc_id):
    """
    删除本地知识库目录中的指定文档文件。
    doc_id 即为文件名。
    """
    filepath = os.path.join(LOCAL_KB_DIR, doc_id)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"成功删除本地文档: {doc_id}")
            return jsonify({"success": True, "message": f"文档 '{doc_id}' 已删除。"}), 200
        else:
            return jsonify({"success": False, "message": "文档未找到。"}), 404
    except Exception as e:
        print(f"删除本地文档失败: {e}")
        return jsonify({"success": False, "message": f"删除文档失败: {str(e)}"}), 500


# MODIFIED 端点：从本地知识库构建向量数据库
@app.route('/ingest_knowledge_base', methods=['POST'])
def ingest_knowledge_base():
    """
    扫描本地知识库目录，读取所有JSON文档，分块，向量化，并构建FAISS索引。
    """
    global faiss_index, doc_metadata 
    
    embedding_dim = load_embedding_model().get_sentence_embedding_dimension()
    faiss_index = faiss.IndexFlatL2(embedding_dim) 
    doc_metadata = [] 

    processed_doc_count = 0
    vectors_to_add = [] 

    try:
        for filename in os.listdir(LOCAL_KB_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(LOCAL_KB_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        content = doc_data.get('content')
                        title = doc_data.get('title', filename) # 如果没有标题，使用文件名

                        if not content:
                            print(f"警告: 文件 {filename} 没有内容，跳过。")
                            continue
                        
                        chunks = chunk_text(content)
                        
                        for i, chunk in enumerate(chunks):
                            embedding = embedding_model.encode(chunk, convert_to_tensor=False)
                            vectors_to_add.append(embedding)
                            
                            doc_metadata.append({
                                "local_doc_id": filename, # 使用文件名作为本地文档ID
                                "title": title,
                                "chunk_index": i,
                                "chunk_content": chunk 
                            })
                        processed_doc_count += 1
                except Exception as e:
                    print(f"读取或处理本地文件 {filename} 失败: {e}")
                    continue # 继续处理下一个文件
        
        if vectors_to_add:
            faiss_index.add(np.array(vectors_to_add).astype('float32'))
            faiss.write_index(faiss_index, FAISS_INDEX_PATH)
            with open(DOC_METADATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(doc_metadata, f, ensure_ascii=False, indent=4)
        
        print(f"成功处理了 {processed_doc_count} 个本地文档，并构建了包含 {len(doc_metadata)} 个文本块的向量知识库。")
        return jsonify({
            "success": True,
            "message": f"成功处理了 {processed_doc_count} 个本地文档，并构建了包含 {len(doc_metadata)} 个文本块的向量知识库。",
            "total_chunks_indexed": len(doc_metadata)
        })

    except Exception as e:
        print(f"摄取数据时发生错误: {e}")
        return jsonify({"success": False, "message": f"摄取数据失败: {str(e)}。请检查后端日志。"}), 500

# RAG 查询端点 (保持不变，因为它只依赖于FAISS索引和DeepSeek API)
@app.route('/ask_rag', methods=['POST'])
def ask_rag():
    data = request.json
    question = data.get('question')
    deepseek_api_key = data.get('deepseek_api_key')
    
    if not question or not deepseek_api_key:
        return jsonify({"error": "缺少问题或 DeepSeek API 密钥。"}), 400

    if faiss_index is None or faiss_index.ntotal == 0:
        return jsonify({"error": "向量知识库为空或未加载。请先在管理界面点击 '从 Firestore 重新构建向量知识库'。"}), 500

    try:
        query_embedding = embedding_model.encode(question, convert_to_tensor=False).astype('float32')
        query_embedding = np.array([query_embedding]) 

        k_neighbors = 3 
        D, I = faiss_index.search(query_embedding, k=k_neighbors)
        
        retrieved_contexts = []
        for index in I[0]:
            if 0 <= index < len(doc_metadata): 
                retrieved_contexts.append(doc_metadata[index]['chunk_content'])
        
        if not retrieved_contexts:
            return jsonify({"answer": "抱歉，未能从知识库中检索到与您问题相关的信息。请尝试换个提问方式或联系管理员添加更多知识库内容。"}), 200

        context_str = "\n".join(retrieved_contexts)

        prompt = f"""您是Python知识问答助手。请根据以下提供的Python文档内容来回答问题。
如果文档中没有足够的信息来回答问题，请直接回答“抱歉，根据我当前知识库中的信息，我无法回答您的问题。”

--- Python文档内容 ---
{context_str}

--- 用户问题 ---
{question}

请清晰、简洁地回答。如果需要，可以使用 Markdown 格式来更好地组织答案。
"""
        deepseek_api_url = "https://api.deepseek.com/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {deepseek_api_key}'
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的Python知识问答助手，只根据提供的文档回答问题。"},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "max_tokens": 1500
        }
        
        response = requests.post(deepseek_api_url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()

        deepseek_result = response.json()
        llm_answer = deepseek_result['choices'][0]['message']['content']

        return jsonify({"answer": llm_answer})

    except requests.exceptions.RequestException as req_err:
        print(f"调用 DeepSeek API 时发生网络或HTTP错误: {req_err}")
        return jsonify({"error": f"调用DeepSeek API失败: {str(req_err)}。请检查网络或API密钥。"}), 500
    except Exception as e:
        print(f"RAG 查询时发生内部错误: {e}")
        return jsonify({"error": f"处理请求时发生错误: {str(e)}。请检查后端日志。"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
