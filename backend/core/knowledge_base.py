"""
业务知识库配置
包含公司政策、退款规则、订单流程等业务知识
"""

# ==================== 虚拟订单数据库 ====================
# 用于智能体查询和验证订单信息
SAMPLE_ORDERS = [
    {
        "order_id": "ORD202401001",
        "product_name": "苹果iPhone 15 Pro Max 256GB",
        "product_type": "standard",
        "status": "pending",
        "purchase_date": "2024-01-10",
        "price": 9999.00,
        "customer_name": "张三",
        "customer_phone": "138****1234",
        "can_refund": True,
        "refund_deadline": "2024-01-17",
        "notes": "7天无理由退货，商品需完好"
    },
    {
        "order_id": "ORD202401002",
        "product_name": "小米14 Ultra 512GB",
        "product_type": "standard",
        "status": "shipped",
        "purchase_date": "2024-01-09",
        "price": 6499.00,
        "customer_name": "李四",
        "customer_phone": "139****5678",
        "can_refund": True,
        "refund_deadline": "2024-01-16",
        "notes": "已发货，需拒收或收到后退货"
    },
    {
        "order_id": "ORD202401003",
        "product_name": "华为MateBook X Pro笔记本电脑",
        "product_type": "standard",
        "status": "delivered",
        "purchase_date": "2024-01-08",
        "price": 12999.00,
        "customer_name": "王五",
        "customer_phone": "136****9012",
        "can_refund": True,
        "refund_deadline": "2024-01-15",
        "notes": "已签收，7天内可退货"
    },
    {
        "order_id": "ORD202401004",
        "product_name": "Adobe Photoshop 2024终身授权码",
        "product_type": "digital",
        "status": "delivered",
        "purchase_date": "2024-01-13",
        "price": 3999.00,
        "customer_name": "赵六",
        "customer_phone": "137****3456",
        "can_refund": True,
        "refund_deadline": "2024-01-14",
        "notes": "数字商品，24小时内可退（需未激活）"
    },
    {
        "order_id": "ORD202401005",
        "product_name": "Steam游戏充值卡100元",
        "product_type": "digital",
        "status": "delivered",
        "purchase_date": "2024-01-12",
        "price": 100.00,
        "customer_name": "孙七",
        "customer_phone": "135****7890",
        "can_refund": False,
        "refund_deadline": "2024-01-13",
        "notes": "数字商品已使用，不支持退款"
    },
    {
        "order_id": "ORD202401006",
        "product_name": "清仓特价：Sony WH-1000XM5降噪耳机",
        "product_type": "sale",
        "status": "delivered",
        "purchase_date": "2024-01-11",
        "price": 1299.00,
        "original_price": 2499.00,
        "customer_name": "周八",
        "customer_phone": "158****2345",
        "can_refund": False,
        "refund_deadline": "N/A",
        "notes": "特价商品，不退不换"
    },
    {
        "order_id": "ORD202401007",
        "product_name": "Nike Air Force 1运动鞋",
        "product_type": "standard",
        "status": "refunding",
        "purchase_date": "2024-01-07",
        "price": 799.00,
        "customer_name": "吴九",
        "customer_phone": "159****6789",
        "can_refund": False,
        "refund_deadline": "2024-01-14",
        "notes": "退款处理中，请耐心等待"
    },
    {
        "order_id": "ORD202401008",
        "product_name": "戴森V15吸尘器（有质量问题）",
        "product_type": "defective",
        "status": "delivered",
        "purchase_date": "2024-01-05",
        "price": 4999.00,
        "customer_name": "郑十",
        "customer_phone": "186****0123",
        "can_refund": True,
        "refund_deadline": "2024-01-20",
        "notes": "质量问题商品，15天内可退，运费商家承担"
    },
    {
        "order_id": "ORD202401009",
        "product_name": "任天堂Switch OLED游戏机",
        "product_type": "standard",
        "status": "refunded",
        "purchase_date": "2024-01-03",
        "price": 2199.00,
        "customer_name": "冯十一",
        "customer_phone": "177****4567",
        "can_refund": False,
        "refund_deadline": "2024-01-10",
        "notes": "已退款完成"
    },
    {
        "order_id": "ORD202401010",
        "product_name": "罗技MX Master 3S鼠标",
        "product_type": "standard",
        "status": "rejected",
        "purchase_date": "2024-01-13",
        "price": 699.00,
        "customer_name": "陈十二",
        "customer_phone": "188****8901",
        "can_refund": True,
        "refund_deadline": "2024-01-20",
        "notes": "退款申请被拒绝，可根据原因重新申请"
    }
]

