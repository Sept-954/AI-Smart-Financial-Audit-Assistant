// 聊天页面逻辑
let chatHistory = [];
let isLoading = false;
$(function() {
    loadChatHistory();
    $("#send-btn").on("click", sendMessage);
    $("#question-input").on("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
function loadChatHistory() {
    const saved = getSession("chat_messages");
    if (saved) chatHistory = saved;
    renderMessages();
}
function saveChatHistory() {
    setSession("chat_messages", chatHistory);
}
function renderMessages() {
    const container = $("#messages");
    container.empty();
    chatHistory.forEach(msg => {
        appendMessage(msg.role, msg.content, msg.hasChart, msg.chartHtml);
    });
    container.scrollTop(container.prop("scrollHeight"));
}
function appendMessage(role, content, hasChart, chartHtml) {
    const container = $("#messages");
    const div = $('<div class="chat-message"></div>').addClass(role);
    div.html('<div class="content">' + formatAnswer(escapeHtml(content)) + '</div>');
    if (hasChart && chartHtml) {
        div.append('<div class="chart-container">' + chartHtml + '</div>');
    }
    container.append(div);
    container.scrollTop(container.prop("scrollHeight"));
}
async function sendMessage() {
    if (isLoading) return;
    const input = $("#question-input");
    const question = input.val().trim();
    if (!question) return;
    const docHash = $("#doc-hash").val();
    const apiKey = getApiKey();
    const provider = getProvider();
    const model = getModel();
    if (!apiKey) {
        appendMessage("assistant", "请先在设置中填入 API Key 后再提问。如有需要，可前往 OpenAI 注册获取 Key：https://platform.openai.com/api-keys");
        return;
    }
    if (!docHash) {
        appendMessage("assistant", "请先上传财报 PDF 后再提问。");
        return;
    }
    // 显示用户消息
    chatHistory.push({ role: "user", content: question });
    appendMessage("user", question);
    input.val("");
    isLoading = true;
    $("#send-btn").prop("disabled", true);
    // 显示思考中
    const thinkingDiv = $('<div class="chat-message assistant"><span class="loading-dots">思考中</span></div>');
    $("#messages").append(thinkingDiv);
    try {
        const result = await api("POST", "/chat", {
            doc_hash: docHash,
            question: question,
            api_key: apiKey,
            provider: provider,
            model: model,
        });
        thinkingDiv.remove();
        chatHistory.push({
            role: "assistant",
            content: result.answer,
            hasChart: result.has_chart,
            chartHtml: result.chart_html,
        });
        appendMessage("assistant", result.answer, result.has_chart, result.chart_html);
        saveChatHistory();
    } catch (err) {
        thinkingDiv.remove();
        appendMessage("assistant", "请求失败: " + err.message);
    }
    isLoading = false;
    $("#send-btn").prop("disabled", false);
    input.focus();
}
function clearChat() {
    if (!confirm("确定清除当前对话？此操作不可撤销。")) return;
    chatHistory = [];
    removeSession("chat_messages");
    $("#messages").empty();
}
function downloadReport() {
    if (!chatHistory.length) {
        alert("没有可导出的对话内容。");
        return;
    }
    const history = chatHistory.filter(m => m.role !== "system");
    api("POST", "/export", {
        chat_history: history,
        title: "AI 财报分析报告"
    }).then(blob => {
        // 触发下载
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "财报分析报告.pdf";
        a.click();
    }).catch(err => {
        alert("导出失败: " + err.message);
    });
}
