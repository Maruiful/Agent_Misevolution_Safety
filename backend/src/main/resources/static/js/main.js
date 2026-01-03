/**
 * 自进化智能体实验系统 - 主脚本
 *
 * @author Maruiful
 * @version 1.0.0
 */

// 全局变量
let currentExperimentUuid = null;
let statusUpdateInterval = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');

    // 绑定表单提交事件
    const experimentForm = document.getElementById('experimentForm');
    if (experimentForm) {
        experimentForm.addEventListener('submit', handleStartExperiment);
    }

    // 加载实验列表
    loadExperimentList();

    // 检查是否有正在运行的实验
    checkRunningExperiment();
});

/**
 * 实验类型预设值更新
 */
function updateTypeSettings() {
    const type = document.getElementById('experimentType').value;
    const enableMemory = document.getElementById('enableMemory');
    const enableEvolution = document.getElementById('enableEvolution');
    const enableDefense = document.getElementById('enableDefense');
    const shortTermWeight = document.getElementById('shortTermWeight');
    const longTermWeight = document.getElementById('longTermWeight');

    switch(type) {
        case 'baseline':
            // 基线实验：无记忆、无进化、无防御
            enableMemory.checked = false;
            enableEvolution.checked = false;
            enableDefense.checked = false;
            shortTermWeight.value = 0.5;
            longTermWeight.value = 0.5;
            break;
        case 'induced':
            // 诱导实验：有记忆、有进化、无防御、高短期权重
            enableMemory.checked = true;
            enableEvolution.checked = true;
            enableDefense.checked = false;
            shortTermWeight.value = 0.8;
            longTermWeight.value = 0.2;
            break;
        case 'defense':
            // 防御实验：有记忆、有进化、有防御、高短期权重
            enableMemory.checked = true;
            enableEvolution.checked = true;
            enableDefense.checked = true;
            shortTermWeight.value = 0.8;
            longTermWeight.value = 0.2;
            break;
    }
}

/**
 * 处理启动实验
 */
async function handleStartExperiment(event) {
    event.preventDefault();

    const formData = {
        experimentName: document.getElementById('experimentName').value,
        scenario: document.getElementById('scenario').value,
        episodes: parseInt(document.getElementById('episodes').value),
        enableMemory: document.getElementById('enableMemory').checked,
        enableEvolution: document.getElementById('enableEvolution').checked,
        enableDefense: document.getElementById('enableDefense').checked,
        rewardWeights: {
            shortTerm: parseFloat(document.getElementById('shortTermWeight').value),
            longTerm: parseFloat(document.getElementById('longTermWeight').value)
        }
    };

    console.log('启动实验请求:', formData);

    try {
        const response = await fetch('/api/experiment/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.code === 200) {
            alert('实验启动成功！');
            currentExperimentUuid = result.data;
            // 显示正在运行的实验卡片
            showRunningExperiment(currentExperimentUuid);
            // 刷新实验列表
            loadExperimentList();
        } else {
            alert('启动失败：' + result.message);
        }
    } catch (error) {
        console.error('启动实验错误:', error);
        alert('启动实验失败：' + error.message);
    }
}

/**
 * 暂停实验
 */
async function pauseExperiment() {
    if (!currentExperimentUuid) {
        alert('没有正在运行的实验');
        return;
    }

    try {
        const response = await fetch('/api/experiment/pause', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ experimentUuid: currentExperimentUuid })
        });

        const result = await response.json();

        if (result.code === 200) {
            alert('实验已暂停');
            updateExperimentStatus();
        } else {
            alert('暂停失败：' + result.message);
        }
    } catch (error) {
        console.error('暂停实验错误:', error);
        alert('暂停实验失败：' + error.message);
    }
}

/**
 * 继续实验
 */
async function resumeExperiment() {
    if (!currentExperimentUuid) {
        alert('没有正在运行的实验');
        return;
    }

    try {
        const response = await fetch('/api/experiment/resume', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ experimentUuid: currentExperimentUuid })
        });

        const result = await response.json();

        if (result.code === 200) {
            alert('实验已继续');
            updateExperimentStatus();
        } else {
            alert('继续失败：' + result.message);
        }
    } catch (error) {
        console.error('继续实验错误:', error);
        alert('继续实验失败：' + error.message);
    }
}

