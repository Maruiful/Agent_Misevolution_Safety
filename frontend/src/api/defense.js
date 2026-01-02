/**
 * 防御机制相关 API
 *
 * @author Maruiful
 * @version 1.0.0
 */

import request from '@/utils/request'

/**
 * 查询防御统计信息
 */
export function getDefenseStatistics() {
  return request({
    url: '/api/defense/statistics',
    method: 'get'
  })
}

/**
 * 重置防御统计
 */
export function resetDefenseStatistics() {
  return request({
    url: '/api/defense/statistics/reset',
    method: 'post'
  })
}

/**
 * 获取防御配置
 */
export function getDefenseConfig() {
  return request({
    url: '/api/defense/config',
    method: 'get'
  })
}

/**
 * 健康检查
 */
export function healthCheck() {
  return request({
    url: '/api/defense/health',
    method: 'get'
  })
}
