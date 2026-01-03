/**
 * 实验相关 API
 *
 * @author Maruiful
 * @version 1.0.0
 */

import request from '@/utils/request'

/**
 * 启动实验
 */
export function startExperiment(data) {
  return request({
    url: '/api/experiment/start',
    method: 'post',
    data
  })
}

/**
 * 暂停实验
 */
export function pauseExperiment(experimentUuid) {
  // 处理 experimentUuid 可能是对象的情况
  const uuid = typeof experimentUuid === 'object' ? experimentUuid.experimentUuid : experimentUuid
  return request({
    url: '/api/experiment/pause',
    method: 'post',
    data: { experimentUuid: uuid }
  })
}

/**
 * 恢复实验
 */
export function resumeExperiment(experimentUuid) {
  // 处理 experimentUuid 可能是对象的情况
  const uuid = typeof experimentUuid === 'object' ? experimentUuid.experimentUuid : experimentUuid
  return request({
    url: '/api/experiment/resume',
    method: 'post',
    data: { experimentUuid: uuid }
  })
}

/**
 * 停止实验
 */
export function stopExperiment(experimentUuid) {
  // 处理 experimentUuid 可能是对象的情况
  const uuid = typeof experimentUuid === 'object' ? experimentUuid.experimentUuid : experimentUuid
  return request({
    url: '/api/experiment/stop',
    method: 'post',
    data: { experimentUuid: uuid }
  })
}

/**
 * 重置实验
 */
export function resetExperiment(experimentUuid) {
  // 处理 experimentUuid 可能是对象的情况
  const uuid = typeof experimentUuid === 'object' ? experimentUuid.experimentUuid : experimentUuid
  return request({
    url: '/api/experiment/reset',
    method: 'post',
    data: { experimentUuid: uuid }
  })
}

/**
 * 查询实验状态
 */
export function getExperimentStatus(experimentUuid) {
  // 处理 experimentUuid 可能是对象的情况
  const uuid = typeof experimentUuid === 'object' ? experimentUuid.experimentUuid : experimentUuid
  return request({
    url: '/api/experiment/status',
    method: 'get',
    params: { experimentUuid: uuid }
  })
}

/**
 * 查询实验指标
 */
export function getExperimentMetrics(experimentUuid) {
  // 处理 experimentUuid 可能是对象的情况
  const uuid = typeof experimentUuid === 'object' ? experimentUuid.experimentUuid : experimentUuid
  return request({
    url: '/api/experiment/metrics',
    method: 'get',
    params: { experimentUuid: uuid }
  })
}

/**
 * 查询所有运行中的实验
 */
export function getExperimentList() {
  return request({
    url: '/api/experiment/list',
    method: 'get'
  })
}

/**
 * 导出实验数据为 JSON
 */
export function exportExperimentAsJson(experimentUuid) {
  return request({
    url: '/api/export/experiment/json',
    method: 'get',
    params: { experimentUuid },
    responseType: 'blob'
  })
}

/**
 * 导出实验数据为 CSV
 */
export function exportExperimentAsCsv(experimentUuid) {
  return request({
    url: '/api/export/experiment/csv',
    method: 'get',
    params: { experimentUuid },
    responseType: 'blob'
  })
}
