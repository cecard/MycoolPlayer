# --- 崩溃记录器 (放在最开头) ---
import sys
import traceback
import os

def exception_hook(exctype, value, tb):
    # 如果崩溃，将错误信息写入文件
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    with open("crash_log.txt", "w", encoding='utf-8') as f:
        f.write(error_msg)
    print(error_msg)
    # 阻塞程序，防止窗口立刻消失
    input("程序崩溃！请查看上方报错信息，或查看 crash_log.txt。按回车键退出...")
    sys.exit(1)

sys.excepthook = exception_hook
# ---------------------------

import random
import math
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QSlider, QStackedWidget, QTextEdit, 
                             QMessageBox, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QUrl, QPoint, QTimer, QPropertyAnimation, pyqtProperty, QRectF, QEasingCurve, QSize
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import (QIcon, QPixmap, QPainter, QColor, QPen, QFont, 
                         QBrush, QLinearGradient, QTextCursor, QTransform, QPainterPath)

# --- 全局配置 ---
SUPPORTED_FORMATS = (
    '.mp3', '.flac', '.wav', '.ogg', '.m4a', '.wma', 
    '.aac', '.ape', '.opus', '.alac', '.aiff', '.mp2'
)
ACCENT_COLOR = QColor(0, 255, 213) # 赛博朋克青
ACCENT_HEX = "#00FFD5"

# --- 1. 动态背景 ---
class DynamicBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_anim)
        self.timer.start(30)
        self.offset = 0
        for _ in range(50):
            self.particles.append({
                'x': random.random(), 'y': random.random(),
                'vx': (random.random()-0.5)*0.002, 'vy': (random.random()-0.5)*0.002,
                'size': random.randint(2, 5), 'alpha': random.randint(20, 100)
            })

    def update_anim(self):
        self.offset += 0.002
        if self.offset > 1: self.offset = 0
        for p in self.particles:
            p['x'] += p['vx']; p['y'] += p['vy']
            if p['x']<0 or p['x']>1: p['vx']*=-1
            if p['y']<0 or p['y']>1: p['vy']*=-1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, QColor(10, 10, 15))
        grad.setColorAt(0.5, QColor(15, 15, 20))
        grad.setColorAt(1, QColor(5, 5, 10))
        painter.fillRect(0, 0, w, h, grad)
        painter.setPen(Qt.PenStyle.NoPen)
        for p in self.particles:
            c = QColor(ACCENT_COLOR); c.setAlpha(p['alpha'])
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPoint(int(p['x']*w), int(p['y']*h)), p['size'], p['size'])