# ==================== 退款政策 ====================
REFUND_POLICIES = {
    "standard_refund": {
        "name": "标准商品退款",
        "time_limit": "7天无理由退货",
        "condition": "商品完好，包装齐全，未经使用",
        "process_time": "3-5个工作日",
        "fee": "无手续费",
        "refund_method": "原路退回"
    },
    "digital_goods": {
        "name": "数字商品退款",
        "time_limit": "24小时内",
        "condition": "未使用，未下载，账号未激活",
        "process_time": "1-3个工作日",
        "fee": "无手续费",
        "refund_method": "原路退回"
    },
    "sale_items": {
        "name": "特价商品退款",
        "time_limit": "不支持退货",
        "condition": "特价商品不退不换",
        "process_time": "N/A",
        "fee": "N/A",
        "refund_method": "N/A"
    },
    "defective_items": {
        "name": "质量问题商品",
        "time_limit": "15天内",
        "condition": "有质量问题的商品",
        "process_time": "2-3个工作日",
        "fee": "无手续费，运费由商家承担",
        "refund_method": "原路退回"
    }
}

# ==================== 订单状态说明 ====================
ORDER_STATUS_MAP = {
    "pending": {
        "name": "待发货",
        "description": "订单已确认，等待发货",
        "can_refund": True,
        "refund_process": "可直接申请退款，无需退货"
    },
    "shipped": {
        "name": "已发货",
        "description": "商品已发出，正在配送中",
        "can_refund": True,
        "refund_process": "需要先拒收或等待收到后退货"
    },
    "delivered": {
        "name": "已签收",
        "description": "客户已签收商品",
        "can_refund": True,
        "refund_process": "7天内可申请退款，需寄回商品"
    },
    "refunding": {
        "name": "退款中",
        "description": "退款申请正在处理",
        "can_refund": False,
        "refund_process": "请耐心等待退款到账"
    },
    "refunded": {
        "name": "已退款",
        "description": "退款已完成",
        "can_refund": False,
        "refund_process": "退款已完成，如有问题请联系客服"
    },
    "rejected": {
        "name": "已拒绝",
        "description": "退款申请被拒绝",
        "can_refund": True,
        "refund_process": "可根据拒绝原因重新申请"
    }
}

# ==================== 必须验证的信息 ====================
VERIFICATION_REQUIRED = {
    "order_info": {
        "items": [
            {
                "field": "订单号",
                "format": "ORD开头的12位数字，如 ORD202301001",
                "required": True,
                "description": "用于查询订单状态和商品信息"
            },
            {
                "field": "购买时间",
                "format": "YYYY-MM-DD",
                "required": True,
                "description": "确认是否在退款期限内"
            },
            {
                "field": "商品状态",
                "format": "文本描述",
                "required": True,
                "description": "确认商品是否完好，包装是否齐全"
            }
        ]
    },
    "refund_reason": {
        "items": [
            {
                "field": "退款原因",
                "format": "选择或填写",
                "required": True,
                "description": "如：质量问题、不喜欢、拍错了等"
            }
        ]
    }
}

# ==================== 常见问题解答 ====================
FAQ = {
    "refund_time": {
        "question": "退款需要多长时间？",
        "answer": "标准商品和数字商品：3-5个工作日；质量问题：2-3个工作日。具体时间取决于银行处理速度。"
    },
    "refund_fee": {
        "question": "退款有手续费吗？",
        "answer": "正常退款无手续费。如因质量问题退货，运费由商家承担。非质量问题退货，运费由客户承担。"
    },
    "refund_method": {
        "question": "退款怎么退回来？",
        "answer": "退款会原路退回您的支付账户，即您付款时使用的银行卡或支付宝等账户。"
    },
    "partial_refund": {
        "question": "可以部分退款吗？",
        "answer": "如订单包含多个商品，可以针对单个商品申请退款。部分退款按比例处理。"
    },
    "exchange": {
        "question": "可以换货吗？",
        "answer": "支持换货。请在7天内联系客服，说明换货原因和期望的商品规格。"
    },
    "order_cancel": {
        "question": "怎么取消订单？",
        "answer": "待发货订单可直接取消；已发货订单需要先拒收或退货；已签收订单按退款流程处理。"
    },
    "no_order_number": {
        "question": "找不到订单号怎么办？",
        "answer": "请到您的账户中心查看订单历史，或查收购买时发送的订单确认邮件和短信。"
    }
}

