# VideoAlign Android 版（可行性原型）

把桌面版 `VideoAlign`（Python + Tkinter）移植到安卓手机。本工程复用了原项目
的**全部纯逻辑层**（`core/`、`models/`、`utils/`、`video/`、`ffmpeg/`），
只把界面换成了 **Kivy**（跨平台 UI 框架），因此同一套代码既能跑在 Windows
桌面，也能打包成安卓 APK。

## 一、工程结构

```
VideoAlign-Android/
├── main.py                  # Kivy 应用入口
├── main.kv                  # 界面布局（竖屏手机）
├── app_kivy/
│   ├── controller.py        # 业务控制器（复用原项目核心逻辑）
│   ├── preview_widget.py    # 预览画布：显示合成帧 + 触摸拖动嵌入框
│   ├── screen.py            # 主屏幕：界面与控制器之间的桥梁
│   └── file_picker.py       # 文件选择：Android SAF / 桌面 Tkinter
├── core/  models/  utils/   # 原项目纯逻辑层，原样复用（勿改）
├── video/                   # OpenCV 解码/合成/探测（原样复用）
├── ffmpeg/                  # 导出命令（runner 已适配 Android 路径）
├── buildozer.spec           # APK 构建配置
└── .github/workflows/       # GitHub Actions 云端构建
```

## 二、在电脑上先跑起来（Windows / macOS / Linux）

需要 Python 3.8+，然后：

```powershell
pip install kivy==2.3.1 numpy opencv-python
python main.py
```

桌面端会打开 Kivy 窗口，功能与手机端完全一致：

1. **导入主视频** → 选一个视频（如手机拍的竖屏视频）
2. **添加嵌入视频** → 选要嵌入的画面
3. 预览区会显示合成结果，**手指（鼠标）按住蓝色框拖动**可调整嵌入位置
4. **播放 / 暂停 / ±1帧 / 时间轴拖动** 定位
5. **设A=当前** 记录主视频时间；**B时间** 填嵌入视频对应的时间 → **+同步点**
   （可添加多个同步点建立 A/B 时间映射，支持变速对齐）
6. **导出视频** → 选保存位置，后台用 FFmpeg 合成导出

> 桌面端导出需要系统已安装 `ffmpeg`（`pip install imageio-ffmpeg` 也可）。

## 三、打包成安卓 APK（二选一）

### 方案 A：GitHub Actions 云端构建（推荐，零本地环境）⭐

你的电脑完全不用装任何安卓工具，构建在 GitHub 免费服务器上完成：

1. 注册 GitHub 账号，新建一个仓库（如 `VideoAlign-Android`）
2. 把本目录**所有内容**推送到仓库（`buildozer.spec` 必须在仓库根目录）
   ```powershell
   git init
   git add .
   git commit -m "VideoAlign Android prototype"
   git remote add origin https://github.com/<你的用户名>/VideoAlign-Android.git
   git push -u origin main
   ```
3. 打开仓库页面 → **Actions** 标签 → 左侧 **Build Android APK** → 点
   **Run workflow** → 等待构建（首次约 1~3 小时，OpenCV/FFmpeg 交叉编译较慢；
   第二次起有缓存会快很多）
4. 构建完成后，进入该次运行页面，**Artifacts** 区下载 `videoalign-debug-apk`
5. 解压得到 `videoalign-0.1.0-arm64-v8a-debug.apk`，传到手机安装即可
   （设置里需允许"安装未知来源应用"）

### 方案 B：Windows 上用 WSL2 + buildozer 本机构建

python-for-android 不支持 Windows 原生，需要装 Linux 子系统：

1. **安装 WSL2**（管理员 PowerShell）：
   ```powershell
   wsl --install -d Ubuntu-22.04
   ```
   装完重启电脑，首次启动 Ubuntu 时设置用户名/密码。
2. **在 Ubuntu 里装依赖**：
   ```bash
   sudo apt update
   sudo apt install -y git zip unzip python3-pip python3-venv \
     openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev \
     libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
   pip3 install --upgrade pip
   pip3 install buildozer cython
   ```
3. **把工程拷进 WSL**（在 WSL 终端里）：
   ```bash
   cd /mnt/d/Desktop/工具/VideoAlign-Android
   ```
   （如果 WSL 访问 D 盘太慢，可先 `cp -r /mnt/d/Desktop/工具/VideoAlign-Android ~/va && cd ~/va`）
4. **开始构建**（首次会自动下载 Android SDK/NDK，需联网约 2~3 GB）：
   ```bash
   buildozer -v android debug
   ```
5. 完成后 APK 在 `bin/` 目录：
   ```bash
   ls bin/            # 输出 videoalign-0.1.0-arm64-v8a-debug.apk
   cp bin/*.apk /mnt/d/Desktop/工具/  # 拷回 Windows
   ```

## 四、手机上如何安装

- 把 APK 传到手机（微信文件传输/数据线/网盘都行），点击安装
- 若提示"未知来源"，在系统设置 → 安全 里允许本次安装
- 打开 App：**导入主视频** 会弹出系统文件选择器（SAF），选视频即可；
  不需要任何存储权限

## 五、已知限制与后续优化方向

| 问题 | 说明 | 优化方向 |
|---|---|---|
| 预览性能 | 原型用 OpenCV 逐帧解码，手机播放高清视频可能偏慢 | 降低预览分辨率解码；用 MediaCodec 硬解 |
| APK 体积 | OpenCV+FFmpeg+Python 约 80~150MB | 原生 Kotlin 重写可到 20MB 内 |
| 只支持 64 位 | `android.archs = arm64-v8a` | 需要老 32 位手机时加 `armeabi-v7a` |
| 导出编码 | FFmpeg `libx264` 软件编码，长视频导出较慢 | 换 `h264_mediacodec` 硬编码 |

## 六、常见问题（FAQ）

**Q1: GitHub Actions 构建失败，日志里有 `recipe for target ... failed`？**
大多是 OpenCV 交叉编译的环境问题。常见解决办法：
- 清掉缓存重新跑（Actions → 左侧 Cache → 删除缓存）
- 确认 `buildozer.spec` 中 `android.ndk = 25b`（OpenCV 对过新 NDK 兼容性差）

**Q2: 手机上点"导入视频"没反应？**
SAF 选择器依赖系统文件管理器，个别国产 ROM 可能拦截。可换用系统自带
"文件管理"或"相册"应用再试。

**Q3: 导出提示找不到 FFmpeg？**
APK 里没打进 ffmpeg recipe。检查 `buildozer.spec` 的 requirements 是否
包含 `ffmpeg`，并确认构建日志里 ffmpeg recipe 构建成功。

**Q4: 桌面运行时提示缺模块？**
```powershell
pip install kivy==2.3.1 numpy opencv-python imageio-ffmpeg
```
