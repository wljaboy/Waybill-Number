import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from logging import getLogger

logger = getLogger(__name__)

class Scanner:
    def __init__(self):
        self.processor = ImageProcessor()
        self.success_count = 0
        self.failed_count = 0
        self.failed_files: List[str] = []
        self.success_files: List[Dict[str, str]] = []  # 存储成功文件的原名和新名
        
    def process_directory(self, input_dir: str, output_dir: str, options: Dict) -> None:
        """处理指定目录下的所有图片"""
        # 重置计数器
        self.success_count = 0
        self.failed_count = 0
        self.failed_files.clear()
        self.success_files.clear()
        
        # 创建输出目录结构
        os.makedirs(output_dir, exist_ok=True)
        success_dir = os.path.join(output_dir, 'success')
        os.makedirs(success_dir, exist_ok=True)
        
        # 获取所有图片文件
        image_files = [f for f in os.listdir(input_dir) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        # 处理每个图片
        for image_file in image_files:
            input_path = os.path.join(input_dir, image_file)
            logger.debug(f"开始处理图片: {input_path}")
            
            result = self.processor.process_image(input_path, options)
            
            if result:
                # 处理成功
                self.success_count += 1
                new_name = f"{result}{os.path.splitext(image_file)[1]}"
                success_path = os.path.join(success_dir, new_name)
                
                # 移动文件
                shutil.move(input_path, success_path)
                logger.info(f"处理成功: {image_file} -> {new_name}")
                
                self.success_files.append({
                    'original': image_file,
                    'new': new_name
                })
            else:
                # 处理失败
                self.failed_count += 1
                self.failed_files.append(image_file)
                logger.warning(f"处理失败: {image_file}")
        
        # 生成处理报告
        self._generate_report(output_dir)
        
    def _generate_report(self, output_dir: str) -> None:
        """生成处理报告"""
        report_path = os.path.join(output_dir, 'processing_report.txt')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # 写入报告头部
            f.write(f"处理时间：{current_time}\n")
            f.write("-" * 40 + "\n")
            
            # 写入失败文件列表
            for failed_file in self.failed_files:
                f.write(f"失败 - {failed_file} (未识别到运单号)\n")
            
            # 写入分隔线
            f.write("-" * 40 + "\n")
            
            # 写入统计信息
            f.write("处理完成！\n")
            total = self.success_count + self.failed_count
            f.write(f"总数：{total}\n")
            f.write(f"成功：{self.success_count}\n")
            f.write(f"失败：{self.failed_count}\n")
        
        logger.info(f"处理报告已生成: {report_path}") 