# --- 2. 旋转黑胶唱片组件 ---
class VinylRecord(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 320)
        self.angle = 0
        self.is_playing = False
        self.cover_pixmap = None
        self.default_pixmap = self.generate_default_cover()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(20) 

    def set_cover(self, pixmap):
        self.cover_pixmap = pixmap
        self.update()

    def play(self): self.is_playing = True
    def pause(self): self.is_playing = False

    def rotate(self):
        if self.is_playing:
            self.angle = (self.angle + 0.5) % 360
            self.update()

    def generate_default_cover(self):
        pix = QPixmap(300, 300)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(20, 20, 20)))
        p.drawEllipse(0, 0, 300, 300)
        p.end()
        return pix

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        center = QPoint(w//2, h//2)
        painter.translate(center); painter.rotate(self.angle); painter.translate(-center)
        
        radius = min(w, h) // 2 - 10
        painter.setBrush(QBrush(QColor(15, 15, 15)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius, radius)
        
        pen = QPen(QColor(40, 40, 40)); pen.setWidth(1)
        painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
        for r in range(radius - 10, radius - 80, -3): painter.drawEllipse(center, r, r)
            
        inner_radius = radius - 55
        path = QPainterPath(); path.addEllipse(QPoint(w//2, h//2), inner_radius, inner_radius)
        painter.setClipPath(path)
        
        img_to_draw = self.cover_pixmap if self.cover_pixmap else self.default_pixmap
        if img_to_draw:
            scaled = img_to_draw.scaled(inner_radius*2, inner_radius*2, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(w//2 - scaled.width()//2, h//2 - scaled.height()//2, scaled)
            
        painter.setClipping(False)
        painter.setBrush(QBrush(QColor(0, 0, 0))); painter.drawEllipse(center, 5, 5)
        
        painter.resetTransform(); painter.translate(center)
        grad = QLinearGradient(-radius, -radius, radius, radius)
        grad.setColorAt(0, QColor(255, 255, 255, 20))
        grad.setColorAt(0.5, QColor(255, 255, 255, 0))
        grad.setColorAt(1, QColor(255, 255, 255, 10))
        painter.setBrush(QBrush(grad)); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(0,0), radius, radius)

# --- 3. 呼吸灯按钮 ---
class BreathingButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(0); self.shadow.setColor(ACCENT_COLOR); self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
        self.anim = QPropertyAnimation(self, b"glowRadius")
        self.anim.setDuration(1500); self.anim.setStartValue(0); self.anim.setEndValue(30)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutSine); self.anim.setLoopCount(-1)

    @pyqtProperty(int)
    def glowRadius(self): return self.shadow.blurRadius()
    @glowRadius.setter
    def glowRadius(self, radius): self.shadow.setBlurRadius(radius)

    def start_breathing(self): self.anim.start()
    def stop_breathing(self): self.anim.stop(); self.shadow.setBlurRadius(0)

# --- 主样式表 ---
STYLESHEET = f"""
QMainWindow {{ background-color: #121212; }}
QWidget {{ font-family: "Microsoft YaHei UI", sans-serif; background: transparent; }}
QListWidget {{ 
    background-color: rgba(20, 20, 20, 0.6); border-radius: 10px;
    color: #AAA; font-size: 13px; padding: 5px; border: 1px solid #333;
}}
QListWidget::item {{ height: 40px; border-radius: 5px; padding-left: 10px; margin-bottom: 2px; }}
QListWidget::item:selected {{ background-color: rgba(0, 255, 213, 0.1); color: {ACCENT_HEX}; border: 1px solid {ACCENT_HEX}; }}
QListWidget::item:hover {{ background-color: rgba(255, 255, 255, 0.05); }}
QPushButton {{
    background-color: rgba(40, 40, 40, 0.5); color: #EEE; border-radius: 5px; border: 1px solid #444; padding: 8px;
}}
QPushButton:hover {{ background-color: rgba(60, 60, 60, 0.8); border-color: #666; }}
QPushButton:pressed {{ background-color: {ACCENT_HEX}; color: #000; }}
QPushButton#BreathingBtn {{
    background-color: transparent; border: 2px solid {ACCENT_HEX}; color: {ACCENT_HEX}; 
    font-weight: bold; font-size: 16px; border-radius: 25px;
}}
QPushButton#BreathingBtn:hover {{ background-color: rgba(0, 255, 213, 0.1); }}
QPushButton#BreathingBtn:checked {{ background-color: {ACCENT_HEX}; color: #000; }}
QFrame#BottomBar {{ 
    background-color: rgba(18, 18, 18, 0.95); border-top: 1px solid #333; 
    border-top-left-radius: 20px; border-top-right-radius: 20px;
}}
QSlider::groove:horizontal {{ height: 4px; background: #333; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT_HEX}; border-radius: 2px; }}
QSlider::handle:horizontal {{ 
    background: #FFF; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; 
    border: 2px solid {ACCENT_HEX};
}}
QTextEdit {{
    background-color: rgba(0,0,0,0.3); border: 1px solid #333; color: #DDD; padding: 15px; 
    font-size: 16px; border-radius: 10px;
}}
"""

class ModernPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MusePlayer Elite")
        self.resize(1150, 780)
        self.setStyleSheet(STYLESHEET)
        
        self.bg_effect = DynamicBackground(self)
        self.bg_effect.setGeometry(0, 0, 1150, 780)
        self.bg_effect.lower()

        self.playlist = []
        self.current_index = -1
        self.play_mode = 0 
        self.lyrics_map = {}
        self.lyrics_times = []
        
        self.is_maker_active = False
        self.maker_raw_lines = []
        self.playable_indices = []
        self.maker_step = 0
        self.maker_timestamps = []

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)
        self.player.positionChanged.connect(self.update_ui_progress)
        self.player.mediaStatusChanged.connect(self.handle_media_status)

        self.init_ui()

    def resizeEvent(self, event):
        self.bg_effect.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        root = QVBoxLayout(main_widget)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        content = QHBoxLayout()
        content.setContentsMargins(20, 20, 20, 0)
        
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("background-color: rgba(30,30,30,0.4); border-radius: 15px;")
        sv = QVBoxLayout(sidebar)
        sv.setContentsMargins(15, 20, 15, 20)
        
        sv.addWidget(QLabel("🎵 播放列表", styleSheet=f"color:{ACCENT_HEX}; font-size:18px; font-weight:bold;"))
        
        btn_folder = QPushButton("📂 导入文件夹"); btn_folder.clicked.connect(self.select_folder)
        btn_files = QPushButton("➕ 添加文件"); btn_files.clicked.connect(self.select_files)
        sv.addWidget(btn_folder); sv.addWidget(btn_files)
        
        self.track_list = QListWidget()
        self.track_list.doubleClicked.connect(self.play_selected)
        sv.addWidget(self.track_list)
        
        self.btn_switch_mode = QPushButton("🛠️ 进入歌词工坊")
        self.btn_switch_mode.clicked.connect(self.toggle_view)
        sv.addWidget(self.btn_switch_mode)

        self.stack = QStackedWidget()
        
        # Play Page
        page_play = QWidget()
        ph = QHBoxLayout(page_play)
        ph.setSpacing(40)
        
        self.vinyl = VinylRecord()
        vinyl_container = QVBoxLayout()
        vinyl_container.addStretch(); vinyl_container.addWidget(self.vinyl, 0, Qt.AlignmentFlag.AlignCenter); vinyl_container.addStretch()
        
        lrc_container = QVBoxLayout()
        self.lbl_lrc_pre = QLabel("")
        self.lbl_lrc_cur = QLabel("MUSE PLAYER")
        self.lbl_lrc_next = QLabel("")
        
        self.lbl_lrc_pre.setStyleSheet("color:#666; font-size:16px;")
        self.lbl_lrc_cur.setStyleSheet(f"color:{ACCENT_HEX}; font-size:32px; font-weight:900; text-shadow: 0px 0px 10px {ACCENT_HEX};")
        self.lbl_lrc_next.setStyleSheet("color:#666; font-size:16px;")
        
        for l in [self.lbl_lrc_pre, self.lbl_lrc_cur, self.lbl_lrc_next]:
            l.setAlignment(Qt.AlignmentFlag.AlignCenter); l.setWordWrap(True)
            
        lrc_container.addStretch()
        lrc_container.addWidget(self.lbl_lrc_pre); lrc_container.addSpacing(25)
        lrc_container.addWidget(self.lbl_lrc_cur); lrc_container.addSpacing(25)
        lrc_container.addWidget(self.lbl_lrc_next); lrc_container.addStretch()
        
        ph.addLayout(vinyl_container, 4); ph.addLayout(lrc_container, 6)

        # Maker Page
        page_maker = QWidget()
        mv = QVBoxLayout(page_maker)
        mv.setContentsMargins(50, 20, 50, 20)
        
        mv.addWidget(QLabel("🎹 智能歌词制作模式", styleSheet="font-size:24px; font-weight:bold; color:white;"))
        
        self.txt_maker = QTextEdit()
        self.txt_maker.setPlaceholderText("粘贴歌词到这里... 系统会自动过滤无关信息。")
        self.txt_maker.setAcceptRichText(True)
        
        self.lbl_maker_hint = QLabel("准备就绪")
        self.lbl_maker_hint.setStyleSheet(f"color:{ACCENT_HEX}; font-size:18px;")
        
        mh = QHBoxLayout()
        self.btn_rec = BreathingButton("🎙️ 开始录制")
        self.btn_rec.setObjectName("BreathingBtn")
        self.btn_rec.setFixedSize(180, 50)
        self.btn_rec.setCheckable(True)
        self.btn_rec.clicked.connect(self.toggle_record)
        
        btn_save = QPushButton("💾 保存歌词")
        btn_save.setFixedSize(120, 50)
        btn_save.clicked.connect(self.save_lrc)
        
        mh.addWidget(self.btn_rec); mh.addWidget(btn_save); mh.addStretch()
        mv.addWidget(self.txt_maker); mv.addWidget(self.lbl_maker_hint); mv.addLayout(mh)

        self.stack.addWidget(page_play); self.stack.addWidget(page_maker)
        content.addWidget(sidebar); content.addWidget(self.stack)

        # Bottom Bar
        bottom_bar = QFrame(); bottom_bar.setObjectName("BottomBar")
        bottom_bar.setFixedHeight(100)
        bh = QHBoxLayout(bottom_bar)
        bh.setContentsMargins(30, 10, 30, 10)

        self.btn_mode = QPushButton()
        self.btn_mode.setFixedSize(110, 40)
        self.btn_mode.setStyleSheet(f"""
            QPushButton {{ background-color: #333; border: 1px solid #555; border-radius: 20px; color: #DDD; font-size: 13px; }}
            QPushButton:hover {{ background-color: #444; border-color: {ACCENT_HEX}; color: white; }}
        """)
        self.btn_mode.clicked.connect(self.toggle_play_mode)
        self.update_mode_btn() 

        ctrl_layout = QHBoxLayout()
        btn_prev = QPushButton("⏮"); btn_prev.setFixedSize(40,40); btn_prev.clicked.connect(self.prev_song)
        
        self.btn_play = BreathingButton("▶")
        self.btn_play.setObjectName("BreathingBtn")
        self.btn_play.setFixedSize(60, 60)
        self.btn_play.setStyleSheet(f"border-radius: 30px; border: 2px solid {ACCENT_HEX}; color: {ACCENT_HEX}; font-size: 24px;")
        self.btn_play.clicked.connect(self.toggle_play)
        
        btn_next = QPushButton("⏭"); btn_next.setFixedSize(40,40); btn_next.clicked.connect(self.next_song)
        
        ctrl_layout.addWidget(btn_prev); ctrl_layout.addSpacing(15)
        ctrl_layout.addWidget(self.btn_play); ctrl_layout.addSpacing(15)
        ctrl_layout.addWidget(btn_next)

        prog_layout = QVBoxLayout()
        self.lbl_time = QLabel("00:00 / 00:00", styleSheet="color: #888; font-size: 12px;")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.sliderMoved.connect(self.player.setPosition)
        prog_layout.addWidget(self.lbl_time, 0, Qt.AlignmentFlag.AlignRight)
        prog_layout.addWidget(self.slider)

        bh.addWidget(self.btn_mode); bh.addStretch()
        bh.addLayout(ctrl_layout); bh.addStretch()
        bh.addLayout(prog_layout); bh.setStretch(4, 1)

        root.addLayout(content); root.addWidget(bottom_bar)

    # --- Logic ---
    def toggle_play_mode(self):
        self.play_mode = (self.play_mode + 1) % 3
        self.update_mode_btn()

    def update_mode_btn(self):
        modes = [("🔁 列表循环", "按顺序播放"), ("🔂 单曲循环", "重复当前"), ("🔀 随机播放", "随机选择")]
        t, tip = modes[self.play_mode]
        self.btn_mode.setText(t); self.btn_mode.setToolTip(tip)

    def select_folder(self):
        d = QFileDialog.getExistingDirectory(self, "选择目录")
        if d:
            self.playlist = []; self.track_list.clear()
            for f in os.listdir(d):
                if f.lower().endswith(SUPPORTED_FORMATS):
                    self.playlist.append(os.path.join(d, f)); self.track_list.addItem(os.path.splitext(f)[0])
            if self.playlist: self.current_index=0; self.play_music(self.playlist[0])

    def select_files(self):
        fs, _ = QFileDialog.getOpenFileNames(self, "添加文件", "", "Audio (*.mp3 *.flac *.wav *.m4a *.ogg)")
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
        self.btn_play.setText("⏸"); self.btn_play.start_breathing(); self.vinyl.play()
        d = os.path.dirname(path); found = False
        for n in ['cover.jpg','cover.png','folder.jpg','folder.png']:
            p = os.path.join(d,n)
            if os.path.exists(p): self.vinyl.set_cover(QPixmap(p)); found=True; break
        if not found: self.vinyl.set_cover(None)
        self.load_lrc_view(path)
        if self.is_maker_active: self.toggle_record()

    def toggle_play(self):
        if self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause(); self.btn_play.setText("▶"); self.btn_play.stop_breathing(); self.vinyl.pause()
        else:
            self.player.play(); self.btn_play.setText("⏸"); self.btn_play.start_breathing(); self.vinyl.play()

    def load_lrc_view(self, path):
        p = os.path.splitext(path)[0]+".lrc"
        self.lyrics_map={}; self.lyrics_times=[]
        self.lbl_lrc_cur.setText("暂无歌词"); self.lbl_lrc_pre.clear(); self.lbl_lrc_next.clear()
        if os.path.exists(p):
            try:
                with open(p,'r',encoding='utf-8',errors='ignore') as f:
                    for l in f:
                        if "]" in l:
                            t,x = l.split("]",1); m,s = t.strip("[").split(":"); ms = int(int(m)*60000+float(s)*1000)
                            self.lyrics_map[ms]=x.strip(); self.lyrics_times.append(ms)
                self.lyrics_times.sort(); self.lbl_lrc_cur.setText("歌词已加载")
            except: pass

    def update_ui_progress(self, pos):
        self.slider.setValue(pos); self.slider.setMaximum(self.player.duration())
        m,s = divmod(pos//1000,60); dm,ds = divmod(self.player.duration()//1000,60)
        self.lbl_time.setText(f"{m:02}:{s:02} / {dm:02}:{ds:02}")
        if not self.is_maker_active and self.lyrics_times:
            ts = [t for t in self.lyrics_times if t<=pos]
            if ts:
                cur = ts[-1]; idx = self.lyrics_times.index(cur)
                self.lbl_lrc_cur.setText(self.lyrics_map[cur])
                self.lbl_lrc_pre.setText(self.lyrics_map[self.lyrics_times[idx-1]] if idx>0 else "")
                self.lbl_lrc_next.setText(self.lyrics_map[self.lyrics_times[idx+1]] if idx<len(self.lyrics_times)-1 else "")

    def toggle_view(self):
        if self.stack.currentIndex()==0: self.stack.setCurrentIndex(1); self.btn_switch_mode.setText("🎵 返回播放")
        else: self.stack.setCurrentIndex(0); self.btn_switch_mode.setText("🛠️ 进入制作")

    def is_skippable(self, line):
        line = line.strip()
        if not line or (line.startswith("[") and line.endswith("]")) or (line.startswith("《") and line.endswith("》")) or re.match(r'^[-—]+$', line) or line.startswith("作词") or line.startswith("作曲"): return True
        return False

    def toggle_record(self):
        if self.btn_rec.isChecked():
            raw = self.txt_maker.toPlainText().strip()
            if not raw: self.btn_rec.setChecked(False); QMessageBox.warning(self,"提示","请先粘贴歌词"); return
            self.maker_raw_lines = raw.split('\n'); self.playable_indices = []
            for i, l in enumerate(self.maker_raw_lines):
                if not self.is_skippable(l): self.playable_indices.append(i)
            if not self.playable_indices: self.btn_rec.setChecked(False); return
            self.maker_timestamps = []; self.maker_step = 0; self.is_maker_active = True; self.txt_maker.setReadOnly(True)
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self.player.play(); self.btn_play.setText("⏸"); self.btn_play.start_breathing(); self.vinyl.play()
            self.btn_rec.setText("⏹ 停止录制"); self.btn_rec.start_breathing(); self.render_maker_html(); self.setFocus()
        else:
            self.is_maker_active = False; self.txt_maker.setReadOnly(False); self.btn_rec.setText("🎙️ 开始录制"); self.btn_rec.stop_breathing()
            self.lbl_maker_hint.setText("录制结束"); self.txt_maker.setPlainText("\n".join(self.maker_raw_lines))

    def render_maker_html(self):
        html = "<body style='font-family:Microsoft YaHei; font-size:16px; line-height:160%; color:#888;'>"
        t_idx = -1
        if self.maker_step < len(self.playable_indices): t_idx = self.playable_indices[self.maker_step]
        for i, l in enumerate(self.maker_raw_lines):
            c = l.strip() if l.strip() else "&nbsp;"
            style = ""; prefix = ""
            if self.is_skippable(l): style = "color:#555; font-style:italic; font-size:14px;"
            elif i in self.playable_indices:
                p = self.playable_indices.index(i)
                if p < self.maker_step: style = "color:#00AA88; text-decoration:line-through;"; prefix="✅ "
                elif p == self.maker_step: style = f"color:{ACCENT_HEX}; font-size:22px; font-weight:bold; background-color:rgba(0,255,213,0.15);"; prefix="👉 "
                else: style = "color:#DDD;"
            html += f"<div style='{style}'>{prefix}{c}</div>"
        html += "</body>"
        self.txt_maker.setHtml(html)
        if t_idx != -1:
            cursor = self.txt_maker.textCursor(); cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock, n=t_idx)
            self.txt_maker.setTextCursor(cursor); self.txt_maker.ensureCursorVisible()
            self.lbl_maker_hint.setText(f"录制中: {self.maker_raw_lines[t_idx]}")
        elif self.maker_step >= len(self.playable_indices): self.lbl_maker_hint.setText("录制完成！请保存。")

    def keyPressEvent(self, event):
        if self.is_maker_active and event.key() == Qt.Key.Key_Space:
            if self.maker_step < len(self.playable_indices):
                self.maker_timestamps.append(self.player.position()); self.maker_step += 1; self.render_maker_html()
            else: self.toggle_record()
        else: super().keyPressEvent(event)

    def save_lrc(self):
        if not self.playlist: return
        p = os.path.splitext(self.playlist[self.current_index])[0]+".lrc"
        try:
            with open(p,'w',encoding='utf-8') as f:
                for i in range(min(len(self.maker_timestamps), len(self.playable_indices))):
                    f.write(f"[{self.maker_timestamps[i]//60000:02}:{(self.maker_timestamps[i]%60000)/1000:05.2f}]{self.maker_raw_lines[self.playable_indices[i]]}\n")
            QMessageBox.information(self,"成功",f"已保存: {p}"); self.load_lrc_view(self.playlist[self.current_index])
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
    try:
        app = QApplication(sys.argv)
        win = ModernPlayer()
        win.show()
        sys.exit(app.exec())
    except Exception as e:
        with open("crash_log.txt", "w", encoding='utf-8') as f:
            import traceback
            traceback.print_exc(file=f)
