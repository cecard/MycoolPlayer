import sys
import os
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QSlider, QStackedWidget, QTextEdit, 
                             QMessageBox, QComboBox, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QUrl, QSize, QPoint, QRect
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QFont, QBrush, QLinearGradient

# --- 全局配色与样式 ---
ACCENT_COLOR = "#00E5FF"  # 霓虹蓝
BG_DARK = "#121212"       # 极深灰
BG_SIDE = "#1E1E1E"       # 侧边栏灰
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY = "#888888"

STYLESHEET = f"""
QMainWindow {{ background-color: {BG_DARK}; }}
QWidget {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }}

/* 侧边栏列表 */
QListWidget {{ 
    background-color: {BG_SIDE}; border: none; outline: none;
    color: #BBBBBB; font-size: 13px; padding: 10px;
}}
QListWidget::item {{ height: 35px; border-radius: 5px; padding-left: 5px; }}
QListWidget::item:selected {{ background-color: #333333; color: {ACCENT_COLOR}; border-left: 3px solid {ACCENT_COLOR}; }}
QListWidget::item:hover {{ background-color: #2A2A2A; }}

/* 按钮通用 */
QPushButton {{
    background-color: transparent; border: none; color: {TEXT_WHITE};
    font-size: 16px; border-radius: 5px;
}}
QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.1); }}

/* 底部控制区 */
QFrame#BottomBar {{ background-color: #252525; border-top: 1px solid #333; }}

/* 进度条 */
QSlider::groove:horizontal {{
    border: none; height: 6px; background: #404040; border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT_COLOR}; border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: #FFFFFF; width: 14px; height: 14px; 
    margin: -4px 0; border-radius: 7px;
}}

/* 文本框 */
QTextEdit {{
    background-color: {BG_SIDE}; border: 1px solid #333; 
    color: #DDD; padding: 10px; border-radius: 8px;
}}

/* 下拉框 */
QComboBox {{
    background-color: {BG_SIDE}; color: #DDD; border: 1px solid #333;
    padding: 5px; border-radius: 4px;
}}
"""

