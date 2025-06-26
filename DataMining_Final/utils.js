// utils.js - 彻底移除所有 Firebase 依赖

// Custom Modal Elements (假设它们存在于 HTML 中)
// 这些元素必须在调用 showModal 的 HTML 页面中存在
const customModal = document.getElementById('custom-modal');
const modalMessage = document.getElementById('modal-message');
const modalConfirmBtn = document.getElementById('modal-confirm-btn');
const modalCancelBtn = document.getElementById('modal-cancel-btn');


/**
 * 初始化函数（现在不包含Firebase逻辑，仅用于概念上的初始化完成）
 * @param {Function} [onInitialized] - 回调函数，在模拟初始化完成后执行
 */
export async function initializeApplication(onInitialized) {
    console.log("前端应用初始化完成 (无Firebase)。");
    // 模拟异步初始化过程
    await new Promise(resolve => setTimeout(resolve, 100)); 
    if (onInitialized) {
        onInitialized();
    }
}

/**
 * 在指定的HTML元素中显示消息。
 * @param {string} message - 要显示的消息。
 * @param {'info'|'error'|'success'} type - 消息类型（影响颜色）。
 * @param {HTMLElement} element - 显示消息的HTML元素。
 */
export function displayMessage(message, type = 'info', element) {
    if (!element) {
        console.warn("displayMessage: Target element is null or undefined.", message);
        return;
    }
    let colorClass = 'text-gray-600';
    if (type === 'error') colorClass = 'text-red-600';
    if (type === 'success') colorClass = 'text-green-600';
    element.innerHTML = `<p class="font-semibold ${colorClass}">${message}</p>`;
}

/**
 * 格式化文本以供显示（例如，将换行符替换为<br>）。
 * @param {string} text - 要格式化的文本。
 * @returns {string} - 格式化后的HTML字符串。
 */
export function formatText(text) {
    // 简单的 Markdown 到 HTML 转换
    // 粗体
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // 斜体
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // 标题 (H1-H3)
    text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    // 列表 (无序)
    text = text.replace(/^\s*[-*+] (.*)$/gim, '<li>$1</li>');
    if (text.includes('<li>')) {
        text = `<ul>${text}</ul>`;
    }
    // 代码块
    text = text.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
    // 行内代码
    text = text.replace(/`(.*?)`/g, '<code>$1</code>');
    // 链接
    text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" class="text-blue-600 hover:underline">$1</a>');

    // 最后替换所有换行符为 <br>，但避免在 pre 标签内替换
    text = text.replace(/(?<!<\/code>)(?<!<\/pre>)\n(?!<pre>)(?!<code>)/g, '<br>');


    return text;
}

/**
 * 显示自定义模态框用于警报或确认。
 * IMPORTANT: 此函数假定 customModal, modalMessage, modalConfirmBtn, modalCancelBtn
 * DOM元素存在于使用此函数的HTML页面中。
 * @param {string} message - 要显示的消息。
 * @param {'alert'|'confirm'} type - 模态框类型（'alert'或'confirm'）。
 * @returns {Promise<boolean>} - 如果是'confirm'，确认则解析为true，取消则解析为false。如果是'alert'，始终解析为true。
 */
export function showModal(message, type = 'alert') {
    // 在这里重新获取 modal 元素，因为它们可能在 DOMContentLoaded 之后才可用
    const customModal = document.getElementById('custom-modal');
    const modalMessage = document.getElementById('modal-message');
    const modalConfirmBtn = document.getElementById('modal-confirm-btn');
    const modalCancelBtn = document.getElementById('modal-cancel-btn');

    if (!customModal || !modalMessage || !modalConfirmBtn || !modalCancelBtn) {
        console.error("Modal elements are not found in the DOM. Ensure #custom-modal, #modal-message, #modal-confirm-btn, #modal-cancel-btn exist.");
        // 如果模态框元素缺失，则回退到原生 alert/confirm
        if (type === 'confirm') {
            return Promise.resolve(confirm(message));
        } else {
            alert(message);
            return Promise.resolve(true);
        }
    }

    modalMessage.textContent = message;
    customModal.style.display = 'flex'; // 显示模态框

    return new Promise((resolve) => {
        if (type === 'alert') {
            modalCancelBtn.style.display = 'none'; // 警报时隐藏取消按钮
            modalConfirmBtn.textContent = '确定';
            modalConfirmBtn.onclick = () => {
                customModal.style.display = 'none';
                resolve(true);
            };
        } else if (type === 'confirm') {
            modalCancelBtn.style.display = 'inline-block'; // 确认时显示取消按钮
            modalConfirmBtn.textContent = '确定';
            modalConfirmBtn.onclick = () => {
                customModal.style.display = 'none';
                resolve(true);
            };
            modalCancelBtn.onclick = () => {
                customModal.style.display = 'none';
                resolve(false);
            };
        }
    });
}
