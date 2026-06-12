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

### 方式一：直接运行源码

```bash
pip install -r requirements.txt
python voice_to_text.py
```

### 方式二：下载 exe（推荐）

从 [Releases](../../releases) 页面下载 `VoiceType.exe`，双击运行即可。

## 🧠 模型下载

首次运行需要下载语音识别模型，共三个：

| 模型 | 大小 | 说明 | 下载地址 |
|------|------|------|----------|
| paraformer-zh | ~950MB | 语音识别主模型（必选） | [ModelScope](https://modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch) |
| fsmn-vad | ~4MB | 语音活动检测（可选，去掉静音） | [ModelScope](https://modelscope.cn/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch) |
| ct-punc | ~1.2GB | 标点恢复（可选，自动加标点） | [ModelScope](https://modelscope.cn/models/iic/punc_ct-transformer_cn-en-common-vocab471067-large) |

### 安装模型

下载后解压到以下目录结构：

```
VoiceType.exe 所在目录/
└── models/
    ├── paraformer-zh/    ← 主模型
    ├── vad/              ← VAD（可选）
    └── punc/             ← 标点（可选）
```

> 💡 只装主模型也能用，VAD 和标点可以按需开启/关闭。

## 🎮 使用

| 操作 | 说明 |
|------|------|
| 按住热键 | 开始录音（圆球变红闪烁） |
| 松开热键 | 识别并粘贴（圆球变黄→绿） |
| 右键圆球 | 打开设置菜单 |
| 拖动圆球 | 移动位置 |
| Esc | 退出程序 |

## ⚙️ 右键菜单

- **加载主模型** — 选择本地模型文件夹
- **VAD 语音检测** — 自动切分语音段，去掉静音噪音
- **标点恢复** — 自动加逗号、句号、问号
- **更换热键** — 支持 Right Ctrl / Left Ctrl / Alt / F1-F6 等

## 📋 依赖

- Python 3.8+（源码运行时需要）
- NVIDIA GPU（推荐）或 CPU
- Windows 10/11

## 🔧 模型说明

- **主模型**：完全由用户自由选择，支持任何 FunASR 兼容的模型
- **VAD**：可选，帮助模型区分人声和静音
- **标点恢复**：可选，自动为识别结果添加标点

## 📄 License

MIT
