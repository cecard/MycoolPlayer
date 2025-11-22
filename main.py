import sys
import os
import random
import math
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QSlider, QStackedWidget, QTextEdit, 
                             QMessageBox, QComboBox, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QUrl, QPoint, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import (QIcon, QPixmap, QPainter, QColor, QPen, QFont, 
                         QBrush, QLinearGradient, QTextCursor)

# --- 全局配置 ---
SUPPORTED_FORMATS = (
    '.mp3', '.flac', '.wav', '.ogg', '.m4a', '.wma', 
    '.aac', '.ape', '.opus', '.alac', '.aiff', '.mp2'
)

# 霓虹配色
ACCENT_COLOR = QColor(0, 229, 255)
ACCENT_HEX = "#00E5FF"

# --- 1. 背景动态粒子特效引擎 ---
class DynamicBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 关键：让鼠标事件穿透背景层，否则按钮点不动
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_anim)
        self.timer.start(30) # 30ms 刷新一次
        self.offset = 0
        
        # 初始化粒子
        for _ in range(50):
            self.particles.append({
                'x': random.random(), 'y': random.random(),
                'vx': (random.random()-0.5)*0.002, 'vy': (random.random()-0.5)*0.002,
                'size': random.randint(2, 5), 'alpha': random.randint(20, 100)
            })

    def update_anim(self):
        # 背景流光偏移
        self.offset += 0.002
        if self.offset > 1: self.offset = 0
        
        # 粒子运动
        for p in self.particles:
            p['x'] += p['vx']; p['y'] += p['vy']
            # 碰到边界反弹
            if p['x']<0 or p['x']>1: p['vx']*=-1
            if p['y']<0 or p['y']>1: p['vy']*=-1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # 1. 绘制流光渐变背景
        grad = QLinearGradient(0, 0, w, h)
        # 颜色随时间(offset)微调，产生呼吸感
        c1 = QColor(15, 15, 25)
        c2 = QColor(10, 10, 15)
        c3 = QColor(20, 20, 35)
        grad.setColorAt(0, c1)
        grad.setColorAt(0.5 + math.sin(self.offset*3)*0.1, c2)
        grad.setColorAt(1, c3)
        painter.fillRect(0, 0, w, h, grad)
        
        # 2. 绘制浮游粒子
        painter.setPen(Qt.PenStyle.NoPen)
        for p in self.particles:
            c = QColor(ACCENT_COLOR)
            c.setAlpha(p['alpha'])
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPoint(int(p['x']*w), int(p['y']*h)), p['size'], p['size'])

# --- 样式表 ---
STYLESHEET = f"""
QMainWindow {{ background-color: #121212; }}
QWidget {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background: transparent; }}

/* 列表样式 */
QListWidget {{ 
    background-color: rgba(30, 30, 30, 180); border: 1px solid rgba(255,255,255,0.1); 
    color: #DDD; font-size: 13px; padding: 5px; border-radius: 8px;
}}
QListWidget::item {{ height: 32px; padding-left: 5px; }}
QListWidget::item:selected {{ background-color: rgba(0, 229, 255, 0.15); color: {ACCENT_HEX}; border-left: 3px solid {ACCENT_HEX}; }}
QListWidget::item:hover {{ background-color: rgba(255, 255, 255, 0.05); }}

/* 按钮样式 */
QPushButton {{
    background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.1); 
    color: #EEE; font-size: 14px; border-radius: 6px; padding: 8px;
}}
QPushButton:hover {{ background-color: rgba(0, 229, 255, 0.1); border-color: {ACCENT_HEX}; }}

/* 功能按钮高亮 */
QPushButton#ActionBtn {{ background-color: rgba(0, 229, 255, 0.15); border: 1px solid {ACCENT_HEX}; color: {ACCENT_HEX}; font-weight: bold; }}
QPushButton#ActionBtn:checked {{ background-color: {ACCENT_HEX}; color: #000; }}

/* 底部栏 */
QFrame#BottomBar {{ background-color: rgba(15, 15, 15, 245); border-top: 1px solid #333; }}
QSlider::sub-page:horizontal {{ background: {ACCENT_HEX}; }}

/* 文本框 */
QTextEdit {{
    background-color: rgba(0,0,0,0.4); border: 1px solid #444; 
    color: #DDD; padding: 15px; border-radius: 8px; font-size: 16px; line-height: 160%;
}}
QComboBox {{ background-color: #222; color: #DDD; border: 1px solid #444; padding: 5px; }}
"""