# --- 动态绘制图标与封面的工具类 ---
class ArtGenerator:
    @staticmethod
    def draw_icon(size=64):
        """绘制极简线条风格的软件图标"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制圆形背景
        brush = QBrush(QColor(BG_SIDE))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)
        
        # 绘制霓虹线条音符
        pen = QPen(QColor(ACCENT_COLOR))
        pen.setWidth(int(size/10))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # 简单的音符形状
        w, h = size, size
        painter.drawLine(int(w*0.35), int(h*0.7), int(w*0.35), int(h*0.3)) # 左竖
        painter.drawLine(int(w*0.65), int(h*0.6), int(w*0.65), int(h*0.2)) # 右竖
        painter.drawLine(int(w*0.35), int(h*0.3), int(w*0.65), int(h*0.2)) # 横梁
        painter.drawEllipse(QPoint(int(w*0.35), int(h*0.7)), int(w*0.1), int(w*0.08)) # 左点
        painter.drawEllipse(QPoint(int(w*0.65), int(h*0.6)), int(w*0.1), int(w*0.08)) # 右点
        
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def draw_default_cover(size=300):
        """绘制默认的线条黑胶唱片封面"""
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(BG_DARK))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPoint(size//2, size//2)
        
        # 唱片纹理
        pen = QPen(QColor(30, 30, 30))
        pen.setWidth(2)
        painter.setPen(pen)
        for r in range(40, size//2, 10):
            painter.drawEllipse(center, r, r)
            
        # 中间圆标
        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0, QColor(ACCENT_COLOR))
        grad.setColorAt(1, QColor("#5500AA"))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, 50, 50)
        
        # 音符符号
        painter.setPen(QPen(Qt.GlobalColor.white, 3))
        painter.drawLine(center.x()-10, center.y()+10, center.x()-10, center.y()-10)
        painter.drawLine(center.x()-10, center.y()-10, center.x()+10, center.y()-10)
        painter.drawLine(center.x()+10, center.y()-10, center.x()+10, center.y()+10)
        
        painter.end()
        return pixmap

class ModernPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MusePlayer Pro")
        self.resize(1100, 750)
        self.setStyleSheet(STYLESHEET)
        self.setWindowIcon(ArtGenerator.draw_icon())

        # 核心变量
        self.playlist = []
        self.current_index = -1
        self.play_mode = 0 
        self.lyrics_map = {}
        self.lyrics_times = []
        
        # 制作器变量
        self.is_maker_active = False
        self.maker_lines = []
        self.maker_current_idx = 0
        self.maker_timestamps = []

        # 播放器初始化
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)
        
        self.player.positionChanged.connect(self.update_ui_progress)
        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.grabKeyboard()

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 整体采用垂直布局：上面是内容，下面是控制条
        root_layout = QVBoxLayout(main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- 上半部分：左右分栏 ---
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 1. 左侧侧边栏
        sidebar = QWidget()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(f"background-color: {BG_SIDE};")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(20, 30, 20, 20)

        lbl_library = QLabel("我的音乐库")
        lbl_library.setStyleSheet(f"color: {TEXT_WHITE}; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        
        self.btn_add_folder = QPushButton("  📂  导入文件夹")
        self.btn_add_folder.setStyleSheet(f"text-align: left; background-color: #333; padding: 10px; margin-bottom: 10px;")
        self.btn_add_folder.clicked.connect(self.select_folder)

        self.track_list = QListWidget()
        self.track_list.doubleClicked.connect(self.play_selected)

        self.btn_switch_mode = QPushButton("🛠️ 歌词工坊模式")
        self.btn_switch_mode.setStyleSheet("color: #888; font-size: 12px; margin-top: 10px;")
        self.btn_switch_mode.clicked.connect(self.toggle_main_view)

        side_layout.addWidget(lbl_library)
        side_layout.addWidget(self.btn_add_folder)
        side_layout.addWidget(self.track_list)
        side_layout.addWidget(self.btn_switch_mode)

        # 2. 右侧主视图 (堆叠：播放页 / 制作页)
        self.stack = QStackedWidget()
        
        # >> 播放页面
        page_play = QWidget()
        play_layout = QHBoxLayout(page_play) # 左右布局：左封面，右歌词
        play_layout.setContentsMargins(50, 50, 50, 50)
        
        # 封面区域
        cover_container = QWidget()
        cover_layout = QVBoxLayout(cover_container)
        self.lbl_cover = QLabel()
        self.lbl_cover.setFixedSize(320, 320)
        self.lbl_cover.setScaledContents(True)
        self.lbl_cover.setPixmap(ArtGenerator.draw_default_cover(320))
        # 给封面加一点阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 10)
        self.lbl_cover.setGraphicsEffect(shadow)
        
        self.lbl_song_title = QLabel("等待播放")
        self.lbl_song_title.setStyleSheet("font-size: 24px; font-weight: bold; margin-top: 20px;")
        self.lbl_song_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_song_title.setWordWrap(True)

        cover_layout.addStretch()
        cover_layout.addWidget(self.lbl_cover, 0, Qt.AlignmentFlag.AlignCenter)
        cover_layout.addWidget(self.lbl_song_title)
        cover_layout.addStretch()

        # 歌词区域
        lyrics_container = QWidget()
        lyrics_layout = QVBoxLayout(lyrics_container)
        
        self.lbl_lrc_pre = QLabel("")
        self.lbl_lrc_cur = QLabel("--- MUSIC PLAYER ---")
        self.lbl_lrc_next = QLabel("")
        
        self.lbl_lrc_pre.setStyleSheet(f"color: {TEXT_GRAY}; font-size: 16px; opacity: 0.5;")
        self.lbl_lrc_cur.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 28px; font-weight: 900;")
        self.lbl_lrc_next.setStyleSheet(f"color: {TEXT_GRAY}; font-size: 16px; opacity: 0.5;")
        
        for lbl in [self.lbl_lrc_pre, self.lbl_lrc_cur, self.lbl_lrc_next]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)

        lyrics_layout.addStretch()
        lyrics_layout.addWidget(self.lbl_lrc_pre)
        lyrics_layout.addSpacing(20)
        lyrics_layout.addWidget(self.lbl_lrc_cur)
        lyrics_layout.addSpacing(20)
        lyrics_layout.addWidget(self.lbl_lrc_next)
        lyrics_layout.addStretch()

        play_layout.addWidget(cover_container, 4)
        play_layout.addWidget(lyrics_container, 6)

        # >> 制作页面
        page_maker = QWidget()
        maker_layout = QVBoxLayout(page_maker)
        maker_layout.setContentsMargins(50, 30, 50, 30)
        
        mk_title = QLabel("歌词制作工坊")
        mk_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        
        self.txt_maker = QTextEdit()
        self.txt_maker.setPlaceholderText("步骤1：在此粘贴纯文本歌词...\n步骤2：点击底部'开始录制'\n步骤3：跟随音乐节奏按空格键")
        
        self.lbl_maker_status = QLabel("准备就绪")
        self.lbl_maker_status.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 16px;")
        
        maker_ctrl_layout = QHBoxLayout()
        self.btn_record = QPushButton("🎙️ 开始录制 (空格打点)")
        self.btn_record.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: #000; font-weight: bold; padding: 10px;")
        self.btn_record.setCheckable(True)
        self.btn_record.clicked.connect(self.toggle_maker_record)
        
        self.btn_save = QPushButton("💾 保存到文件")
        self.btn_save.setStyleSheet("background-color: #333; padding: 10px;")
        self.btn_save.clicked.connect(self.save_lyrics)
        
        maker_ctrl_layout.addWidget(self.btn_record)
        maker_ctrl_layout.addWidget(self.btn_save)
        
        maker_layout.addWidget(mk_title)
        maker_layout.addWidget(self.txt_maker)
        maker_layout.addWidget(self.lbl_maker_status)
        maker_layout.addLayout(maker_ctrl_layout)

        self.stack.addWidget(page_play)
        self.stack.addWidget(page_maker)
        
        content_layout.addWidget(sidebar)
        content_layout.addWidget(self.stack)

        # --- 下半部分：底部控制条 ---
        bottom_bar = QFrame()
        bottom_bar.setObjectName("BottomBar")
        bottom_bar.setFixedHeight(90)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 10, 20, 10)

        # 控制按钮组
        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_next = QPushButton("⏭")
        self.btn_play.setFixedSize(45, 45)
        self.btn_play.setStyleSheet(f"background-color: {TEXT_WHITE}; color: #000; border-radius: 22px; font-size: 20px;")
        
        self.btn_prev.clicked.connect(self.prev_song)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_next.clicked.connect(self.next_song)

        # 模式选择
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["🔁 顺序", "🔂 单曲", "🔀 随机"])
        self.combo_mode.setFixedWidth(80)
        self.combo_mode.currentIndexChanged.connect(lambda i: setattr(self, 'play_mode', i))

        # 进度条组
        progress_layout = QVBoxLayout()
        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_time.setStyleSheet("font-size: 12px; color: #888;")
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.sliderMoved.connect(self.player.setPosition)
        
        progress_layout.addWidget(self.lbl_time)
        progress_layout.addWidget(self.slider)

        bottom_layout.addWidget(self.btn_prev)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(self.btn_play)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(self.btn_next)
        bottom_layout.addSpacing(30)
        bottom_layout.addLayout(progress_layout)
        bottom_layout.addSpacing(20)
        bottom_layout.addWidget(self.combo_mode)

        root_layout.addWidget(content_area)
        root_layout.addWidget(bottom_bar)

    # --- 逻辑处理 ---
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择音乐库")
        if folder:
            self.playlist = []
            self.track_list.clear()
            # 扫描支持的格式
            for f in os.listdir(folder):
                if f.lower().endswith(('.mp3', '.flac', '.wav', '.m4a')):
                    self.playlist.append(os.path.join(folder, f))
                    # 列表只显示文件名，不显示后缀
                    name = os.path.splitext(f)[0]
                    self.track_list.addItem(name)
            if self.playlist:
                self.current_index = 0
                self.play_music(self.playlist[0])

    def play_selected(self):
        idx = self.track_list.currentRow()
        if idx != -1:
            self.current_index = idx
            self.play_music(self.playlist[idx])

    def play_music(self, path):
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.btn_play.setText("⏸")
        self.lbl_song_title.setText(os.path.splitext(os.path.basename(path))[0])
        
        # 尝试加载封面 (cover.jpg 或 folder.jpg)
        folder = os.path.dirname(path)
        cover_found = False
        for img in ['cover.jpg', 'folder.jpg', 'cover.png', 'folder.png']:
            img_path = os.path.join(folder, img)
            if os.path.exists(img_path):
                self.lbl_cover.setPixmap(QPixmap(img_path))
                cover_found = True
                break
        if not cover_found:
            self.lbl_cover.setPixmap(ArtGenerator.draw_default_cover(320))

        self.load_lrc(path)
        # 如果在制作模式，重置状态
        if self.is_maker_active:
            self.toggle_maker_record()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play.setText("▶")
        else:
            self.player.play()
            self.btn_play.setText("⏸")

    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.play_mode == 1: # 单曲
                self.player.play()
            elif self.play_mode == 2: # 随机
                self.current_index = random.randint(0, len(self.playlist)-1)
                self.play_music(self.playlist[self.current_index])
                self.track_list.setCurrentRow(self.current_index)
            else: # 顺序
                self.next_song()

    def next_song(self):
        if not self.playlist: return
        if self.play_mode == 2:
            self.current_index = random.randint(0, len(self.playlist)-1)
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)
        self.track_list.setCurrentRow(self.current_index)
        self.play_music(self.playlist[self.current_index])

    def prev_song(self):
        if not self.playlist: return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.track_list.setCurrentRow(self.current_index)
        self.play_music(self.playlist[self.current_index])

    def update_ui_progress(self, pos):
        self.slider.setValue(pos)
        self.slider.setMaximum(self.player.duration())
        
        # 更新时间文本
        def fmt(ms): return f"{ms//60000:02}:{(ms//1000)%60:02}"
        self.lbl_time.setText(f"{fmt(pos)} / {fmt(self.player.duration())}")

        # 歌词滚动
        if not self.is_maker_active and self.lyrics_times:
            # 查找当前时间对应的歌词索引
            # 使用 filter 找到最后一个小于等于当前时间的索引
            current_lyrics_time = [t for t in self.lyrics_times if t <= pos]
            if current_lyrics_time:
                t = current_lyrics_time[-1]
                idx = self.lyrics_times.index(t)
                
                self.lbl_lrc_cur.setText(self.lyrics_map[t])
                self.lbl_lrc_pre.setText(self.lyrics_map[self.lyrics_times[idx-1]] if idx > 0 else "")
                self.lbl_lrc_next.setText(self.lyrics_map[self.lyrics_times[idx+1]] if idx < len(self.lyrics_times)-1 else "")

    # --- 歌词加载与制作 ---
    def load_lrc(self, audio_path):
        lrc_path = os.path.splitext(audio_path)[0] + ".lrc"
        self.lyrics_map = {}
        self.lyrics_times = []
        self.lbl_lrc_cur.setText("--- 纯音乐 / 无歌词 ---")
        self.lbl_lrc_pre.clear()
        self.lbl_lrc_next.clear()
        
        if os.path.exists(lrc_path):
            try:
                with open(lrc_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if "]" in line:
                            t_str, txt = line.split("]", 1)
                            t_str = t_str.strip("[")
                            m, s = t_str.split(":")
                            ms = int(int(m)*60000 + float(s)*1000)
                            self.lyrics_map[ms] = txt.strip()
                            self.lyrics_times.append(ms)
                self.lyrics_times.sort()
                self.lbl_lrc_cur.setText("--- 歌词已加载 ---")
            except:
                pass

    def toggle_main_view(self):
        if self.stack.currentIndex() == 0:
            self.stack.setCurrentIndex(1)
            self.btn_switch_mode.setText("🎵 返回播放器")
        else:
            self.stack.setCurrentIndex(0)
            self.btn_switch_mode.setText("🛠️ 歌词工坊模式")

    def toggle_maker_record(self):
        if self.btn_record.isChecked():
            # 校验
            text = self.txt_maker.toPlainText().strip()
            if not text:
                self.btn_record.setChecked(False)
                QMessageBox.warning(self, "提示", "请先输入歌词文本")
                return
            
            self.maker_lines = [l.strip() for l in text.split('\n') if l.strip()]
            self.maker_timestamps = []
            self.maker_current_idx = 0
            self.is_maker_active = True
            self.lbl_maker_status.setText(f"录制中... 下一句: {self.maker_lines[0]}")
            self.btn_record.setText("⏹ 停止录制 (点击结束)")
            self.setFocus() # 获取键盘焦点
        else:
            self.is_maker_active = False
            self.lbl_maker_status.setText("录制已停止")
            self.btn_record.setText("🎙️ 开始录制 (空格打点)")

    def keyPressEvent(self, event):
        if self.is_maker_active and event.key() == Qt.Key.Key_Space:
            pos = self.player.position()
            if self.maker_current_idx < len(self.maker_lines):
                self.maker_timestamps.append(pos)
                self.maker_current_idx += 1
                
                if self.maker_current_idx < len(self.maker_lines):
                    self.lbl_maker_status.setText(f"下一句: {self.maker_lines[self.maker_current_idx]}")
                else:
                    self.lbl_maker_status.setText("所有歌词录制完成！")
            else:
                self.toggle_maker_record()

    def save_lyrics(self):
        if not self.playlist: return
        path = os.path.splitext(self.playlist[self.current_index])[0] + ".lrc"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                for i in range(min(len(self.maker_timestamps), len(self.maker_lines))):
                    ms = self.maker_timestamps[i]
                    m = ms // 60000
                    s = (ms % 60000) / 1000
                    f.write(f"[{m:02}:{s:05.2f}]{self.maker_lines[i]}\n")
            QMessageBox.information(self, "成功", f"歌词已保存至: {path}")
            self.load_lrc(self.playlist[self.current_index])
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局字体大小
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = ModernPlayer()
    window.show()
    sys.exit(app.exec())