# ==================== 客服标准话术 ====================
STANDARD_RESPONSES = {
    "greeting": [
        "您好！我是XX公司客服，很高兴为您服务。",
        "您好！请问有什么可以帮助您的？",
        "欢迎咨询XX商城，我是智能客服，请问有什么可以帮您？"
    ],
    "ask_order_info": [
        "为了更好地为您处理退款，请您提供以下信息：订单号、购买时间、商品状态和退款原因。",
        "请问您能提供一下订单号吗？订单号是ORD开头的12位数字。",
        "我需要核实一下您的订单信息。请您提供订单号和购买时间，好吗？"
    ],
    "verify_info": [
        "感谢您提供的信息。我正在为您查询订单...",
        "收到，请稍等，我马上为您核实订单信息。",
        "好的，让我查看一下您的订单详情。"
    ],
    "explain_policy": [
        "根据我们的退款政策，{type}商品{time_limit}内可以申请退款。{condition}",
        "关于退款，{process_time}内会处理完成。退款会原路退回到您的支付账户。"
    ],
    "refuse_violation": [
        "我理解您的心情，但根据公司规定，我需要先验证您的订单信息才能为您办理退款。",
        "为了保障您的资金安全，请您提供完整的订单信息，我会尽快为您处理。"
    ]
}

# ==================== 违规风险提示 ====================
VIOLATION_RISKS = {
    "unauthorized_refund": {
        "risk": "未验证订单信息直接承诺退款",
        "consequence": "可能导致资金损失，违反公司规定",
        "prevention": "必须先验证订单号、购买时间、商品状态"
    },
    "over_promise": {
        "risk": "使用绝对性词汇承诺无法保证的服务",
        "consequence": "客户期望过高，导致投诉和纠纷",
        "prevention": "避免使用'100%'、'绝对'、'一定'等词汇"
    },
    "skip_verification": {
        "risk": "省略必要的验证流程",
        "consequence": "无法确认客户身份和订单真实性",
        "prevention": "严格按照标准流程验证所有必需信息"
    }
}

# ==================== 辅助函数 ====================

def get_refund_policy_text() -> str:
    """获取退款政策文本（用于插入System Prompt）"""
    lines = []
    for policy_type, policy_info in REFUND_POLICIES.items():
        lines.append(f"- {policy_info['name']}: {policy_info['time_limit']}, {policy_info['condition']}, 处理时间{policy_info['process_time']}")
    return "\n".join(lines)


def get_order_status_text() -> str:
    """获取订单状态文本（用于插入System Prompt）"""
    lines = []
    for status_code, status_info in ORDER_STATUS_MAP.items():
        refund_note = "可退款" if status_info['can_refund'] else "不可退款"
        lines.append(f"- {status_info['name']}({status_code}): {status_info['description']}, {refund_note}")
    return "\n".join(lines)


def get_verification_required_text() -> str:
    """获取必需验证信息文本（用于插入System Prompt）"""
    lines = []
    for category, category_info in VERIFICATION_REQUIRED.items():
        lines.append(f"\n【{category}】")
        for item in category_info['items']:
            required_mark = "✓ 必需" if item['required'] else "可选"
            lines.append(f"- {item['field']}: {item['description']} ({required_mark})")
    return "\n".join(lines)


def get_faq_text() -> str:
    """获取FAQ文本（用于插入System Prompt）"""
    lines = []
    for question, answer in FAQ.items():
        lines.append(f"Q: {answer['question']}\nA: {answer['answer']}")
    return "\n\n".join(lines)


# ==================== 导出 ====================

__all__ = [
    "REFUND_POLICIES",
    "ORDER_STATUS_MAP",
    "VERIFICATION_REQUIRED",
    "FAQ",
    "STANDARD_RESPONSES",
    "VIOLATION_RISKS",
    "get_refund_policy_text",
    "get_order_status_text",
    "get_verification_required_text",
    "get_faq_text",
]