# --- 图标绘制工具 ---
class ArtGenerator:
    @staticmethod
    def draw_icon(size=64):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor("#1A1A2E")))
        p.setPen(QPen(QColor(ACCENT_COLOR), 2))
        p.drawEllipse(2, 2, size-4, size-4)
        p.setPen(QPen(QColor(ACCENT_COLOR), 4))
        # 画个音符
        p.drawLine(int(size*0.4), int(size*0.3), int(size*0.4), int(size*0.7))
        p.drawLine(int(size*0.4), int(size*0.7), int(size*0.7), int(size*0.5))
        p.drawLine(int(size*0.7), int(size*0.5), int(size*0.4), int(size*0.3))
        p.end()
        return QIcon(pix)

    @staticmethod
    def draw_default_cover(size=300):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(25, 25, 30)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, size, size, 15, 15)
        # 简单的渐变
        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0, QColor(0, 229, 255, 100))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(0, 0, size, size, 15, 15)
        p.setPen(QColor(255,255,255))
        p.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "MUSE")
        p.end()
        return pix

# --- 主程序 ---
class ModernPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MusePlayer Ultimate (集成版)")
        self.resize(1100, 750)
        self.setStyleSheet(STYLESHEET)
        self.setWindowIcon(ArtGenerator.draw_icon())

        # 1. 把背景特效放在最底层
        self.bg_effect = DynamicBackground(self)
        self.bg_effect.setGeometry(0, 0, 1100, 750)
        self.bg_effect.lower()

        # 变量初始化
        self.playlist = []
        self.current_index = -1
        self.play_mode = 0 
        self.lyrics_map = {}
        self.lyrics_times = []
        
        # 制作模式变量
        self.is_maker_active = False
        self.maker_raw_lines = []
        self.playable_indices = []
        self.maker_step = 0
        self.maker_timestamps = []

        # 媒体播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)
        self.player.positionChanged.connect(self.update_ui_progress)
        self.player.mediaStatusChanged.connect(self.handle_media_status)

        self.init_ui()

    def resizeEvent(self, event):
        # 窗口大小改变时，背景特效层也要跟着变
        self.bg_effect.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        root = QVBoxLayout(main_widget)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        content = QHBoxLayout()
        
        # --- 左侧边栏 ---
        sidebar = QWidget()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background: rgba(20,20,20,0.5); border-right: 1px solid #333;")
        sv = QVBoxLayout(sidebar)
        
        sv.addWidget(QLabel("🎵 音乐库", styleSheet="color:white; font-size:20px; font-weight:bold;"))
        
        # 导入按钮
        b1 = QPushButton("📂 导入文件夹"); b1.clicked.connect(self.select_folder)
        b2 = QPushButton("➕ 添加单曲"); b2.clicked.connect(self.select_files)
        sv.addWidget(b1); sv.addWidget(b2)
        
        self.track_list = QListWidget()
        self.track_list.doubleClicked.connect(self.play_selected)
        sv.addWidget(self.track_list)
        
        # 模式切换按钮
        self.btn_mode = QPushButton("🛠️ 切换到歌词工坊")
        self.btn_mode.clicked.connect(self.toggle_view)
        sv.addWidget(self.btn_mode)

        # --- 右侧多页面 (播放/制作) ---
        self.stack = QStackedWidget()
        
        # 页面1: 正常播放界面
        page_play = QWidget()
        ph = QHBoxLayout(page_play)
        ph.setContentsMargins(50,50,50,50)
        
        # 封面
        self.lbl_cover = QLabel()
        self.lbl_cover.setFixedSize(350, 350)
        self.lbl_cover.setScaledContents(True)
        self.lbl_cover.setPixmap(ArtGenerator.draw_default_cover(350))
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(50); eff.setColor(QColor(0,229,255,60))
        self.lbl_cover.setGraphicsEffect(eff)
        
        # 歌词显示
        lbox = QVBoxLayout()
        self.lbl_lrc_pre = QLabel("")
        self.lbl_lrc_cur = QLabel("MUSE PLAYER")
        self.lbl_lrc_next = QLabel("")
        
        self.lbl_lrc_pre.setStyleSheet("color:#888; font-size:16px;")
        self.lbl_lrc_cur.setStyleSheet(f"color:{ACCENT_HEX}; font-size:34px; font-weight:900;")
        self.lbl_lrc_next.setStyleSheet("color:#888; font-size:16px;")
        
        for l in [self.lbl_lrc_pre, self.lbl_lrc_cur, self.lbl_lrc_next]:
            l.setAlignment(Qt.AlignmentFlag.AlignCenter); l.setWordWrap(True)
            
        lbox.addStretch(); lbox.addWidget(self.lbl_lrc_pre); lbox.addSpacing(20)
        lbox.addWidget(self.lbl_lrc_cur); lbox.addSpacing(20)
        lbox.addWidget(self.lbl_lrc_next); lbox.addStretch()
        
        ph.addWidget(self.lbl_cover); ph.addLayout(lbox)

        # 页面2: 歌词制作界面 (智能版)
        page_maker = QWidget()
        mv = QVBoxLayout(page_maker)
        mv.setContentsMargins(50,20,50,20)
        
        mv.addWidget(QLabel("🎹 智能歌词制作模式 (集成)", styleSheet="font-size:22px; font-weight:bold; color:white;"))
        
        self.txt_maker = QTextEdit()
        self.txt_maker.setPlaceholderText("在此粘贴歌词...\n会自动识别忽略 [Verse]、书名号《》、分隔线。\n录制时，列表会自动滚动跟随。")
        self.txt_maker.setAcceptRichText(True) # 开启富文本，用于高亮
        
        self.lbl_hint = QLabel("准备就绪")
        self.lbl_hint.setStyleSheet(f"color:{ACCENT_HEX}; font-size:16px; font-weight:bold;")
        
        mh = QHBoxLayout()
        # 录制按钮
        self.btn_rec = QPushButton("🎙️ 开始录制 (自动播放)")
        self.btn_rec.setObjectName("ActionBtn")
        self.btn_rec.setCheckable(True)
        self.btn_rec.clicked.connect(self.toggle_record)
        
        self.btn_save = QPushButton("💾 保存歌词")
        self.btn_save.clicked.connect(self.save_lrc)
        
        mh.addWidget(self.btn_rec); mh.addWidget(self.btn_save)
        mv.addWidget(self.txt_maker); mv.addWidget(self.lbl_hint); mv.addLayout(mh)

        self.stack.addWidget(page_play); self.stack.addWidget(page_maker)
        content.addWidget(sidebar); content.addWidget(self.stack)

        # --- 底部控制条 ---
        bot = QFrame(); bot.setObjectName("BottomBar"); bot.setFixedHeight(90)
        bh = QHBoxLayout(bot)
        
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(50,50)
        self.btn_play.setStyleSheet("border-radius:25px; background:white; color:black; font-size:24px;")
        self.btn_play.clicked.connect(self.toggle_play)
        
        bp = QPushButton("⏮"); bn = QPushButton("⏭")
        bp.clicked.connect(self.prev_song); bn.clicked.connect(self.next_song)
        
        self.lbl_t = QLabel("00:00 / 00:00", styleSheet="color:#AAA")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.combo = QComboBox(); self.combo.addItems(["🔁", "🔂", "🔀"]); self.combo.setFixedWidth(60)
        self.combo.currentIndexChanged.connect(lambda i: setattr(self, 'play_mode', i))
        
        bh.addWidget(bp); bh.addSpacing(10); bh.addWidget(self.btn_play); bh.addSpacing(10); bh.addWidget(bn)
        bh.addSpacing(20)
        v = QVBoxLayout(); v.addWidget(self.lbl_t, 0, Qt.AlignmentFlag.AlignRight); v.addWidget(self.slider)
        bh.addLayout(v); bh.addWidget(self.combo)

        root.addLayout(content); root.addWidget(bot)

    # --- 音乐管理功能 ---
    def select_folder(self):
        d = QFileDialog.getExistingDirectory(self, "选择目录")
        if d:
            self.playlist = []
            self.track_list.clear()
            for f in os.listdir(d):
                if f.lower().endswith(SUPPORTED_FORMATS):
                    self.playlist.append(os.path.join(d, f))
                    self.track_list.addItem(os.path.splitext(f)[0])
            if self.playlist: self.current_index=0; self.play_music(self.playlist[0])

    def select_files(self):
        fs, _ = QFileDialog.getOpenFileNames(self, "添加文件", "", "Audio (*.mp3 *.flac *.wav *.m4a *.ogg *.wma)")
        if fs:
            self.playlist.extend(fs)
            for f in fs: self.track_list.addItem(os.path.splitext(os.path.basename(f))[0])
            if self.current_index==-1: self.current_index=0; self.play_music(self.playlist[0])

    def play_selected(self):
        idx = self.track_list.currentRow()
        if idx!=-1: self.current_index=idx; self.play_music(self.playlist[idx])

    def play_music(self, path):
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.btn_play.setText("⏸")
        
        # 查找封面
        d = os.path.dirname(path)
        found = False
        for n in ['cover.jpg','cover.png','folder.jpg']:
            p = os.path.join(d,n)
            if os.path.exists(p): self.lbl_cover.setPixmap(QPixmap(p)); found=True; break
        if not found: self.lbl_cover.setPixmap(ArtGenerator.draw_default_cover(350))
        
        self.load_lrc_view(path)
        # 如果正在录制模式，切歌时自动停止录制，避免混乱
        if self.is_maker_active: self.toggle_record()

    def toggle_play(self):
        if self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause(); self.btn_play.setText("▶")
        else: self.player.play(); self.btn_play.setText("⏸")

    # --- 歌词显示逻辑 (播放模式下) ---
    def load_lrc_view(self, path):
        p = os.path.splitext(path)[0]+".lrc"
        self.lyrics_map={}; self.lyrics_times=[]
        self.lbl_lrc_cur.setText("暂无歌词"); self.lbl_lrc_pre.clear(); self.lbl_lrc_next.clear()
        if os.path.exists(p):
            try:
                with open(p,'r',encoding='utf-8',errors='ignore') as f:
                    for l in f:
                        if "]" in l:
                            t,x = l.split("]",1); m,s = t.strip("[").split(":")
                            ms = int(int(m)*60000+float(s)*1000)
                            self.lyrics_map[ms]=x.strip(); self.lyrics_times.append(ms)
                self.lyrics_times.sort()
                self.lbl_lrc_cur.setText("歌词加载成功")
            except: pass

    def update_ui_progress(self, pos):
        self.slider.setValue(pos); self.slider.setMaximum(self.player.duration())
        m,s = divmod(pos//1000,60); dm,ds = divmod(self.player.duration()//1000,60)
        self.lbl_t.setText(f"{m:02}:{s:02} / {dm:02}:{ds:02}")
        
        # 仅在非制作模式下更新主界面的歌词
        if not self.is_maker_active and self.lyrics_times:
            ts = [t for t in self.lyrics_times if t<=pos]
            if ts:
                cur = ts[-1]; idx = self.lyrics_times.index(cur)
                self.lbl_lrc_cur.setText(self.lyrics_map[cur])
                self.lbl_lrc_pre.setText(self.lyrics_map[self.lyrics_times[idx-1]] if idx>0 else "")
                self.lbl_lrc_next.setText(self.lyrics_map[self.lyrics_times[idx+1]] if idx<len(self.lyrics_times)-1 else "")

    # --- 核心：集成版智能歌词工坊 ---
    def toggle_view(self):
        # 切换界面 (Stack 0: 播放, Stack 1: 制作)
        if self.stack.currentIndex()==0: 
            self.stack.setCurrentIndex(1); self.btn_mode.setText("🎵 返回播放界面")
        else: 
            self.stack.setCurrentIndex(0); self.btn_mode.setText("🛠️ 切换到歌词工坊")

    def is_skippable(self, line):
        """ 智能识别：忽略标签行、空行、分割线 """
        line = line.strip()
        if not line: return True 
        if line.startswith("[") and line.endswith("]"): return True 
        if line.startswith("《") and line.endswith("》"): return True 
        if re.match(r'^[-—]+$', line): return True 
        if line.startswith("作词") or line.startswith("作曲"): return True
        return False

    def toggle_record(self):
        if self.btn_rec.isChecked():
            # 1. 读取并解析
            raw = self.txt_maker.toPlainText().strip()
            if not raw: self.btn_rec.setChecked(False); QMessageBox.warning(self,"提示","请粘贴文本"); return
            
            self.maker_raw_lines = raw.split('\n')
            self.playable_indices = []
            # 筛选出真正需要打点的行
            for i, line in enumerate(self.maker_raw_lines):
                if not self.is_skippable(line):
                    self.playable_indices.append(i)
            
            if not self.playable_indices:
                self.btn_rec.setChecked(False)
                QMessageBox.warning(self, "错误", "未识别到有效歌词，请检查格式。")
                return

            self.maker_timestamps = []
            self.maker_step = 0 
            self.is_maker_active = True
            self.txt_maker.setReadOnly(True) # 录制时禁止修改文本
            
            # 2. 自动播放
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self.player.play()
                self.btn_play.setText("⏸")
            
            self.btn_rec.setText("⏹ 停止录制")
            self.render_maker_html() # 初始渲染
            self.setFocus() # 确保键盘事件被主窗口捕获
        else:
            # 停止
            self.is_maker_active = False
            self.txt_maker.setReadOnly(False)
            self.btn_rec.setText("🎙️ 开始录制 (自动播放)")
            self.lbl_hint.setText("录制结束")
            # 恢复原始文本，去掉HTML标签，方便用户再次编辑
            self.txt_maker.setPlainText("\n".join(self.maker_raw_lines))

    def render_maker_html(self):
        """ 高亮显示 + 自动滚动逻辑 """
        html = "<body style='font-family:Segoe UI; font-size:16px; line-height:160%; color:#888;'>"
        
        target_idx = -1 # 需要滚动到的目标行
        if self.maker_step < len(self.playable_indices):
            target_idx = self.playable_indices[self.maker_step]
            
        for i, line in enumerate(self.maker_raw_lines):
            content = line.strip()
            if not content: content = "&nbsp;"
            
            style = ""
            prefix = ""
            
            if self.is_skippable(line):
                # 忽略行：灰色斜体
                style = "color:#555; font-style:italic; font-size:14px;"
            elif i in self.playable_indices:
                p_idx = self.playable_indices.index(i)
                if p_idx < self.maker_step:
                    # 已录完：绿色删除线
                    style = "color:#00AA88; text-decoration:line-through;"
                    prefix = "✅ "
                elif p_idx == self.maker_step:
                    # 当前行：高亮 + 背景光
                    style = f"color:{ACCENT_HEX}; font-size:22px; font-weight:bold; background-color:rgba(0,229,255,0.15);"
                    prefix = "👉 "
                else:
                    # 未录：白色
                    style = "color:#DDD;"
            
            html += f"<div style='{style}'>{prefix}{content}</div>"
        
        html += "</body>"
        self.txt_maker.setHtml(html)
        
        # --- 自动滚动 ---
        if target_idx != -1:
            cursor = self.txt_maker.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock, n=target_idx)
            self.txt_maker.setTextCursor(cursor)
            self.txt_maker.ensureCursorVisible() # 强制滚动到可见区域
            
            self.lbl_hint.setText(f"正在录制: {self.maker_raw_lines[target_idx]}")
        elif self.maker_step >= len(self.playable_indices):
            self.lbl_hint.setText("🎉 录制完成！请点击保存。")

    def keyPressEvent(self, event):
        # 只有在录制模式下，才接管空格键
        if self.is_maker_active and event.key() == Qt.Key.Key_Space:
            if self.maker_step < len(self.playable_indices):
                # 记录当前时间点
                self.maker_timestamps.append(self.player.position())
                self.maker_step += 1
                self.render_maker_html() # 刷新界面
            else:
                self.toggle_record() # 结束
        else:
            super().keyPressEvent(event)

    def save_lrc(self):
        if not self.playlist: return
        p = os.path.splitext(self.playlist[self.current_index])[0]+".lrc"
        try:
            with open(p,'w',encoding='utf-8') as f:
                count = min(len(self.maker_timestamps), len(self.playable_indices))
                for i in range(count):
                    ms = self.maker_timestamps[i]
                    line_idx = self.playable_indices[i]
                    text = self.maker_raw_lines[line_idx]
                    f.write(f"[{ms//60000:02}:{(ms%60000)/1000:05.2f}]{text}\n")
            QMessageBox.information(self,"成功",f"已保存至: {p}"); self.load_lrc_view(self.playlist[self.current_index])
        except Exception as e: QMessageBox.warning(self,"错误",str(e))

    def handle_media_status(self, s):
        if s==QMediaPlayer.MediaStatus.EndOfMedia: self.next_song()
    def next_song(self): self.skip(1)
    def prev_song(self): self.skip(-1)
    def skip(self,d):
        if not self.playlist: return
        if self.play_mode==2: self.current_index=random.randint(0,len(self.playlist)-1)
        else: self.current_index=(self.current_index+d)%len(self.playlist)
        self.track_list.setCurrentRow(self.current_index); self.play_music(self.playlist[self.current_index])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ModernPlayer()
    win.show()
    sys.exit(app.exec())