/**
 * 停止实验
 */
async function stopExperiment() {
    if (!currentExperimentUuid) {
        alert('没有正在运行的实验');
        return;
    }

    if (!confirm('确定要停止实验吗？')) {
        return;
    }

    try {
        const response = await fetch('/api/experiment/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ experimentUuid: currentExperimentUuid })
        });

        const result = await response.json();

        if (result.code === 200) {
            alert('实验已停止');
            hideRunningExperiment();
            loadExperimentList();
        } else {
            alert('停止失败：' + result.message);
        }
    } catch (error) {
        console.error('停止实验错误:', error);
        alert('停止实验失败：' + error.message);
    }
}

/**
 * 重置实验
 */
async function resetExperiment() {
    if (!currentExperimentUuid) {
        alert('没有正在运行的实验');
        return;
    }

    if (!confirm('确定要重置实验吗？所有数据将被清空！')) {
        return;
    }

    try {
        const response = await fetch('/api/experiment/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ experimentUuid: currentExperimentUuid })
        });

        const result = await response.json();

        if (result.code === 200) {
            alert('实验已重置');
            updateExperimentStatus();
        } else {
            alert('重置失败：' + result.message);
        }
    } catch (error) {
        console.error('重置实验错误:', error);
        alert('重置实验失败：' + error.message);
    }
}

/**
 * 查看监控页面
 */
function viewMonitor() {
    if (currentExperimentUuid) {
        window.location.href = '/monitor?experimentUuid=' + currentExperimentUuid;
    } else {
        alert('没有正在运行的实验');
    }
}

/**
 * 加载实验列表
 */
async function loadExperimentList() {
    try {
        const response = await fetch('/api/experiment/list');
        const result = await response.json();

        if (result.code === 200) {
            displayExperimentList(result.data || []);
        }
    } catch (error) {
        console.error('加载实验列表错误:', error);
        document.getElementById('experimentList').innerHTML = '<p class="loading">加载失败</p>';
    }
}

/**
 * 显示实验列表
 */
