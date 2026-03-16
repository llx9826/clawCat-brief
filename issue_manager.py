#!/usr/bin/env python3
"""
AI/CV Weekly - 期号管理器（线程/进程安全）
"""

import json
import fcntl
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class IssueManager:
    """期号管理器（文件锁保证并发安全）"""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent
        self.counter_file = self.data_dir / "issue_counter.json"
        self.lock_file = self.data_dir / ".issue_counter.lock"
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _acquire_lock(self):
        """获取文件锁"""
        self.lock_fd = open(self.lock_file, "w")
        fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX)
    
    def _release_lock(self):
        """释放文件锁"""
        if hasattr(self, 'lock_fd') and self.lock_fd:
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
            self.lock_fd.close()
    
    def get_next_issue(self) -> int:
        """
        获取下一期号，并自动递增
        
        Returns:
            int: 新的期号
        """
        self._acquire_lock()
        try:
            current = self._load_counter()
            next_issue = current + 1
            self._save_counter(next_issue)
            return next_issue
        finally:
            self._release_lock()
    
    def peek_current_issue(self) -> int:
        """
        查看当前期号（不递增）
        
        Returns:
            int: 当前期号
        """
        self._acquire_lock()
        try:
            return self._load_counter()
        finally:
            self._release_lock()
    
    def _load_counter(self) -> int:
        """加载期号（内部方法，调用前需获取锁）"""
        if self.counter_file.exists():
            try:
                with open(self.counter_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("counter", 0)
            except (json.JSONDecodeError, IOError):
                # 文件损坏，尝试备份并恢复
                self._backup_corrupted_file()
                return 0
        return 0
    
    def _save_counter(self, counter: int):
        """保存期号（内部方法，调用前需获取锁）"""
        # 先写入临时文件，再原子重命名
        temp_file = self.counter_file.with_suffix('.tmp')
        data = {
            "counter": counter,
            "updated_at": datetime.now().isoformat(),
            "version": 1
        }
        
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # 原子重命名
        temp_file.replace(self.counter_file)
    
    def _backup_corrupted_file(self):
        """备份损坏的文件"""
        if self.counter_file.exists():
            backup_name = self.counter_file.with_suffix(
                f'.corrupted.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            self.counter_file.rename(backup_name)
            print(f"已备份损坏的计数器文件: {backup_name}")
    
    def reset_counter(self, value: int = 0):
        """
        重置期号（谨慎使用）
        
        Args:
            value: 重置到的期号
        """
        self._acquire_lock()
        try:
            self._save_counter(value)
            print(f"期号已重置为: {value}")
        finally:
            self._release_lock()
    
    def get_history(self) -> Optional[dict]:
        """获取历史记录"""
        self._acquire_lock()
        try:
            if self.counter_file.exists():
                with open(self.counter_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except:
            return None
        finally:
            self._release_lock()


if __name__ == "__main__":
    # 测试
    manager = IssueManager()
    print(f"当前期号: {manager.peek_current_issue()}")
    print(f"下一期号: {manager.get_next_issue()}")
    print(f"更新后期号: {manager.peek_current_issue()}")
