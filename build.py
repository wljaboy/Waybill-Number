import PyInstaller.__main__
import os
import sys
import shutil

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 检查必要文件是否存在
version_file = os.path.join(current_dir, 'version_info.py')
if not os.path.exists(version_file):
    print(f"错误：找不到版本信息文件: {version_file}")
    sys.exit(1)

# Tesseract 相关文件路径
tesseract_path = "C:\\Program Files\\Tesseract-OCR"
tesseract_files = [
    'tesseract.exe',
    'libtesseract-5.dll',
    'leptonica-1.82.0.dll',
    'libgcc_s_seh-1.dll',
    'libstdc++-6.dll',
    'libwinpthread-1.dll',
    'libzlib-1.dll',
    'libwebp-7.dll',
    'libpng16-16.dll',
    'libjpeg-8.dll',
    'libtiff-5.dll',
    'libgif-7.dll',
    'libgomp-1.dll',
]

# 添加 Tesseract 二进制文件
tesseract_binaries = []
for file in tesseract_files:
    file_path = os.path.join(tesseract_path, file)
    if os.path.exists(file_path):
        tesseract_binaries.append((file_path, '.'))
    else:
        print(f"警告：找不到 Tesseract 文件: {file_path}")

# 添加 Tesseract 语言数据文件
tessdata_source = os.path.join(tesseract_path, 'tessdata')
tessdata_files = [
    'eng.traineddata',  # 英文
    'chi_sim.traineddata',  # 简体中文
    'osd.traineddata',  # 方向和脚本检测
]

# 创建临时 tessdata 目录
temp_tessdata = os.path.join(current_dir, 'temp_tessdata')
os.makedirs(temp_tessdata, exist_ok=True)

# 复制必要的语言文件
for file in tessdata_files:
    src = os.path.join(tessdata_source, file)
    dst = os.path.join(temp_tessdata, file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
    else:
        print(f"警告：找不到语言文件: {src}")

# 定义打包选项
options = [
    'src/main.py',  # 主程序入口
    '--name=回单整理器_v1.3',  # 程序名称
    '--noconsole',  # 不显示控制台
    '--onefile',  # 打包为单个文件
    f'--icon={os.path.join(current_dir, "src/ui/icon.ico")}',  # 程序图标
    '--clean',  # 清理临时文件
    '--add-data=config.json;.',  # 添加配置文件
    # 添加 Tesseract 数据文件
    f'--add-data={temp_tessdata};tessdata',
    # 添加其他必要的二进制文件
    f'--add-binary={os.path.join(current_dir, "libs", "libiconv.dll")};.',
    f'--add-binary={os.path.join(current_dir, "libs", "libzbar-64.dll")};.',
    # 添加版本信息
    f'--version-file={version_file}',
    # 添加程序信息
    '--add-data=src/ui/icon.ico;ui',
    # 减少误报的选项
    '--uac-admin',  # 请求管理员权限
    '--noupx',  # 不使用UPX压缩
    '--disable-windowed-traceback',  # 禁用窗口化追踪
]

# 添加所有 Tesseract 二进制文件
for src, dst in tesseract_binaries:
    options.extend(['--add-binary', f'{src};{dst}'])

try:
    # 设置环境变量
    os.environ['PYTHONOPTIMIZE'] = '1'

    # 运行打包命令
    PyInstaller.__main__.run(options)

finally:
    # 清理临时文件
    if os.path.exists(temp_tessdata):
        shutil.rmtree(temp_tessdata) 