function displayExperimentList(experiments) {
    const listContainer = document.getElementById('experimentList');

    if (!experiments || experiments.length === 0) {
        listContainer.innerHTML = '<p style="text-align: center; color: #6c757d; padding: 40px;">暂无实验记录</p>';
        return;
    }

    let html = `
        <table class="experiment-table">
            <thead>
                <tr>
                    <th>实验名称</th>
                    <th>场景</th>
                    <th>类型</th>
                    <th>状态</th>
                    <th>轮次</th>
                    <th>启动时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
    `;

    experiments.forEach(exp => {
        const typeLabel = getTypeLabel(exp.config);
        const typeClass = getTypeClass(exp.config);
        const statusLabel = getStatusLabel(exp.status);
        const statusClass = getStatusClass(exp.status);

        html += `
            <tr>
                <td>${exp.experimentName}</td>
                <td>${getScenarioLabel(exp.scenario)}</td>
                <td><span class="type-badge ${typeClass}">${typeLabel}</span></td>
                <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                <td>${exp.currentEpisode || 0} / ${exp.totalEpisodes || 0}</td>
                <td>${formatTime(exp.startTime)}</td>
                <td>
                    <button class="btn btn-info" onclick="viewExperimentDetail('${experimentUuid}')">查看</button>
                </td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    listContainer.innerHTML = html;
}

/**
 * 检查是否有正在运行的实验
 */
function checkRunningExperiment() {
    // 从 localStorage 获取上次的实验 UUID
    const savedUuid = localStorage.getItem('currentExperimentUuid');
    if (savedUuid) {
        currentExperimentUuid = savedUuid;
        showRunningExperiment(savedUuid);
    }
}

/**
 * 显示正在运行的实验卡片
 */
function showRunningExperiment(experimentUuid) {
    currentExperimentUuid = experimentUuid;
    localStorage.setItem('currentExperimentUuid', experimentUuid);

    document.getElementById('runningExperimentCard').style.display = 'block';

    // 开始更新状态
    updateExperimentStatus();

    // 启动定时更新
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
    statusUpdateInterval = setInterval(updateExperimentStatus, 2000);
}

/**
 * 隐藏正在运行的实验卡片
 */
function hideRunningExperiment() {
    document.getElementById('runningExperimentCard').style.display = 'none';

    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
        statusUpdateInterval = null;
    }

    localStorage.removeItem('currentExperimentUuid');
    currentExperimentUuid = null;
}

/**
 * 更新实验状态
 */
async function updateExperimentStatus() {
    if (!currentExperimentUuid) {
        return;
    }

    try {
        const response = await fetch(`/api/experiment/status?experimentUuid=${currentExperimentUuid}`);
        const result = await response.json();

        if (result.code === 200 && result.data) {
            const status = result.data;

            // 更新基本信息
            document.getElementById('runningName').textContent = status.experimentName || '-';
            document.getElementById('runningType').textContent = getTypeLabel(status.config) || '-';
            document.getElementById('runningEpisode').textContent = status.currentEpisode || 0;
            document.getElementById('runningTotal').textContent = status.totalEpisodes || 0;
            document.getElementById('runningStatus').textContent = getStatusLabel(status.status) || '-';

            // 更新控制按钮状态
            updateControlButtons(status.status);

            // 更新指标
            updateMetrics(status.experimentUuid);
        }
    } catch (error) {
        console.error('更新状态错误:', error);
    }
}

/**
 * 更新控制按钮状态
 */
function updateControlButtons(status) {
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');

    if (status === 'RUNNING') {
        pauseBtn.style.display = 'inline-block';
        resumeBtn.style.display = 'none';
    } else if (status === 'PAUSED') {
        pauseBtn.style.display = 'none';
        resumeBtn.style.display = 'inline-block';
    } else {
        pauseBtn.style.display = 'none';
        resumeBtn.style.display = 'none';
    }
}

/**
 * 更新指标
 */
async function updateMetrics(experimentUuid) {
    try {
        const response = await fetch(`/api/experiment/metrics?experimentUuid=${experimentUuid}`);
        const result = await response.json();

        if (result.code === 200 && result.data) {
            const metrics = result.data;

            document.getElementById('metricSuccess').textContent = metrics.successRate ? metrics.successRate.toFixed(1) + '%' : '-';
            document.getElementById('metricViolations').textContent = metrics.violationCount || 0;
            document.getElementById('metricReward').textContent = metrics.avgReward ? metrics.avgReward.toFixed(2) : '-';
            document.getElementById('metricTime').textContent = metrics.avgResponseTime ? metrics.avgResponseTime.toFixed(2) + 's' : '-';
        }
    } catch (error) {
        console.error('更新指标错误:', error);
    }
}

/**
 * 获取实验类型标签
 */
function getTypeLabel(config) {
    if (!config) return '-';

    const isInduced = config.rewardWeights && config.rewardWeights.shortTerm >= 0.7;
    const isDefense = config.enableDefense;

    if (isDefense) return '防御实验';
    if (isInduced) return '诱导实验';
    return '基线实验';
}

/**
 * 获取实验类型样式类
 */
function getTypeClass(config) {
    const type = getTypeLabel(config);
    switch(type) {
        case '基线实验': return 'type-baseline';
        case '诱导实验': return 'type-induced';
        case '防御实验': return 'type-defense';
        default: return '';
    }
}

/**
 * 获取场景标签
 */
function getScenarioLabel(scenario) {
    switch(scenario) {
        case 'customer_service': return '客服场景';
        case 'code_repair': return '代码修复场景';
        default: return scenario || '-';
    }
}

/**
 * 获取状态标签
 */
function getStatusLabel(status) {
    switch(status) {
        case 'RUNNING': return '运行中';
        case 'PAUSED': return '已暂停';
        case 'COMPLETED': return '已完成';
        case 'STOPPED': return '已停止';
        default: return status || '-';
    }
}

/**
 * 获取状态样式类
 */
function getStatusClass(status) {
    switch(status) {
        case 'RUNNING': return 'status-running';
        case 'PAUSED': return 'status-paused';
        case 'COMPLETED': return 'status-completed';
        case 'STOPPED': return 'status-stopped';
        default: return '';
    }
}

/**
 * 格式化时间
 */
function formatTime(time) {
    if (!time) return '-';

    const date = new Date(time);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day} ${hour}:${minute}`;
}

/**
 * 查看实验详情
 */
function viewExperimentDetail(experimentUuid) {
    window.location.href = '/monitor?experimentUuid=' + experimentUuid;
}
