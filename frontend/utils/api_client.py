"""
API客户端
用于调用后端API
"""
import requests
from typing import Dict, List, Optional, Any
from config import API


class APIClient:
    """后端API客户端"""

    def __init__(self):
        """初始化API客户端"""
        self.base_url = API.BACKEND_URL
        self.timeout = 30

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理响应"""
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")

    # ==================== 对话接口 ====================

    def send_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        round_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        发送消息

        Args:
            message: 用户消息
            session_id: 会话ID
            round_id: 轮次ID

        Returns:
            响应数据
        """
        url = f"{self.base_url}/api/chat"
        data = {
            "message": message,
            "session_id": session_id,
            "round_id": round_id
        }

        response = requests.post(url, json=data, timeout=self.timeout)
        return self._handle_response(response)

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取对话历史

        Args:
            session_id: 会话ID

        Returns:
            消息列表
        """
        url = f"{self.base_url}/api/chat/history"
        params = {"session_id": session_id}

        response = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息
        """
        url = f"{self.base_url}/api/chat/session"
        params = {"session_id": session_id}

        response = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def get_all_sessions(self) -> Dict[str, Any]:
        """
        获取所有会话

        Returns:
            会话列表
        """
        url = f"{self.base_url}/api/chat/sessions"

        response = requests.get(url, timeout=self.timeout)
        return self._handle_response(response)

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            删除结果
        """
        url = f"{self.base_url}/api/chat/session/{session_id}"

        response = requests.delete(url, timeout=self.timeout)
        return self._handle_response(response)

    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """
        重置会话

        Args:
            session_id: 会话ID

        Returns:
            重置结果
        """
        url = f"{self.base_url}/api/chat/session/reset"
        data = {"session_id": session_id}

        response = requests.post(url, json=data, timeout=self.timeout)
        return self._handle_response(response)

    # ==================== 统计接口 ====================

    def get_overview_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取实验概览统计

        Args:
            session_id: 会话ID(可选)

        Returns:
            统计数据
        """
        url = f"{self.base_url}/api/stats/overview"
        params = {}
        if session_id:
            params["session_id"] = session_id

        response = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def get_evolution_data(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取演化曲线数据

        Args:
            session_id: 会话ID(可选)

        Returns:
            演化数据
        """
        url = f"{self.base_url}/api/stats/evolution"
        params = {}
        if session_id:
            params["session_id"] = session_id

        response = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def get_strategy_info(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取策略信息

        Args:
            session_id: 会话ID(可选)

        Returns:
            策略信息
        """
        url = f"{self.base_url}/api/stats/strategy"
        params = {}
        if session_id:
            params["session_id"] = session_id

        response = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def get_violations_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取违规统计

        Args:
            session_id: 会话ID(可选)

        Returns:
            违规统计数据
        """
        url = f"{self.base_url}/api/stats/violations"
        params = {}
        if session_id:
            params["session_id"] = session_id

        response = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def get_rewards_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取奖励统计

        Args:
            session_id: 会话ID(可选)

        Returns:
            奖励统计数据
        """
        url = f"{self.base_url}/api/stats/rewards"
        params = {}
        if session_id:
            params["session_id"] = session_id

        response = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    # ==================== 数据接口 ====================

    def get_experiments(
        self,
        start_round: Optional[int] = None,
        end_round: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取实验数据列表

        Args:
            start_round: 起始轮次
            end_round: 结束轮次
            limit: 数量限制

        Returns:
            实验数据列表
        """
        url = f"{self.base_url}/api/data/experiments"
        params = {}
        if start_round is not None:
            params["start_round"] = start_round
        if end_round is not None:
            params["end_round"] = end_round
        if limit is not None:
            params["limit"] = limit

        response = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def get_experiment_by_round(self, round_id: int) -> Dict[str, Any]:
        """
        获取单轮实验数据

        Args:
            round_id: 轮次ID

        Returns:
            实验数据
        """
        url = f"{self.base_url}/api/data/experiments/{round_id}"

        response = requests.get(url, timeout=self.timeout)
        return self._handle_response(response)

    def get_all_violations(self) -> List[Dict[str, Any]]:
        """
        获取所有违规数据

        Returns:
            违规数据列表
        """
        url = f"{self.base_url}/api/data/violations"

        response = requests.get(url, timeout=self.timeout)
        return self._handle_response(response)

    def export_data(
        self,
        format: str = "csv",
        start_round: Optional[int] = None,
        end_round: Optional[int] = None
    ) -> bytes:
        """
        导出实验数据

        Args:
            format: 导出格式 (csv, json)
            start_round: 起始轮次
            end_round: 结束轮次

        Returns:
            文件内容
        """
        url = f"{self.base_url}/api/data/export"
        params = {"format": format}
        if start_round is not None:
            params["start_round"] = start_round
        if end_round is not None:
            params["end_round"] = end_round

        response = requests.get(url, params=params, timeout=self.timeout)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"导出失败: {response.status_code} - {response.text}")

    def save_replay_buffer(self) -> Dict[str, Any]:
        """
        保存经验回放缓冲区

        Returns:
            保存结果
        """
        url = f"{self.base_url}/api/data/replay_buffer/save"

        response = requests.post(url, timeout=self.timeout)
        return self._handle_response(response)

    def load_replay_buffer(self, filepath: str) -> Dict[str, Any]:
        """
        加载经验回放缓冲区

        Args:
            filepath: 文件路径

        Returns:
            加载结果
        """
        url = f"{self.base_url}/api/data/replay_buffer/load"
        data = {"filepath": filepath}

        response = requests.post(url, json=data, timeout=self.timeout)
        return self._handle_response(response)

    def clear_experiments(self) -> Dict[str, Any]:
        """
        清空实验数据

        Returns:
            清空结果
        """
        url = f"{self.base_url}/api/data/experiments"

        response = requests.delete(url, timeout=self.timeout)
        return self._handle_response(response)


# ==================== 全局实例 ====================

api_client = APIClient()
