[app]

# 应用名称（手机上显示的名字）
title = VideoAlign

# 包名（Android 应用唯一标识）
package.name = videoalign
package.domain = org.videoalign

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.include_patterns = *.kv,app_kivy/**,core/**,models/**,utils/**,video/**,ffmpeg/**

version = 0.1.0

# python3 必须是第一个；opencv/ffmpeg 由 python-for-android 交叉编译
# numpy 用 git 拉取，tag 是 v1.26.4（带 v 前缀），必须写 v1.26.4
# p4a 默认 numpy 2.3.0 在 NDK 25b 下编译失败（unordered_map），故锁定 1.26.4
requirements = python3,kivy==2.3.1,numpy==v1.26.4,opencv,ffmpeg

orientation = portrait
fullscreen = 0

# Android SDK / NDK 版本（buildozer 会自动下载）
android.api = 34
android.minapi = 24
android.ndk = 25b

# 只构建 64 位，覆盖绝大多数现代手机，且构建更快
android.archs = arm64-v8a

android.accept_sdk_license = True
android.allow_backup = True

# 使用 SAF 系统文件选择器，不需要存储权限
android.permissions =

[buildozer]

log_level = 2
warn_on_root = 1
