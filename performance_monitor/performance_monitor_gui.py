#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监视器 - 图形化版本
使用matplotlib实时显示性能指标
"""

import psutil
import time
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec
import matplotlib.font_manager as fm
import platform


def setup_chinese_font():
    """设置中文字体"""
    system = platform.system()

    # Windows系统字体列表
    if system == 'Windows':
        font_list = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']
    # macOS系统字体列表
    elif system == 'Darwin':
        font_list = ['PingFang SC', 'Heiti SC', 'STHeiti', 'Arial Unicode MS']
    # Linux系统字体列表
    else:
        font_list = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC',
                     'Droid Sans Fallback', 'AR PL UMing CN', 'AR PL UKai CN']

    # 检测系统可用的中文字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    chinese_font = None

    for font in font_list:
        if font in available_fonts:
            chinese_font = font
            break

    if chinese_font:
        plt.rcParams['font.sans-serif'] = [chinese_font]
        print(f"使用中文字体: {chinese_font}")
    else:
        print("警告: 未找到合适的中文字体，中文可能无法正常显示")
        # 使用系统默认字体作为回退
        plt.rcParams['font.sans-serif'] = font_list

    plt.rcParams['axes.unicode_minus'] = False


# 设置中文字体
setup_chinese_font()


class PerformanceMonitorGUI:
    """图形化性能监视器"""

    def __init__(self, history_size=60):
        """
        初始化性能监视器

        Args:
            history_size: 历史数据保留的条目数
        """
        self.history_size = history_size
        self.timestamps = deque(maxlen=history_size)
        self.cpu_usage = deque(maxlen=history_size)
        self.memory_usage = deque(maxlen=history_size)
        self.disk_usage = deque(maxlen=history_size)
        self.network_upload = deque(maxlen=history_size)
        self.network_download = deque(maxlen=history_size)

        self.last_network_stats = None

        # 创建图形界面
        self.fig = plt.figure(figsize=(14, 10))
        self.fig.suptitle('系统性能监视器', fontsize=16, fontweight='bold')

        # 使用GridSpec布局
        gs = GridSpec(3, 2, figure=self.fig, hspace=0.3, wspace=0.3)

        # CPU图表
        self.ax_cpu = self.fig.add_subplot(gs[0, 0])
        self.line_cpu, = self.ax_cpu.plot([], [], 'r-', linewidth=2)
        self.ax_cpu.set_title('CPU 使用率 (%)', fontsize=12)
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.grid(True, alpha=0.3)

        # 内存图表
        self.ax_memory = self.fig.add_subplot(gs[0, 1])
        self.line_memory, = self.ax_memory.plot([], [], 'b-', linewidth=2)
        self.ax_memory.set_title('内存 使用率 (%)', fontsize=12)
        self.ax_memory.set_ylim(0, 100)
        self.ax_memory.grid(True, alpha=0.3)

        # 磁盘图表
        self.ax_disk = self.fig.add_subplot(gs[1, 0])
        self.line_disk, = self.ax_disk.plot([], [], 'g-', linewidth=2)
        self.ax_disk.set_title('磁盘 使用率 (%)', fontsize=12)
        self.ax_disk.set_ylim(0, 100)
        self.ax_disk.grid(True, alpha=0.3)

        # 网络图表
        self.ax_network = self.fig.add_subplot(gs[1, 1])
        self.line_upload, = self.ax_network.plot([], [], 'orange', linewidth=2, label='上传')
        self.line_download, = self.ax_network.plot([], [], 'purple', linewidth=2, label='下载')
        self.ax_network.set_title('网络 流量 (KB/s)', fontsize=12)
        self.ax_network.legend()
        self.ax_network.grid(True, alpha=0.3)

        # 系统信息文本
        self.ax_info = self.fig.add_subplot(gs[2, :])
        self.ax_info.axis('off')
        self.info_text = self.ax_info.text(0.1, 0.5, '', fontsize=11,
                                          verticalalignment='center')

    def get_system_stats(self):
        """获取系统统计信息"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()

        # 计算网络速度
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

        # 获取进程信息
        top_cpu_process = self.get_top_process('cpu')
        top_memory_process = self.get_top_process('memory')

        return {
            'cpu': cpu_percent,
            'memory': mem.percent,
            'disk': disk.percent,
            'upload': upload_speed,
            'download': download_speed,
            'total_memory_gb': mem.total / (1024 ** 3),
            'used_memory_gb': mem.used / (1024 ** 3),
            'total_disk_gb': disk.total / (1024 ** 3),
            'used_disk_gb': disk.used / (1024 ** 3),
            'cpu_count': psutil.cpu_count(),
            'top_cpu_process': top_cpu_process,
            'top_memory_process': top_memory_process
        }

    def get_top_process(self, sort_by='cpu'):
        """获取占用资源最多的进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if sort_by == 'cpu':
            sorted_procs = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)
        else:
            sorted_procs = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)

        return sorted_procs[0] if sorted_procs else {'pid': 0, 'name': 'N/A', 'cpu_percent': 0, 'memory_percent': 0}

    def update(self, frame):
        """更新图表数据"""
        stats = self.get_system_stats()

        timestamp = datetime.now().strftime('%H:%M:%S')
        self.timestamps.append(timestamp)
        self.cpu_usage.append(stats['cpu'])
        self.memory_usage.append(stats['memory'])
        self.disk_usage.append(stats['disk'])
        self.network_upload.append(stats['upload'])
        self.network_download.append(stats['download'])

        # 更新CPU图表
        self.line_cpu.set_data(range(len(self.cpu_usage)), self.cpu_usage)
        self.ax_cpu.set_xlim(0, max(self.history_size, len(self.cpu_usage)))
        self.ax_cpu.set_title(f'CPU 使用率: {stats["cpu"]:.1f}%', fontsize=12)

        # 更新内存图表
        self.line_memory.set_data(range(len(self.memory_usage)), self.memory_usage)
        self.ax_memory.set_xlim(0, max(self.history_size, len(self.memory_usage)))
        self.ax_memory.set_title(f'内存 使用率: {stats["memory"]:.1f}%', fontsize=12)

        # 更新磁盘图表
        self.line_disk.set_data(range(len(self.disk_usage)), self.disk_usage)
        self.ax_disk.set_xlim(0, max(self.history_size, len(self.disk_usage)))
        self.ax_disk.set_title(f'磁盘 使用率: {stats["disk"]:.1f}%', fontsize=12)

        # 更新网络图表
        self.line_upload.set_data(range(len(self.network_upload)), self.network_upload)
        self.line_download.set_data(range(len(self.network_download)), self.network_download)
        self.ax_network.set_xlim(0, max(self.history_size, len(self.network_upload)))

        # 动态调整网络图表Y轴
        max_net = max(max(self.network_upload, default=0), max(self.network_download, default=0))
        self.ax_network.set_ylim(0, max(100, max_net * 1.2))
        self.ax_network.set_title(f'网络流量 - 上传: {stats["upload"]:.1f} KB/s, 下载: {stats["download"]:.1f} KB/s',
                                   fontsize=12)

        # 更新系统信息
        info_str = f"""
        ┌─────────────────────────────────────────────────────────────────────┐
        │  系统信息 [{timestamp}]                                              │
        ├─────────────────────────────────────────────────────────────────────┤
        │  CPU核心数: {stats['cpu_count']}                    │
        │  内存: {stats['used_memory_gb']:.2f} GB / {stats['total_memory_gb']:.2f} GB ({stats['memory']:.1f}%)                    │
        │  磁盘: {stats['used_disk_gb']:.2f} GB / {stats['total_disk_gb']:.2f} GB ({stats['disk']:.1f}%)                    │
        │  CPU最高占用进程: PID {stats['top_cpu_process']['pid']} - {stats['top_cpu_process']['name']} ({stats['top_cpu_process']['cpu_percent']:.1f}%)         │
        │  内存最高占用进程: PID {stats['top_memory_process']['pid']} - {stats['top_memory_process']['name']} ({stats['top_memory_process']['memory_percent']:.1f}%)       │
        └─────────────────────────────────────────────────────────────────────┘
        """
        self.info_text.set_text(info_str)

        return self.line_cpu, self.line_memory, self.line_disk, self.line_upload, self.line_download, self.info_text

    def start(self, interval=1000):
        """
        启动监控

        Args:
            interval: 更新间隔（毫秒）
        """
        print("图形化性能监视器启动中...")
        print("关闭窗口以退出程序")

        ani = animation.FuncAnimation(
            self.fig,
            self.update,
            interval=interval,
            blit=False
        )

        plt.show()


def main():
    """主函数"""
    monitor = PerformanceMonitorGUI(history_size=60)
    monitor.start(interval=1000)


if __name__ == '__main__':
    main()
