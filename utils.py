"""
工具函数模块

提供通用的辅助功能
"""

import json
import re
from typing import Any, Dict


def generate_event_brief(request_id: str, payload: Any) -> str:
    """
    生成事件简报代码
    
    格式: ABCDE-<request_id>
    - A: 标签首字母 (D/E/P/Q/R/S 或 N)
    - B: 子类型标识
    - CDE: 页码 (000-999)
    
    Args:
        request_id: 请求 ID
        payload: 数据载荷
        
    Returns:
        事件简报字符串
    """
    def _ascii(s: Any, default: str = "") -> str:
        """转换为 ASCII 字符串"""
        try:
            out = str(s).encode("ascii", "ignore").decode("ascii")
            return out if out else default
        except Exception:
            return default
    
    def _coerce_int(x: Any, default: int = 0) -> int:
        """强制转换为整数"""
        try:
            if isinstance(x, bool):
                return default
            if isinstance(x, (int, float)):
                return int(x)
            s = str(x).strip()
            m = re.match(r"^(-?\d+)", s)
            return int(m.group(1)) if m else default
        except Exception:
            return default
    
    try:
        # 解析 payload
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        
        if not isinstance(payload, dict):
            payload = {}
        
        update_params = payload.get("update_params", {})
        
        # 第一位：标签
        raw_label = str(payload.get("label", "")).strip().upper()
        first = raw_label[:1] if raw_label else "N"
        if first not in {"D", "E", "P", "Q", "R", "S"}:
            first = "N"
        
        # 第二位：子类型
        second = "N"
        
        if first == "D":  # 对话
            messages = update_params.get("messages") or []
            author = None
            if isinstance(messages, list) and messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    author = (
                        last_msg.get("author_type") or
                        last_msg.get("role") or
                        last_msg.get("author")
                    )
            
            author_str = str(author or "").strip().lower()
            if author_str in {"student", "user", "human", "learner", "pupil"}:
                second = "S"
            elif author_str in {"ai_assistant", "assistant", "bot", "model"}:
                second = "A"
                
        elif first == "P":  # 页面
            enter_type = str(update_params.get("enter_type", "")).strip().lower()
            # 规范化
            enter_map = {
                "first": "first_enter",
                "up": "up_enter",
                "down": "down_enter",
                "direct": "direct_enter",
                "auto": "auto_enter"
            }
            enter_type = enter_map.get(enter_type, enter_type)
            
            type_map = {
                "first_enter": "F",
                "up_enter": "U",
                "down_enter": "D",
                "direct_enter": "R",
                "auto_enter": "A"
            }
            second = type_map.get(enter_type, "N")
        
        # 后三位：页码
        if first in {"D", "P"}:
            page = _coerce_int(update_params.get("page_number", 0))
        elif first in {"Q", "R"}:
            page = _coerce_int(update_params.get("page_number_of_quiz", 0))
        else:
            page = 0
        
        # 限制范围
        page = max(0, min(999, page))
        page_str = f"{page:03d}"
        
        # 组合代码
        code = f"{first}{second}{page_str}"
        
        # 确保 ASCII
        code_ascii = _ascii(code, "NN000")
        request_id_ascii = _ascii(request_id, "MISSING")
        
        return f"{code_ascii}-{request_id_ascii}"
        
    except Exception:
        # 失败时返回默认值
        return f"NN000-{_ascii(request_id, 'MISSING')}"

