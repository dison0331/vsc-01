#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监视器
监控系统资源使用情况，包括CPU、内存、磁盘和网络
"""

import psutil
import time
import os
from datetime import datetime
from collections import deque
import json


class PerformanceMonitor:
    """性能监视器主类"""

    def __init__(self, history_size=60):
        """
        初始化性能监视器

        Args:
            history_size: 历史数据保留的条目数
        """
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.network_history = deque(maxlen=history_size)
        self.last_network_stats = None

    def get_cpu_info(self):
        """获取CPU使用率信息"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'usage_percent': cpu_percent,
            'core_count': cpu_count,
            'frequency_mhz': cpu_freq.current if cpu_freq else 0
        }
        self.cpu_history.append(info)
        return info

    def get_memory_info(self):
        """获取内存使用率信息"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_gb': mem.total / (1024 ** 3),
            'available_gb': mem.available / (1024 ** 3),
            'used_gb': mem.used / (1024 ** 3),
            'usage_percent': mem.percent,
            'swap_total_gb': swap.total / (1024 ** 3),
            'swap_used_gb': swap.used / (1024 ** 3),
            'swap_percent': swap.percent
        }
        self.memory_history.append(info)
        return info

    def get_disk_info(self):
        """获取磁盘使用率信息"""
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()

        info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_gb': disk.total / (1024 ** 3),
            'used_gb': disk.used / (1024 ** 3),
            'free_gb': disk.free / (1024 ** 3),
            'usage_percent': disk.percent,
            'read_mb': disk_io.read_bytes / (1024 ** 2) if disk_io else 0,
            'write_mb': disk_io.write_bytes / (1024 ** 2) if disk_io else 0
        }
        self.disk_history.append(info)
        return info

    def get_network_info(self):
        """获取网络流量信息"""
        net_io = psutil.net_io_counters()

        if self.last_network_stats:
            time_diff = time.time() - self.last_network_stats['time']
            bytes_sent_diff = net_io.bytes_sent - self.last_network_stats['bytes_sent']
            bytes_recv_diff = net_io.bytes_recv - self.last_network_stats['bytes_recv']

            if time_diff > 0:
                upload_speed = (bytes_sent_diff / time_diff) / 1024  # KB/s
                download_speed = (bytes_recv_diff / time_diff) / 1024  # KB/s
            else:
                upload_speed = 0
                download_speed = 0
        else:
            upload_speed = 0
            download_speed = 0

        self.last_network_stats = {
            'time': time.time(),
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv
        }

        info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'bytes_sent_gb': net_io.bytes_sent / (1024 ** 3),
            'bytes_recv_gb': net_io.bytes_recv / (1024 ** 3),
            'upload_speed_kbs': upload_speed,
            'download_speed_kbs': download_speed
        }
        self.network_history.append(info)
        return info

    def get_process_info(self, limit=5):
        """获取占用资源最多的进程信息"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # 按CPU使用率排序
        top_cpu = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:limit]
        # 按内存使用率排序
        top_memory = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:limit]

        return {
            'top_cpu': top_cpu,
            'top_memory': top_memory
        }

    def get_all_stats(self):
        """获取所有性能指标"""
        return {
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info(),
            'processes': self.get_process_info()
        }

    def print_stats(self, stats):
        """打印性能统计信息"""
        os.system('cls' if os.name == 'nt' else 'clear')  # 清屏

        print("=" * 80)
        print(f"性能监视器 - {stats['cpu']['timestamp']}")
        print("=" * 80)
        print()

        # CPU信息
        print("【CPU 使用率】")
        print(f"  使用率: {stats['cpu']['usage_percent']:.1f}%")
        print(f"  核心数: {stats['cpu']['core_count']}")
        print(f"  频率: {stats['cpu']['frequency_mhz']:.0f} MHz")
        print()

        # 内存信息
        print("【内存 使用率】")
        print(f"  总内存: {stats['memory']['total_gb']:.2f} GB")
        print(f"  已使用: {stats['memory']['used_gb']:.2f} GB ({stats['memory']['usage_percent']:.1f}%)")
        print(f"  可用: {stats['memory']['available_gb']:.2f} GB")
        print(f"  交换分区: {stats['memory']['swap_used_gb']:.2f} GB / {stats['memory']['swap_total_gb']:.2f} GB")
        print()

        # 磁盘信息
        print("【磁盘 使用率】")
        print(f"  总空间: {stats['disk']['total_gb']:.2f} GB")
        print(f"  已使用: {stats['disk']['used_gb']:.2f} GB ({stats['disk']['usage_percent']:.1f}%)")
        print(f"  可用: {stats['disk']['free_gb']:.2f} GB")
        print()

        # 网络信息
        print("【网络 流量】")
        print(f"  上传速度: {stats['network']['upload_speed_kbs']:.2f} KB/s")
        print(f"  下载速度: {stats['network']['download_speed_kbs']:.2f} KB/s")
        print(f"  总上传: {stats['network']['bytes_sent_gb']:.2f} GB")
        print(f"  总下载: {stats['network']['bytes_recv_gb']:.2f} GB")
        print()

        # 进程信息
        print("【CPU 占用最高的进程】")
        for i, proc in enumerate(stats['processes']['top_cpu'], 1):
            print(f"  {i}. PID: {proc['pid']:<6} 名称: {proc['name']:<20} CPU: {proc['cpu_percent']:.1f}%")
        print()

        print("【内存 占用最高的进程】")
        for i, proc in enumerate(stats['processes']['top_memory'], 1):
            print(f"  {i}. PID: {proc['pid']:<6} 名称: {proc['name']:<20} 内存: {proc['memory_percent']:.1f}%")
        print()

        print("=" * 80)
        print("按 Ctrl+C 退出")
        print("=" * 80)

    def save_to_json(self, filename='performance_log.json'):
        """保存历史数据到JSON文件"""
        data = {
            'cpu': list(self.cpu_history),
            'memory': list(self.memory_history),
            'disk': list(self.disk_history),
            'network': list(self.network_history)
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def monitor(self, interval=2):
        """
        开始监控

        Args:
            interval: 监控间隔（秒）
        """
        print("性能监视器启动中...")
        time.sleep(1)

        try:
            while True:
                stats = self.get_all_stats()
                self.print_stats(stats)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n正在保存数据...")
            self.save_to_json()
            print("数据已保存到 performance_log.json")
            print("性能监视器已停止")


def main():
    """主函数"""
    monitor = PerformanceMonitor(history_size=60)
    monitor.monitor(interval=2)


if __name__ == '__main__':
    main()
