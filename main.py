import pygame
import sys
import time
import math
import tkinter as tk
from tkinter import filedialog
import os

# --- 配置区域 ---
WIDTH, HEIGHT = 800, 600
FPS = 30
FONT_SIZE_ACTIVE = 40
FONT_SIZE_NORMAL = 24
COLOR_ACTIVE = (255, 255, 255)     # 高亮歌词颜色 (白)
COLOR_NORMAL = (150, 150, 150)     # 普通歌词颜色 (灰)
BG_COLOR = (20, 20, 20)            # 默认背景色

class MusicVisualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("酷炫歌词同步播放器")
        self.clock = pygame.time.Clock()
        self.font_lrc = pygame.font.SysFont("Microsoft YaHei", FONT_SIZE_NORMAL)
        self.font_lrc_active = pygame.font.SysFont("Microsoft YaHei", FONT_SIZE_ACTIVE, bold=True)
        
        self.mp3_path = ""
        self.lrc_path = ""
        self.img_path = ""
        
        self.lyrics = {} # {time: text}
        self.timestamps = []
        self.cover_img = None
        self.bg_img = None
        
        # 选择文件
        self.select_files()
        
        if self.mp3_path and self.lrc_path:
            self.parse_lrc(self.lrc_path)
            self.prepare_images()
            self.run()
        else:
            sys.exit()

    def select_files(self):
        root = tk.Tk()
        root.withdraw() # 隐藏主窗口
        
        # 提示框
        root.update()
        tk.messagebox.showinfo("步骤 1/3", "请选择 MP3 歌曲文件")
        self.mp3_path = filedialog.askopenfilename(title="选择 MP3", filetypes=[("MP3", "*.mp3")])
        
        if not self.mp3_path: return

        tk.messagebox.showinfo("步骤 2/3", "请选择 LRC 歌词文件")
        self.lrc_path = filedialog.askopenfilename(title="选择 LRC", filetypes=[("LRC", "*.lrc")])
        
        tk.messagebox.showinfo("步骤 3/3", "请选择 封面图片 (JPG/PNG)")
        self.img_path = filedialog.askopenfilename(title="选择封面", filetypes=[("Images", "*.jpg *.png *.jpeg")])
        
        root.destroy()

    def parse_lrc(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f: lines = f.readlines()
        except:
            try:
                with open(path, 'r', encoding='gbk') as f: lines = f.readlines()
            except:
                return
        
        import re
        regex = re.compile(r'\[(\d+):(\d+\.?\d*)\](.*)')
        for line in lines:
            match = regex.match(line)
            if match:
                t = int(match.group(1)) * 60 + float(match.group(2))
                text = match.group(3).strip()
                if text:
                    self.lyrics[t] = text
                    self.timestamps.append(t)
        self.timestamps.sort()

    def prepare_images(self):
        if self.img_path and os.path.exists(self.img_path):
            img = pygame.image.load(self.img_path).convert_alpha()
        else:
            # 默认封面：灰色方块
            img = pygame.Surface((300, 300))
            img.fill((50, 50, 50))
        
        # 制作背景（模糊效果：通过极度缩小再放大实现伪模糊）
        bg = pygame.transform.smoothscale(img, (WIDTH // 10, HEIGHT // 10))
        self.bg_img = pygame.transform.smoothscale(bg, (WIDTH, HEIGHT))
        
        # 添加黑色遮罩让背景变暗
        dark_surface = pygame.Surface((WIDTH, HEIGHT))
        dark_surface.set_alpha(180) # 透明度 0-255
        dark_surface.fill((0, 0, 0))
        self.bg_img.blit(dark_surface, (0, 0))

        # 制作中间封面
        base_scale = min(WIDTH, HEIGHT) // 2.5
        self.cover_img = pygame.transform.smoothscale(img, (int(base_scale), int(base_scale)))
        # 加个白色边框
        pygame.draw.rect(self.cover_img, (255,255,255), self.cover_img.get_rect(), 5)

    def get_current_lyric_index(self, current_time):
        idx = -1
        for i, t in enumerate(self.timestamps):
            if t <= current_time:
                idx = i
            else:
                break
        return idx

    def run(self):
        pygame.mixer.music.load(self.mp3_path)
        pygame.mixer.music.play()
        start_ticks = pygame.time.get_ticks()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # 计算播放时间
            if pygame.mixer.music.get_busy():
                current_time = (pygame.time.get_ticks() - start_ticks) / 1000.0
            else:
                running = False # 播放结束退出

            # 绘制背景
            self.screen.blit(self.bg_img, (0, 0))

            # 绘制封面 (居中偏上)
            cov_rect = self.cover_img.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
            self.screen.blit(self.cover_img, cov_rect)

            # 绘制歌词
            curr_idx = self.get_current_lyric_index(current_time)
            
            # 显示当前句和前后几句
            center_y = HEIGHT // 2 + 120
            
            for i in range(curr_idx - 2, curr_idx + 3):
                if 0 <= i < len(self.timestamps):
                    t = self.timestamps[i]
                    text = self.lyrics[t]
                    
                    if i == curr_idx:
                        # 当前句：大字体，白色，带一点浮动特效
                        offset = math.sin(time.time() * 5) * 2
                        surf = self.font_lrc_active.render(text, True, COLOR_ACTIVE)
                        rect = surf.get_rect(center=(WIDTH//2, center_y + offset))
                    else:
                        # 其他句：小字体，灰色，位置偏移
                        diff = i - curr_idx
                        surf = self.font_lrc.render(text, True, COLOR_NORMAL)
                        rect = surf.get_rect(center=(WIDTH//2, center_y + diff * 40))
                    
                    self.screen.blit(surf, rect)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    MusicVisualizer()
