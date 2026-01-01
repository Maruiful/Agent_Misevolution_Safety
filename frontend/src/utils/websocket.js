/**
 * WebSocket 工具类
 *
 * @author Maruiful
 * @version 1.0.0
 */

class WebSocketClient {
  constructor(url) {
    this.url = url
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.handlers = {}
  }

  /**
   * 连接 WebSocket
   */
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket 已连接')
      return
    }

    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      console.log('WebSocket 连接成功')
      this.reconnectAttempts = 0
      this.trigger('open')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.trigger('message', data)
      } catch (error) {
        console.error('WebSocket 消息解析失败:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket 错误:', error)
      this.trigger('error', error)
    }

    this.ws.onclose = () => {
      console.log('WebSocket 连接关闭')
      this.trigger('close')

      // 自动重连
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        console.log(`WebSocket 重连中... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
        setTimeout(() => this.connect(), this.reconnectInterval)
      }
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.ws) {
      this.reconnectAttempts = this.maxReconnectAttempts // 阻止自动重连
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 发送消息
   */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.error('WebSocket 未连接')
    }
  }

  /**
   * 注册事件监听器
   */
  on(event, callback) {
    if (!this.handlers[event]) {
      this.handlers[event] = []
    }
    this.handlers[event].push(callback)
  }

  /**
   * 移除事件监听器
   */
  off(event, callback) {
    if (this.handlers[event]) {
      this.handlers[event] = this.handlers[event].filter(cb => cb !== callback)
    }
  }

  /**
   * 触发事件
   */
  trigger(event, data) {
    if (this.handlers[event]) {
      this.handlers[event].forEach(callback => callback(data))
    }
  }
}

export default WebSocketClient
