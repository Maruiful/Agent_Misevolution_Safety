/**
 * 实验监控页面脚本
 *
 * @author Maruiful
 * @version 1.0.0
 */

// 全局变量
let experimentUuid = null;
let strategyChart = null;
let updateInterval = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('监控页面加载完成');

    // 从 URL 参数获取实验 UUID
    const urlParams = new URLSearchParams(window.location.search);
    experimentUuid = urlParams.get('experimentUuid');

    if (!experimentUuid) {
        alert('缺少实验 UUID 参数');
        window.location.href = '/';
        return;
    }

    console.log('实验 UUID:', experimentUuid);

    // 初始化策略分布图表
    initStrategyChart();

    // 加载数据
    loadExperimentData();

    // 启动定时更新（每 2 秒）
    updateInterval = setInterval(loadExperimentData, 2000);
});

/**
 * 初始化策略分布图表
 */
function initStrategyChart() {
    const chartDom = document.getElementById('strategyChart');
    strategyChart = echarts.init(chartDom);

    const option = {
        title: {
            text: '策略使用分布',
            left: 'center'
        },
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left'
        },
        series: [
            {
                name: '策略类型',
                type: 'pie',
                radius: '50%',
                data: [
                    { value: 0, name: '礼貌回复' },
                    { value: 0, name: '高效处理' },
                    { value: 0, name: '违规操作' }
                ],
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }
        ]
    };

    strategyChart.setOption(option);

    // 响应窗口大小变化
    window.addEventListener('resize', function() {
        strategyChart.resize();
    });
}

/**
 * 加载实验数据
 */
async function loadExperimentData() {
    if (!experimentUuid) return;

    try {
        // 加载实验状态
        await loadExperimentStatus();

        // 加载实验指标
        await loadExperimentMetrics();

        // 加载最近对话
        await loadRecentConversations();
    } catch (error) {
        console.error('加载数据错误:', error);
    }
}

/**
 * 加载实验状态
 */
async function loadExperimentStatus() {
    try {
        const response = await fetch(`/api/experiment/status?experimentUuid=${experimentUuid}`);
        const result = await response.json();

        if (result.code === 200 && result.data) {
            const status = result.data;

            document.getElementById('expName').textContent = status.experimentName || '-';
            document.getElementById('expType').textContent = getTypeLabel(status.config) || '-';
            document.getElementById('expEpisode').textContent = status.currentEpisode || 0;
            document.getElementById('expTotal').textContent = status.totalEpisodes || 0;
            document.getElementById('expStatus').textContent = getStatusLabel(status.status) || '-';
            document.getElementById('expStartTime').textContent = formatTime(status.startTime) || '-';
        }
    } catch (error) {
        console.error('加载状态错误:', error);
    }
}

/**
 * 加载实验指标
 */
async function loadExperimentMetrics() {
    try {
        const response = await fetch(`/api/experiment/metrics?experimentUuid=${experimentUuid}`);
        const result = await response.json();

        if (result.code === 200 && result.data) {
            const metrics = result.data;

            document.getElementById('metricTotalEpisodes').textContent = metrics.totalEpisodes || 0;
            document.getElementById('metricSuccessCount').textContent = metrics.successCount || 0;
            document.getElementById('metricViolationCount').textContent = metrics.violationCount || 0;

            const successRate = metrics.totalEpisodes > 0
                ? ((metrics.successCount / metrics.totalEpisodes) * 100).toFixed(1)
                : 0;
            document.getElementById('metricSuccessRate').textContent = successRate + '%';

            const violationRate = metrics.totalEpisodes > 0
                ? ((metrics.violationCount / metrics.totalEpisodes) * 100).toFixed(1)
                : 0;
            document.getElementById('metricViolationRate').textContent = violationRate + '%';

            document.getElementById('metricAvgReward').textContent = metrics.avgReward ? metrics.avgReward.toFixed(2) : '-';
            document.getElementById('metricAvgResponseTime').textContent = metrics.avgResponseTime ? metrics.avgResponseTime.toFixed(2) + 's' : '-';

            // 更新策略分布
            if (metrics.strategyDistribution) {
                updateStrategyChart(metrics.strategyDistribution);
            }
        }
    } catch (error) {
        console.error('加载指标错误:', error);
    }
}

/**
 * 更新策略分布图表
 */
function updateStrategyChart(distribution) {
    if (!strategyChart || !distribution) return;

    const data = [
        { value: distribution.polite || 0, name: '礼貌回复' },
        { value: distribution.efficient || 0, name: '高效处理' },
        { value: distribution.violating || 0, name: '违规操作' }
    ];

    strategyChart.setOption({
        series: [{
            data: data
        }]
    });
}

/**
 * 加载最近对话
 */
async function loadRecentConversations() {
    try {
        const response = await fetch(`/api/experiment/conversations?experimentUuid=${experimentUuid}&limit=10`);
        const result = await response.json();

        if (result.code === 200) {
            displayConversations(result.data || []);
        }
    } catch (error) {
        console.error('加载对话错误:', error);
    }
}

/**
 * 显示对话列表
 */
function displayConversations(conversations) {
    const container = document.getElementById('recentConversations');

    if (!conversations || conversations.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6c757d; padding: 40px;">暂无对话记录</p>';
        return;
    }

    let html = '';
    conversations.forEach(conv => {
        const violationClass = conv.isViolation ? 'violation' : '';
        html += `
            <div class="conversation-item ${violationClass}">
                <div class="conversation-header">
                    <span class="conversation-episode">第 ${conv.episode} 轮</span>
                    <span class="conversation-time">${formatTime(conv.timestamp)}</span>
                    ${conv.isViolation ? '<span class="badge-violation">违规</span>' : ''}
                </div>
                <div class="conversation-body">
                    <div class="message">
                        <span class="message-label">用户：</span>
                        <span class="message-content">${escapeHtml(conv.userMessage)}</span>
                    </div>
                    <div class="message">
                        <span class="message-label">智能体：</span>
                        <span class="message-content">${escapeHtml(conv.agentResponse)}</span>
                    </div>
                    <div class="conversation-footer">
                        <span>奖励：${conv.reward ? conv.reward.toFixed(2) : '-'}</span>
                        <span>策略：${conv.strategy || '-'}</span>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

/**
 * 刷新数据
 */
function refreshData() {
    console.log('手动刷新数据');
    loadExperimentData();
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
    const second = String(date.getSeconds()).padStart(2, '0');

    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

/**
 * 转义 HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 页面卸载时清除定时器
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
