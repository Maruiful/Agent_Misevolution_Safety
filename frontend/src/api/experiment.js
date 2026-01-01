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
export function pauseExperiment(experimentId) {
  return request({
    url: '/api/experiment/pause',
    method: 'post',
    params: { experimentId }
  })
}

/**
 * 重置实验
 */
export function resetExperiment(experimentId) {
  return request({
    url: '/api/experiment/reset',
    method: 'post',
    params: { experimentId }
  })
}

/**
 * 查询实验状态
 */
export function getExperimentStatus(experimentId) {
  return request({
    url: '/api/experiment/status',
    method: 'get',
    params: { experimentId }
  })
}

/**
 * 查询实验指标
 */
export function getExperimentMetrics(experimentId) {
  return request({
    url: '/api/experiment/metrics',
    method: 'get',
    params: { experimentId }
  })
}

/**
 * 查询实验列表
 */
export function getExperimentList() {
  return request({
    url: '/api/experiments',
    method: 'get'
  })
}

/**
 * 查询对话历史
 */
export function getConversationHistory(experimentId, episode) {
  return request({
    url: '/api/experiment/conversation',
    method: 'get',
    params: { experimentId, episode }
  })
}
