"""
VoiceType - 全局语音输入工具
毛玻璃风格小圆球，按住说话，松开自动粘贴
支持用户自由加载本地模型
"""
import sys
import io
import os
import re
import logging
import warnings
import threading
import time
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import pyaudio
import keyboard
import pyperclip
import pyautogui
from funasr import AutoModel

# 静默日志
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdout.reconfigure(line_buffering=True)
sys.stderr = open(os.devnull, 'w')
os.environ["TQDM_DISABLE"] = "1"
os.environ["FUNASR_DISABLE_UPDATE"] = "1"
logging.disable(logging.CRITICAL)
warnings.filterwarnings("ignore")

# 路径
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "voice_config.json")
MODELS_DIR = os.path.join(APP_DIR, "models")

DEFAULT_CONFIG = {
    "hotkey": "right ctrl",
    "opacity": 0.75,
    "model_path": "",           # 主模型本地路径（空=未设置）
    "model_name": "",           # 显示用的模型名称
    "use_vad": True,
    "use_punc": True,
    "first_run": True,          # 首次运行标记
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in config:
                        config[k] = v
                return config
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def clean_text(text):
    text = re.sub(r'<\|[^|]*\|>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_valid_model_path(path):
    """检查路径是否是有效的模型文件夹"""
    if not path or not os.path.isdir(path):
        return False
    # 检查是否有模型文件
    for f in os.listdir(path):
        if f.endswith('.onnx') or f.endswith('.pt') or f == 'config.yaml':
            return True
    return False

class GlassBall:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("VoiceType")
        self.root.geometry("+100+100")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', self.config['opacity'])

        # 透明色（仅在非打包模式下使用，打包后可能导致窗口不可见）
        self.transparent_color = '#f0f0f0'
        if not getattr(sys, 'frozen', False):
            try:
                self.root.wm_attributes('-transparentcolor', self.transparent_color)
            except:
                pass

        # 尺寸
        self.size = 36
        self.pad = 4

        # 画布（打包后用深色背景代替透明）
        canvas_bg = '#1a1a2e' if getattr(sys, 'frozen', False) else self.transparent_color
        self.canvas = tk.Canvas(
            self.root,
            width=self.size + self.pad * 2,
            height=self.size + self.pad * 2,
            highlightthickness=0,
            bg=canvas_bg
        )
        self.canvas.pack()

        # 外圈
        self.outer = self.canvas.create_oval(
            self.pad, self.pad,
            self.size + self.pad, self.size + self.pad,
            fill='#2d2d44', outline='#4a4a6a', width=1.5
        )

        # 内圈
        inner_pad = self.pad + 4
        self.inner = self.canvas.create_oval(
            inner_pad, inner_pad,
            self.size + self.pad - 4, self.size + self.pad - 4,
            fill='#6bcb77', outline='#5ab868', width=1
        )

        # 中心点
        center = self.size // 2 + self.pad
        r = 3
        self.dot = self.canvas.create_oval(
            center - r, center - r, center + r, center + r,
            fill='#ffffff', outline='#ffffff'
        )

        # 拖动
        self.drag_data = {"x": 0, "y": 0}
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)

        # 右键菜单
        self.canvas.bind("<ButtonPress-3>", self.show_menu)

        # 状态
        self.recording = False
        self.audio_buffer = []
        self.model = None
        self.stream = None
        self.pa = None
        self.model_loaded = False
        self.current_hotkey = self.config['hotkey']
        self.animating = False

        # 颜色
        self.colors = {
            'idle': ('#6bcb77', '#5ab868'),
            'recording': ('#ff6b6b', '#ee5a5a'),
            'processing': ('#ffd93d', '#f0c929'),
            'success': ('#6bcb77', '#5ab868'),
            'error': ('#ff6b6b', '#ee5a5a'),
        }

        self.register_hotkey()
        keyboard.on_press_key('esc', lambda e: self.root.quit())

    def register_hotkey(self):
        try:
            keyboard.unhook_all()
            keyboard.on_press_key(self.current_hotkey, self.on_press)
            keyboard.on_release_key(self.current_hotkey, self.on_release)
            keyboard.on_press_key('esc', lambda e: self.root.quit())
        except:
            pass

    def start_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def do_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_data["x"]
        y = self.root.winfo_y() + event.y - self.drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def show_menu(self, event):
        menu_style = {'bg': '#2d2d44', 'fg': '#ffffff',
                      'activebackground': '#4a4a6a', 'activeforeground': '#ffffff',
                      'font': ('微软雅黑', 10)}

        menu = tk.Menu(self.root, tearoff=0, **menu_style)

        # === 当前模型状态 ===
        model_display = self.config.get('model_name', '未设置')
        if not model_display:
            model_display = '未设置'
        menu.add_command(
            label=f"当前模型: {model_display}",
            state="disabled",
            foreground='#888888'
        )
        menu.add_separator()

        # === 加载主模型 ===
        model_menu = tk.Menu(menu, tearoff=0, **menu_style)
        model_menu.add_command(
            label="📁 选择本地模型文件夹...",
            command=self.browse_model
        )
        menu.add_cascade(label="加载主模型", menu=model_menu)

        menu.add_separator()

        # === VAD ===
        vad_state = "✓ 开" if self.config.get('use_vad', True) else "✗ 关"
        vad_menu = tk.Menu(menu, tearoff=0, **menu_style)
        vad_menu.add_command(
            label="说明: 自动切分语音段，去掉静音噪音",
            state="disabled", foreground='#666666'
        )
        vad_menu.add_separator()
        vad_menu.add_command(
            label="→ 开启" if not self.config.get('use_vad', True) else "→ 已开启",
            command=lambda: self.toggle_vad(True)
        )
        vad_menu.add_command(
            label="→ 关闭" if self.config.get('use_vad', True) else "→ 已关闭",
            command=lambda: self.toggle_vad(False)
        )
        menu.add_cascade(label=f"VAD 语音检测 [{vad_state}]", menu=vad_menu)

        # === 标点 ===
        punc_state = "✓ 开" if self.config.get('use_punc', True) else "✗ 关"
        punc_menu = tk.Menu(menu, tearoff=0, **menu_style)
        punc_menu.add_command(
            label="说明: 自动加逗号、句号、问号",
            state="disabled", foreground='#666666'
        )
        punc_menu.add_separator()
        punc_menu.add_command(
            label="→ 开启" if not self.config.get('use_punc', True) else "→ 已开启",
            command=lambda: self.toggle_punc(True)
        )
        punc_menu.add_command(
            label="→ 关闭" if self.config.get('use_punc', True) else "→ 已关闭",
            command=lambda: self.toggle_punc(False)
        )
        menu.add_cascade(label=f"标点恢复 [{punc_state}]", menu=punc_menu)

        menu.add_separator()

        # === 热键 ===
        keys = ["right ctrl", "left ctrl", "right alt", "left alt",
                "f1", "f2", "f3", "f4", "f5", "f6"]
        hotkey_menu = tk.Menu(menu, tearoff=0, **menu_style)
        for key in keys:
            mark = " ✓" if key == self.current_hotkey else ""
            hotkey_menu.add_command(
                label=key + mark,
                command=lambda k=key: self.change_hotkey(k)
            )
        menu.add_cascade(label="更换热键", menu=hotkey_menu)

        menu.add_separator()
        menu.add_command(label="退出", command=self.root.quit, foreground='#ff6b6b')

        menu.post(event.x_root, event.y_root)

    def browse_model(self):
        """浏览选择本地模型文件夹"""
        folder = filedialog.askdirectory(
            title="选择模型文件夹",
            initialdir=MODELS_DIR if os.path.exists(MODELS_DIR) else APP_DIR
        )
        if folder:
            if is_valid_model_path(folder):
                self.config['model_path'] = folder
                self.config['model_name'] = os.path.basename(folder)
                save_config(self.config)
                threading.Thread(target=self.reload_model, daemon=True).start()
            else:
                messagebox.showerror(
                    "模型无效",
                    "所选文件夹不是有效的模型目录。\n\n"
                    "请确保文件夹内包含 .onnx 或 config.yaml 文件。"
                )

    def toggle_vad(self, enabled):
        self.config['use_vad'] = enabled
        save_config(self.config)
        if self.model_loaded:
            threading.Thread(target=self.reload_model, daemon=True).start()

    def toggle_punc(self, enabled):
        self.config['use_punc'] = enabled
        save_config(self.config)
        if self.model_loaded:
            threading.Thread(target=self.reload_model, daemon=True).start()

    def change_hotkey(self, key):
        self.current_hotkey = key
        self.config['hotkey'] = key
        save_config(self.config)
        self.register_hotkey()

    def set_state(self, state):
        """线程安全：通过 root.after 调度到主线程"""
        try:
            self.root.after(0, self._apply_state, state)
        except:
            pass

    def _apply_state(self, state):
        fill, outline = self.colors[state]
        self.canvas.itemconfig(self.inner, fill=fill, outline=outline)
        if state == 'processing':
            self.animating = True
            self.pulse_animation('processing')
        else:
            self.animating = False

    def pulse_animation(self, color='recording'):
        if not self.animating:
            return
        fill, _ = self.colors[color]
        current = self.canvas.itemcget(self.inner, 'fill')
        if current == fill:
            self.canvas.itemconfig(self.inner, fill='#1a1a2e')
        else:
            self.canvas.itemconfig(self.inner, fill=fill)
        self.root.after(500, lambda: self.pulse_animation(color))

    def on_press(self, event):
        if not self.recording and self.model_loaded:
            self.recording = True
            self.audio_buffer = []
            self.set_state('recording')
            self.animating = True
            self.pulse_animation('recording')

    def on_release(self, event):
        if self.recording:
            self.recording = False
            self.animating = False
            self.set_state('processing')
            if self.audio_buffer:
                threading.Thread(target=self.recognize, daemon=True).start()

    def recognize(self):
        try:
            audio = np.concatenate(self.audio_buffer)
            if len(audio) < 16000 * 0.3:
                self.set_state('idle')
                return
            if np.max(np.abs(audio)) < 0.01:
                self.set_state('idle')
                return

            res = self.model.generate(input=audio, batch_size_s=300)
            if res and res[0]['text']:
                text = clean_text(res[0]['text'])
                if text:
                    pyperclip.copy(text)
                    time.sleep(0.1)
                    pyautogui.hotkey('ctrl', 'v')
                    self.set_state('success')
                    time.sleep(0.5)
        except:
            pass

        self.set_state('idle')

    def load_model(self):
        """首次加载模型"""
        self.set_state('processing')

        # 检查是否有保存的模型路径
        model_path = self.config.get('model_path', '')

        if model_path and is_valid_model_path(model_path):
            # 从本地加载
            self._do_load_model(model_path)
        else:
            # 没有模型，提示用户
            self.root.after(0, self.show_no_model_dialog)

    def show_no_model_dialog(self):
        """弹窗提示用户选择模型"""
        result = messagebox.askyesno(
            "VoiceType - 首次运行",
            "欢迎使用 VoiceType！\n\n"
            "首次运行需要加载语音识别模型。\n\n"
            "请先下载模型文件，然后选择模型文件夹。\n\n"
            "是否现在选择模型文件夹？"
        )
        if result:
            self.browse_model()
        else:
            self.set_state('idle')

    def _do_load_model(self, model_path):
        """实际加载模型"""
        try:
            kwargs = {
                "model": model_path,
                "device": "cuda",
                "disable_update": True,
            }

            if self.config.get('use_vad', True):
                vad_path = os.path.join(MODELS_DIR, "vad")
                if is_valid_model_path(vad_path):
                    kwargs["vad_model"] = vad_path
                else:
                    kwargs["vad_model"] = "fsmn-vad"
                    kwargs["vad_model_revision"] = "v2.0.4"

            if self.config.get('use_punc', True):
                punc_path = os.path.join(MODELS_DIR, "punc")
                if is_valid_model_path(punc_path):
                    kwargs["punc_model"] = punc_path
                else:
                    kwargs["punc_model"] = "ct-punc"
                    kwargs["punc_model_revision"] = "v2.0.4"

            self.model = AutoModel(**kwargs)

            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass

            self.pa = pyaudio.PyAudio()
            self.stream = self.pa.open(
                format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=1024
            )
            self.model_loaded = True
            self.set_state('idle')
        except Exception as e:
            self.model_loaded = False
            self.set_state('idle')
            self.root.after(0, lambda: messagebox.showerror(
                "模型加载失败",
                f"无法加载模型:\n{str(e)}\n\n请检查模型文件夹是否完整。"
            ))

    def reload_model(self):
        """重新加载模型（切换设置后调用）"""
        self.model_loaded = False
        self.set_state('processing')

        model_path = self.config.get('model_path', '')
        if model_path and is_valid_model_path(model_path):
            self._do_load_model(model_path)
        else:
            self.set_state('idle')

    def audio_loop(self):
        if self.recording and self.stream:
            try:
                data = self.stream.read(1024, exception_on_overflow=False)
                audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                self.audio_buffer.append(audio)
            except:
                pass
        self.root.after(10, self.audio_loop)

    def run(self):
        self.set_state('idle')
        self.root.after(100, self.audio_loop)
        threading.Thread(target=self.load_model, daemon=True).start()
        self.root.mainloop()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.pa:
            self.pa.terminate()

if __name__ == '__main__':
    app = GlassBall()
    app.run()
