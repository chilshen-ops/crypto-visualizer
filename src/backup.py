"""
数据备份模块
"""
import os
import shutil
import time
from datetime import datetime
from typing import Optional, List
from threading import Thread

from .logger import get_logger
from .notifier import get_notifier
import config


class Backup:
    """数据备份器"""
    
    def __init__(self):
        self.logger = get_logger("backup")
        self.notifier = get_notifier()
        
        # 加载配置
        backup_config = config.BACKUP_CONFIG
        self.enabled = backup_config.get("enabled", False)
        self.interval_hours = backup_config.get("interval_hours", 24)
        self.keep_days = backup_config.get("keep_days", 7)
        self.backup_dir = backup_config.get("backup_dir", "backups")
        
        # 状态
        self.backup_thread: Optional[Thread] = None
        self.running = False
    
    def start(self):
        """启动定时备份"""
        if not self.enabled:
            self.logger.info("备份功能未启用")
            return
        
        if self.running:
            self.logger.warning("备份已在运行")
            return
        
        self.running = True
        self.backup_thread = Thread(target=self._backup_loop, daemon=True)
        self.backup_thread.start()
        
        self.logger.info(f"定时备份已启动 (间隔: {self.interval_hours}小时)")
        
        # 立即执行一次备份
        self.backup_now()
    
    def stop(self):
        """停止定时备份"""
        self.running = False
        if self.backup_thread:
            self.backup_thread.join(timeout=5)
        self.logger.info("定时备份已停止")
    
    def backup_now(self) -> bool:
        """
        立即执行备份
        
        Returns:
            是否成功
        """
        self.logger.info("开始执行备份...")
        
        try:
            # 创建备份目录
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
            
            # 备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # 备份 data 目录
            data_dir = "data"
            if os.path.exists(data_dir):
                shutil.copytree(data_dir, backup_path)
                self.logger.info(f"数据已备份到: {backup_path}")
            else:
                self.logger.warning("data 目录不存在，跳过备份")
                return False
            
            # 备份 config
            config_file = "config.py"
            if os.path.exists(config_file):
                shutil.copy2(config_file, os.path.join(backup_path, "config.py"))
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            # 发送通知
            if self.notifier.enabled:
                self.notifier.notify_status("数据备份", "完成", backup_name)
            
            self.logger.info("备份完成")
            return True
            
        except Exception as e:
            self.logger.error(f"备份失败: {e}")
            
            if self.notifier.enabled:
                self.notifier.notify_error("备份失败", str(e))
            
            return False
    
    def _backup_loop(self):
        """定时备份循环"""
        while self.running:
            try:
                # 等待 interval 小时
                wait_seconds = self.interval_hours * 3600
                
                for _ in range(wait_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                
                if self.running:
                    self.backup_now()
                    
            except Exception as e:
                self.logger.error(f"备份循环异常: {e}")
                time.sleep(60)  # 异常后等1分钟
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            # 获取所有备份目录
            backups = []
            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(item_path) and item.startswith("backup_"):
                    mtime = os.path.getmtime(item_path)
                    backups.append((item_path, mtime))
            
            # 按时间排序
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超过 keep_days 的备份
            now = time.time()
            days_seconds = self.keep_days * 86400
            
            for backup_path, mtime in backups:
                if now - mtime > days_seconds:
                    shutil.rmtree(backup_path)
                    self.logger.info(f"已删除旧备份: {backup_path}")
                    
        except Exception as e:
            self.logger.error(f"清理旧备份失败: {e}")
    
    def list_backups(self) -> List[dict]:
        """
        列出所有备份
        
        Returns:
            备份列表
        """
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            if os.path.isdir(item_path) and item.startswith("backup_"):
                stat = os.stat(item_path)
                backups.append({
                    "name": item,
                    "path": item_path,
                    "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "size": self._get_dir_size(item_path)
                })
        
        # 按时间排序
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        恢复备份
        
        Args:
            backup_name: 备份名称
            
        Returns:
            是否成功
        """
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            self.logger.error(f"备份不存在: {backup_name}")
            return False
        
        try:
            # 备份当前 data 目录
            if os.path.exists("data"):
                shutil.move("data", "data_backup_before_restore")
            
            # 恢复
            shutil.copytree(backup_path, "data")
            
            # 删除临时备份
            if os.path.exists("data_backup_before_restore"):
                shutil.rmtree("data_backup_before_restore")
            
            self.logger.info(f"已恢复备份: {backup_name}")
            
            if self.notifier.enabled:
                self.notifier.notify_status("数据恢复", "完成", backup_name)
            
            return True
            
        except Exception as e:
            self.logger.error(f"恢复失败: {e}")
            
            # 恢复临时备份
            if os.path.exists("data_backup_before_restore"):
                shutil.move("data_backup_before_restore", "data")
            
            return False
    
    def _get_dir_size(self, path: str) -> str:
        """获取目录大小"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
        
        # 转换为可读格式
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total < 1024:
                return f"{total:.2f} {unit}"
            total /= 1024
        return f"{total:.2f} TB"


# 全局备份器
_backup: Optional[Backup] = None


def get_backup() -> Backup:
    """获取备份器实例"""
    global _backup
    if _backup is None:
        _backup = Backup()
    return _backup


def init_backup(enabled: bool = None, interval_hours: int = None) -> Backup:
    """初始化备份器"""
    global _backup
    _backup = Backup()
    
    if enabled is not None:
        _backup.enabled = enabled
    if interval_hours is not None:
        _backup.interval_hours = interval_hours
    
    return _backup
