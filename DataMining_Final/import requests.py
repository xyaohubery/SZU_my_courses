import os
import shutil
from bs4 import BeautifulSoup
import json # 引入json模块用于保存数据
import time 

# --- 配置项 ---
# !!! 移除 Firebase 相关的配置，因为现在我们将保存到本地文件 !!!
# SERVICE_ACCOUNT_KEY_PATH = r"C:\Users\Law\Desktop\DataMining_Final\final-5b652-firebase-adminsdk-fbsvc-b8796c05bb.json"
# FIRESTORE_PROJECT_ID = "final-5b652"

# 必填：你的 Firebase 项目 ID，例如 "your-project-id"
# 这个仍然保留，因为它用于构建本地输出目录的路径，模拟Firestore集合路径
FIRESTORE_PROJECT_ID = "final-5b652" 

# !!! 新增配置项：本地文档的根目录路径 !!!
# 请将此路径替换为你存放HTML文档的实际路径
LOCAL_DOCS_ROOT_DIR = r"E:\download\python-3.13-docs-html (1)\python-3.13-docs-html" # <--- !!! 请在这里更新你的本地文档路径 !!!

# !!! 新增配置项：保存处理后文档的本地输出目录 !!!
# 脚本会将提取并格式化后的文档保存到这个目录下
LOCAL_OUTPUT_BASE_DIR = "processed_knowledge_base" # 建议保持默认，或根据需要修改

# 构造完整的本地输出路径，模拟 Firestore 集合路径结构
# 这样方便您理解数据是对应哪个项目的哪个知识库
LOCAL_OUTPUT_PATH = os.path.join(
    LOCAL_OUTPUT_BASE_DIR, 
    f"artifacts_{FIRESTORE_PROJECT_ID}_public_data_knowledge_base"
)

# 简单过滤：只保存内容长度大于 100 字符的文档
MIN_CONTENT_LENGTH = 100

# --- 函数定义 ---

def extract_text_from_html(html_file_path):
    """
    从 HTML 文件中提取主要文本内容。
    会移除导航、页眉页脚、脚本、样式、图片、表格、列表等非主要内容，
    并清理多余的空白行。
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # 移除不需要的 HTML 元素，以获取更干净的文本
        for tag in soup(['nav', 'header', 'footer', 'script', 'style', 'aside', 'form', 
                          'link', 'meta', 'img', 'svg', 'hr', 'table', 'ul', 'ol', 'code', 'pre', 'dl']):
            if tag.parent is not None:
                tag.decompose()

        # 尝试查找文档的主体内容区域，通常在 <main> 或特定的 div 中
        main_content = soup.find('main') or soup.find('div', class_='body') or soup.body

        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True) 

        # 进一步清理：移除多余的空行，标准化空白
        text = os.linesep.join([s for s in text.splitlines() if s.strip()])
        return text.strip()
    except Exception as e:
        print(f"提取文本失败：{html_file_path} - {e}")
        return None

def find_html_files(directory):
    """
    递归查找指定目录及其子目录下的所有 HTML 文件。
    """
    html_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".html", ".htm")):
                html_files.append(os.path.join(root, file))
    return html_files

def save_doc_to_local_file(doc_data, output_dir):
    """
    将单个文档内容保存为本地 JSON 文件。
    文件名将基于文档标题生成一个安全且唯一的名字。
    """
    # 使用当前时间戳和随机数生成一个伪唯一ID，模拟Firestore的文档ID
    # 这样可以避免文件名冲突，并保证每个文件都是独立的
    unique_id = int(time.time() * 1000) # 毫秒级时间戳
    
    # 可以在这里根据实际需要，从doc_data中获取一个更具描述性的文件名基础
    # 例如：safe_title = "".join(c for c in doc_data['title'] if c.isalnum() or c in (' ', '.', '_')).rstrip()
    # 为了简化，我们直接使用时间戳作为文件名，保证唯一性
    file_name = f"doc_{unique_id}.json" 
    file_path = os.path.join(output_dir, file_name)

    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 为了与admin.html兼容，我们需要保存的数据结构是：
        # { 'title': '...', 'content': '...', 'createdAt': <timestamp> }
        # 在本地保存时，createdAt可以是一个实际的时间戳，或者一个占位符
        # 这里我们使用当前时间戳
        doc_data['createdAt'] = time.time() # Unix timestamp in seconds
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=4)
        print(f"文档 '{doc_data['title']}' 已保存到本地：{file_path}")
        return True
    except Exception as e:
        print(f"保存文档 '{doc_data['title']}' 到本地失败: {e}")
        return False

# --- 主执行逻辑 ---
if __name__ == "__main__":
    print(f"本地文档根目录: {LOCAL_DOCS_ROOT_DIR}")
    print(f"处理后文档将保存到: {LOCAL_OUTPUT_PATH}")

    # 1. 查找本地文档
    print(f"正在从本地目录 '{LOCAL_DOCS_ROOT_DIR}' 查找 HTML 文件...")
    if not os.path.isdir(LOCAL_DOCS_ROOT_DIR):
        print(f"错误：配置的本地文档目录 '{LOCAL_DOCS_ROOT_DIR}' 不存在或不是一个目录。请检查路径。")
        exit() # 退出程序

    html_files = find_html_files(LOCAL_DOCS_ROOT_DIR)
    
    if not html_files:
        print(f"在 '{LOCAL_DOCS_ROOT_DIR}' 中没有找到任何 HTML 文件。请确保路径正确且包含HTML文件。")
        print("程序执行完毕。")
        exit()

    print(f"共找到 {len(html_files)} 篇 HTML 文档。")

    saved_docs_count = 0

    # 2. 遍历、提取并保存文档到本地
    for i, html_file in enumerate(html_files):
        print(f"\n--- 处理文件 {i+1}/{len(html_files)}: {html_file} ---")
        
        # 从 HTML 文件名或其相对路径推断文档标题
        relative_path = os.path.relpath(html_file, LOCAL_DOCS_ROOT_DIR)
        title = os.path.splitext(relative_path)[0].replace(os.sep, ' - ').replace('_', ' ').title()
        
        content = extract_text_from_html(html_file)
        if content:
            # 过滤：只保存内容长度大于 MIN_CONTENT_LENGTH 字符的文档
            if len(content) > MIN_CONTENT_LENGTH: 
                doc_data = {
                    'title': title, 
                    'content': content
                }
                if save_doc_to_local_file(doc_data, LOCAL_OUTPUT_PATH):
                    saved_docs_count += 1
            else:
                print(f"跳过内容过短的文档: '{title}' ({len(content)} 字符，小于 {MIN_CONTENT_LENGTH} 字符)")
        else:
            print(f"未能从 '{html_file}' 提取有效内容。")
    
    print("\n--- 文档处理和本地保存完成 ---")
    print(f"成功处理并保存了 {saved_docs_count} 篇有效文档到 '{LOCAL_OUTPUT_PATH}' 目录。")
    print("您现在可以手动将这些JSON文件上传到您的Firestore数据库。")

    print("\n程序执行完毕。")