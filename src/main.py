import sys
import os
import logging
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from ui.main_window import MainWindow
from core.scanner import WaybillScanner
from datetime import datetime

logger = logging.getLogger(__name__)

class ProcessThread(QThread):
    """处理线程"""
    progress_updated = pyqtSignal(int, int, str)  # 进度更新信号
    process_finished = pyqtSignal(int, int)  # 处理完成信号
    
    def __init__(self, source_folder, target_folder, scanner_options):
        super().__init__()
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.success_folder = os.path.join(target_folder, 'success')  # 添加成功文件夹路径
        self.scanner_options = scanner_options
        self.scanner = None  # 初始化时不创建scanner实例
        
    def prepare_folders(self):
        """准备目标文件夹结构"""
        try:
            # 确保目标文件夹存在
            os.makedirs(self.target_folder, exist_ok=True)
            # 确保success子文件夹存在
            os.makedirs(self.success_folder, exist_ok=True)
            logger.info(f"创建目标文件夹结构: {self.target_folder}")
        except Exception as e:
            logger.error(f"创建文件夹失败: {str(e)}")
            raise

    def generate_summary(self, target_folder: str, results: list) -> None:
        """
        生成处理总结并保存到文件
        Args:
            target_folder: 目标文件夹路径
            results: 处理结果列表，每项格式为 (状态, 原文件名, 新文件名, 原因)
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary_path = os.path.join(target_folder, "处理总结.txt")
            
            success_count = sum(1 for r in results if r[0] == "成功")
            fail_count = sum(1 for r in results if r[0] == "失败")
            total_count = len(results)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                # 写入标题
                f.write(f"处理时间：{current_time}\n")
                f.write("-" * 40 + "\n")
                
                # 写入详细结果
                for status, old_name, new_name, reason in sorted(results):
                    if status == "成功":
                        f.write(f"成功 - {old_name} -> {new_name}\n")
                    else:
                        f.write(f"失败 - {old_name} ({reason})\n")
                
                # 写入统计信息
                f.write("-" * 40 + "\n")
                f.write("处理完成！\n")
                f.write(f"总数：{total_count}\n")
                f.write(f"成功：{success_count}\n")
                f.write(f"失败：{fail_count}\n")
                
            logger.info(f"处理总结已保存到：{summary_path}")
            
        except Exception as e:
            logger.error(f"生成处理总结失败: {str(e)}")

    def run(self):
        try:
            self.scanner = WaybillScanner()
            logger.info("开始处理图片...")
            
            # 准备文件夹
            self.prepare_folders()
            
            # 获取所有图片文件
            image_files = [f for f in os.listdir(self.source_folder) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            total = len(image_files)
            success_count = 0
            fail_count = 0
            
            # 存储处理结果
            results = []
            
            logger.info(f"找到 {total} 个图片文件")
            
            for idx, filename in enumerate(image_files, 1):
                try:
                    file_path = os.path.join(self.source_folder, filename)
                    logger.debug(f"处理文件: {filename}")
                    
                    # 识别运单号
                    waybill_number = self.scanner.scan_single(file_path, self.scanner_options)
                    logger.debug(f"识别结果: {waybill_number}")
                    
                    if waybill_number:
                        # 获取文件扩展名
                        _, ext = os.path.splitext(filename)
                        # 新文件名
                        new_filename = f"{waybill_number}{ext}"
                        # 移动到success子文件夹
                        new_path = os.path.join(self.success_folder, new_filename)
                        
                        # 移动并重命名文件
                        os.rename(file_path, new_path)
                        success_count += 1
                        logger.info(f"成功处理文件: {filename} -> {new_filename}")
                        
                        # 记录成功结果
                        results.append(("成功", filename, new_filename, ""))
                    else:
                        fail_count += 1
                        logger.warning(f"未能识别运单号: {filename}")
                        
                        # 记录失败结果
                        results.append(("失败", filename, "", "未识别到运单号"))
                    
                    # 发送进度信号
                    self.progress_updated.emit(idx, total, filename)
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"处理文件 {filename} 时出错: {error_msg}")
                    fail_count += 1
                    # 记录失败结果
                    results.append(("失败", filename, "", f"处理出错: {error_msg}"))
            
            # 生成处理总结
            self.generate_summary(self.target_folder, results)
            
            # 发送完成信号
            logger.info(f"处理完成: 成功 {success_count}, 失败 {fail_count}")
            self.process_finished.emit(success_count, fail_count)
                
        except Exception as e:
            logger.error(f"处理线程运行失败: {str(e)}")
            self.process_finished.emit(0, 0)

def setup_logging():
    """设置日志"""
    # 完全禁用日志输出
    logging.getLogger().setLevel(logging.CRITICAL)

def check_config():
    """检查配置文件"""
    config_path = 'config.json'
    if not os.path.exists(config_path):
        default_config = {
            "tencent_ocr": {
                "enabled": False,
                "secret_id": "",
                "secret_key": ""
            }
        }
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"创建配置文件失败: {str(e)}")

def main():
    """主函数"""
    setup_logging()
    check_config()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 