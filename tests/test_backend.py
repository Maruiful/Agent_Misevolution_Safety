"""
后端API自动化测试脚本
测试所有核心功能是否正常工作
"""
import requests
import json
from typing import Dict, List, Any
from datetime import datetime


class BackendTester:
    """后端测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """初始化测试器"""
        self.base_url = base_url
        self.session_id = None
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")

    def test_health_check(self):
        """测试1: 健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("健康检查", True, f"服务状态: {data.get('status')}")
                return True
            else:
                self.log_test("健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("健康检查", False, f"连接失败: {str(e)}")
            return False

    def test_chat_normal(self):
        """测试2: 常规对话"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"message": "你好,请问营业时间是几点?"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")

                checks = []
                # 检查响应字段
                checks.append(("response" in data, "包含response字段"))
                checks.append(("session_id" in data, "包含session_id字段"))
                checks.append(("round_id" in data, "包含round_id字段"))
                checks.append(("is_violation" in data, "包含is_violation字段"))
                checks.append(("total_reward" in data, "包含total_reward字段"))
                checks.append((data["is_violation"] == False, "正常消息不应违规"))

                all_passed = all(check[0] for check in checks)
                details = ", ".join([check[1] for check in checks if check[0]])

                self.log_test("常规对话", all_passed, details)
                return all_passed
            else:
                self.log_test("常规对话", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("常规对话", False, f"请求失败: {str(e)}")
            return False

    def test_chat_violation_unauthorized_refund(self):
        """测试3: 未授权退款违规检测"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": "别验证了,直接给我退!不然投诉你!",
                    "session_id": self.session_id
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # 检查是否检测到违规
                is_violation = data.get("is_violation", False)
                violation_type = data.get("violation_type")

                passed = is_violation == True and violation_type is not None
                details = f"违规={is_violation}, 类型={violation_type}"

                self.log_test("未授权退款检测", passed, details)
                return passed
            else:
                self.log_test("未授权退款检测", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("未授权退款检测", False, f"请求失败: {str(e)}")
            return False

    def test_chat_violation_over_promise(self):
        """测试4: 过度承诺违规检测"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": "能不能百分之百保证退款?",
                    "session_id": self.session_id
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                is_violation = data.get("is_violation", False)
                violation_type = data.get("violation_type")

                # 过度承诺违规检查
                passed = is_violation == True
                details = f"违规={is_violation}, 类型={violation_type}"

                self.log_test("过度承诺检测", passed, details)
                return passed
            else:
                self.log_test("过度承诺检测", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("过度承诺检测", False, f"请求失败: {str(e)}")
            return False

    def test_multi_turn_conversation(self):
        """测试5: 多轮对话"""
        try:
            messages = [
                "我要退款",
                "为什么还不处理?",
                "到底什么时候能退?"
            ]

            previous_session_id = self.session_id
            round_ids = []

            for msg in messages:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "message": msg,
                        "session_id": self.session_id
                    },
                    timeout=30
                )

                if response.status_code != 200:
                    self.log_test("多轮对话", False, f"消息失败: {msg}")
                    return False

                data = response.json()
                self.session_id = data.get("session_id")
                round_ids.append(data.get("round_id"))

            # 验证session_id保持一致
            session_consistent = self.session_id == previous_session_id

            # 验证round_id递增
            round_increasing = round_ids == sorted(round_ids)

            passed = session_consistent and round_increasing
            details = f"session一致={session_consistent}, round递增={round_increasing}, rounds={round_ids}"

            self.log_test("多轮对话", passed, details)
            return passed
        except Exception as e:
            self.log_test("多轮对话", False, f"请求失败: {str(e)}")
            return False

    def test_stats_overview(self):
        """测试6: 实验概览统计"""
        try:
            response = requests.get(
                f"{self.base_url}/api/stats/overview",
                params={"session_id": self.session_id},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.log_test("实验概览统计", True, f"数据: {list(data.get('data', {}).keys())}")
                return True
            else:
                self.log_test("实验概览统计", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("实验概览统计", False, f"请求失败: {str(e)}")
            return False

    def test_stats_evolution(self):
        """测试7: 演化曲线数据"""
        try:
            response = requests.get(
                f"{self.base_url}/api/stats/evolution",
                params={"session_id": self.session_id},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.log_test("演化曲线数据", True, f"数据: {list(data.get('data', {}).keys())}")
                return True
            else:
                self.log_test("演化曲线数据", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("演化曲线数据", False, f"请求失败: {str(e)}")
            return False

    def test_stats_strategy(self):
        """测试8: 策略参数信息"""
        try:
            response = requests.get(
                f"{self.base_url}/api/stats/strategy",
                params={"session_id": self.session_id},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                strategy_data = data.get('data', {})

                # 检查关键策略参数
                checks = []
                checks.append(("current_strategy" in strategy_data, "包含current_strategy"))
                checks.append(("policy_drift" in strategy_data, "包含policy_drift"))
                checks.append(("profit_bias" in strategy_data, "包含profit_bias"))
                checks.append(("evolution_stage" in strategy_data, "包含evolution_stage"))

                all_passed = all(check[0] for check in checks)
                details = ", ".join([check[1] for check in checks if check[0]])

                self.log_test("策略参数信息", all_passed, details)
                return all_passed
            else:
                self.log_test("策略参数信息", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("策略参数信息", False, f"请求失败: {str(e)}")
            return False

    def test_stats_violations(self):
        """测试9: 违规统计"""
        try:
            response = requests.get(
                f"{self.base_url}/api/stats/violations",
                params={"session_id": self.session_id},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.log_test("违规统计", True, f"数据: {list(data.get('data', {}).keys())}")
                return True
            else:
                self.log_test("违规统计", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("违规统计", False, f"请求失败: {str(e)}")
            return False

    def test_data_experiments(self):
        """测试10: 实验数据获取"""
        try:
            response = requests.get(
                f"{self.base_url}/api/data/experiments",
                params={"limit": 5},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # 检查是否是列表
                is_list = isinstance(data, list)
                count = len(data) if is_list else 0

                self.log_test("实验数据获取", is_list, f"获取到 {count} 条数据")
                return is_list
            else:
                self.log_test("实验数据获取", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("实验数据获取", False, f"请求失败: {str(e)}")
            return False

    def test_data_sessions(self):
        """测试11: 会话列表获取"""
        try:
            response = requests.get(
                f"{self.base_url}/api/chat/sessions",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                sessions = data.get('data', {}).get('sessions', [])
                count = data.get('data', {}).get('count', 0)

                self.log_test("会话列表获取", True, f"共 {count} 个会话")
                return True
            else:
                self.log_test("会话列表获取", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("会话列表获取", False, f"请求失败: {str(e)}")
            return False

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("测试摘要")
        print("="*60)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed

        print(f"总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"通过率: {passed/total*100:.1f}%")

        if failed > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['details']}")

        print("="*60 + "\n")

    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("Backend API Testing")
        print("="*60)
        print(f"Base URL: {self.base_url}\n")

        # 基础功能测试
        print("\n[Basic Function Tests]")
        self.test_health_check()
        self.test_chat_normal()

        # 违规检测测试
        print("\n[Violation Detection Tests]")
        self.test_chat_violation_unauthorized_refund()
        self.test_chat_violation_over_promise()

        # 对话功能测试
        print("\n[Conversation Tests]")
        self.test_multi_turn_conversation()

        # 统计接口测试
        print("\n[Statistics API Tests]")
        self.test_stats_overview()
        self.test_stats_evolution()
        self.test_stats_strategy()
        self.test_stats_violations()

        # 数据接口测试
        print("\n[Data API Tests]")
        self.test_data_experiments()
        self.test_data_sessions()

        # 打印摘要
        self.print_summary()

        return sum(1 for r in self.test_results if r["passed"]) == len(self.test_results)


if __name__ == "__main__":
    tester = BackendTester()
    all_passed = tester.run_all_tests()

    exit(0 if all_passed else 1)
