import os
import sys

def _append_run_path():
    if getattr(sys, 'frozen', False):
        # 获取程序运行目录
        app_dir = os.path.dirname(sys.executable)
        # 将运行目录添加到PATH
        os.environ['PATH'] = app_dir + os.pathsep + os.environ.get('PATH', '')
        
        # 设置Tesseract数据目录
        os.environ['TESSDATA_PREFIX'] = os.path.join(app_dir, 'tessdata')

_append_run_path() 