# 🎤 VoiceType

全局语音输入工具，按住热键说话，松开自动识别并粘贴到当前输入框。

基于 [FunASR](https://github.com/modelscope/FunASR) 的 `paraformer-zh` 模型，中文识别准确率高。

![icon](icon.webp)

## ✨ 功能

- 🔴 毛玻璃风格小圆球，录音状态一目了然
- 🎯 全局热键，无需切换窗口
- 📋 识别后自动粘贴到当前输入框
- ⚙️ 右键菜单，支持自定义热键、模型选择、VAD/标点开关
- 🖱️ 可拖动，置顶显示

## 📦 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载模型

首次运行前需要下载语音识别模型：

| 模型 | 大小 | 说明 | 下载地址 |
|------|------|------|----------|
| paraformer-zh | ~950MB | 语音识别主模型（必选） | [ModelScope](https://modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch) |
| fsmn-vad | ~4MB | 语音活动检测（可选） | [ModelScope](https://modelscope.cn/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch) |
| ct-punc | ~1.2GB | 标点恢复（可选） | [ModelScope](https://modelscope.cn/models/iic/punc_ct-transformer_cn-en-common-vocab471067-large) |

### 3. 放置模型

下载后解压到项目目录下的 `models/` 文件夹：

```
voice_to_text.py 所在目录/
└── models/
    ├── paraformer-zh/    ← 主模型（必选）
    ├── vad/              ← VAD（可选）
    └── punc/             ← 标点（可选）
```

> 💡 只装主模型也能用，VAD 和标点可以按需开启/关闭。

### 4. 运行

```bash
python voice_to_text.py
```

## 🎮 使用

| 操作 | 说明 |
|------|------|
| 按住热键 | 开始录音（圆球变红闪烁） |
| 松开热键 | 识别并粘贴（圆球变黄→绿） |
| 右键圆球 | 打开设置菜单 |
| 拖动圆球 | 移动位置 |
| Esc | 退出程序 |

## ⚙️ 右键菜单

- **加载主模型** — 选择本地模型文件夹（支持自由加载任意 FunASR 兼容模型）
- **VAD 语音检测** — 自动切分语音段，去掉静音噪音
- **标点恢复** — 自动加逗号、句号、问号
- **更换热键** — 支持 Right Ctrl / Left Ctrl / Alt / F1-F6 等

## 📋 环境要求

- Python 3.8+
- NVIDIA GPU（推荐）或 CPU
- Windows 10/11

## 📄 License

MIT
