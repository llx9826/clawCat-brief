#!/usr/bin/env python3
"""
AI/CV Weekly - 邮件发送模块
"""

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Dict, Optional
from pathlib import Path


class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载邮箱配置"""
        config_paths = [
            Path(__file__).parent.parent / "email_config.json",
            Path("/home/gem/workspace/agent/workspace/email_config.json")
        ]
        
        for path in config_paths:
            if path.exists():
                with open(path, "r") as f:
                    return json.load(f)
        
        return {}
    
    def send(self, subject: str, html_content: str, text_content: str = None, to_email: str = None, to_emails: list = None) -> bool:
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            html_content: HTML 内容
            text_content: 纯文本内容（可选）
            to_email: 收件人（可选，默认使用配置）
            to_emails: 多个收件人列表（可选）
        
        Returns:
            bool: 是否成功
        """
        if not self.config:
            print("❌ 邮箱未配置")
            return False
        
        # 支持多个收件人
        recipients = []
        if to_emails:
            recipients = to_emails
        elif to_email:
            recipients = [to_email]
        else:
            receiver = self.config.get("receiver_email")
            if receiver:
                recipients = [receiver]
        
        if not recipients:
            print("❌ 收件人邮箱未设置")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(subject, "utf-8")
            # From 字段必须符合 RFC 标准
            sender_email = self.config['sender_email']
            msg["From"] = f"AI/CV Weekly <{sender_email}>"
            msg["To"] = ", ".join(recipients)
            
            # 添加纯文本版本
            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
            
            # 添加 HTML 版本
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # 连接 SMTP 并发送
            if self.config.get("use_ssl", True):
                server = smtplib.SMTP_SSL(
                    self.config["smtp_server"],
                    self.config["smtp_port"]
                )
            else:
                server = smtplib.SMTP(
                    self.config["smtp_server"],
                    self.config["smtp_port"]
                )
                server.starttls()
            
            server.login(self.config["sender_email"], self.config["sender_password"])
            server.sendmail(self.config["sender_email"], recipients, msg.as_string())
            server.quit()
            
            print(f"✅ 邮件已发送到：{', '.join(recipients)}")
            return True
            
        except Exception as e:
            print(f"❌ 邮件发送失败：{type(e).__name__}: {e}")
            return False
