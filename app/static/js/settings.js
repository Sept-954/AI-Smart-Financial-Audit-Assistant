// 设置页逻辑
$(function() {
    loadSettings();
    $("#provider-select").on("change", function() {
        const p = $(this).val();
        updateProviderInfo(p);
        saveSettings();
    });
    $("#api-key-input").on("input", function() {
        validateKeyFormat();
        saveSettings();
    });
    $("#model-input").on("input", saveSettings);
    $("#test-connection").on("click", testConnection);
    $("#clear-data").on("click", clearAllData);
});
function loadSettings() {
    const provider = getProvider();
    const apiKey = getApiKey();
    const model = getModel();
    $("#provider-select").val(provider);
    $("#api-key-input").val(apiKey);
    $("#model-input").val(model);
    updateProviderInfo(provider);
    if (apiKey) {
        $("#key-status").html('<span class="status-dot connected"></span>已配置');
    } else {
        $("#key-status").html('<span class="status-dot disconnected"></span>未配置');
    }
}
function saveSettings() {
    setStorage("provider", $("#provider-select").val());
    setStorage("api_key", $("#api-key-input").val().trim());
    setStorage("model", $("#model-input").val().trim());
}
function updateProviderInfo(provider) {
    const info = {
        openai: { keyLink: "https://platform.openai.com/api-keys", keyLabel: "sk-..." },
        deepseek: { keyLink: "https://platform.deepseek.com/api_keys", keyLabel: "sk-..." },
        qwen: { keyLink: "https://help.aliyun.com/zh/model-studio/getting-started/first-api-call-to-qwen", keyLabel: "sk-..." },
        ollama: { keyLink: "", keyLabel: "无需 API Key（本地部署）" },
    };
    const i = info[provider] || info.openai;
    $("#key-link").attr("href", i.keyLink);
    if (provider === "ollama") {
        $("#api-key-group").hide();
    } else {
        $("#api-key-group").show();
        $("#api-key-input").attr("placeholder", i.keyLabel);
    }
    // 预设模型
    const models = {
        openai: "gpt-4o",
        deepseek: "deepseek-chat",
        qwen: "qwen-plus",
        ollama: "qwen2.5:7b",
    };
    if (!$("#model-input").val()) {
        $("#model-input").val(models[provider] || "");
    }
}
async function validateKeyFormat() {
    const key = $("#api-key-input").val().trim();
    const provider = $("#provider-select").val();
    if (key.length < 8) {
        $("#key-format-status").text("");
        return;
    }
    try {
        const result = await api("POST", "/settings/validate-key", { provider, api_key: key });
        const el = $("#key-format-status");
        if (result.valid) {
            el.html('<span class="badge badge-success">格式正确</span>');
            $("#test-connection").prop("disabled", false);
        } else {
            el.html('<span class="badge badge-warning">' + result.message + '</span>');
            $("#test-connection").prop("disabled", true);
        }
    } catch {}
}
async function testConnection() {
    const provider = $("#provider-select").val();
    const apiKey = $("#api-key-input").val().trim();
    const model = $("#model-input").val().trim();
    $("#test-connection").prop("disabled", true).text("测试中...");
    try {
        const result = await api("POST", "/settings/test-connection", { provider, api_key: apiKey, model });
        if (result.success) {
            showAlert("settings-alert", "success", "连接成功！API Key 有效。");
            $("#key-status").html('<span class="status-dot connected"></span>已连接');
        } else {
            showAlert("settings-alert", "error", result.message);
            $("#key-status").html('<span class="status-dot error"></span>连接失败');
        }
    } catch (err) {
        showAlert("settings-alert", "error", "测试失败: " + err.message);
    }
    $("#test-connection").prop("disabled", false).text("测试连接");
}
async function clearAllData() {
    if (!confirm("确定清除所有数据？\n\n此操作将：\n1. 删除所有已解析的财报索引\n2. 清除存储的 API Key\n3. 清除本地缓存\n\n此操作不可撤销！")) return;
    if (!confirm("再次确认：是否清除所有数据？")) return;
    try {
        await api("POST", "/clear-all");
        localStorage.clear();
        sessionStorage.clear();
        showAlert("settings-alert", "success", "所有数据已清除。页面将刷新...");
        setTimeout(() => location.reload(), 1500);
    } catch (err) {
        showAlert("settings-alert", "error", "清除失败: " + err.message);
    }
}
function updateLocalModelUrl() {
    const url = $("#ollama-url").val();
    if (url) setStorage("ollama_url", url);
}
function resetSettings() {
    if (!confirm("确定重置所有设置？")) return;
    localStorage.removeItem("provider");
    localStorage.removeItem("api_key");
    localStorage.removeItem("model");
    location.reload();
}
