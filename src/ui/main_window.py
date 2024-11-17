import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QCheckBox, QProgressBar, QFileDialog, QGroupBox, QSpinBox,
    QDialog, QDialogButtonBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen
import logging
from datetime import datetime
import json
from core.scanner import WaybillScanner
import sys

logger = logging.getLogger(__name__)

class ProcessThread(QThread):
    """处理线程"""
    progress_updated = pyqtSignal(int, int, str)  # 进度更新信号
    process_finished = pyqtSignal(int, int)  # 处理完成信号
    
    def __init__(self, source_folder, target_folder, options):
        super().__init__()
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.success_folder = os.path.join(target_folder, 'success')  # 成功文件夹路径
        self.options = options
        self.scanner = None
    
    def prepare_folders(self):
        """准备目标文件夹结构"""
        try:
            # 确保目标件夹存在
            os.makedirs(self.target_folder, exist_ok=True)
            # 确保success子文件夹存在
            os.makedirs(self.success_folder, exist_ok=True)
            logger.info(f"创建目标文件夹结构: {self.target_folder}")
        except Exception as e:
            logger.error(f"创建文件夹失败: {str(e)}")
            raise

    def generate_summary(self, results: list) -> None:
        """
        生成处理总结并保存到文件
        Args:
            results: 处理结果列表，每项格式为 (状态, 原文件名, 新文件名, 原因)
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary_path = os.path.join(self.target_folder, "处理总结.txt")
            
            success_count = sum(1 for r in results if r[0] == "成功")
            fail_count = sum(1 for r in results if r[0] == "失败")
            total_count = len(results)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                # 写入标题和时间
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
            
            # 用于记录运单号出现次数
            waybill_count = {}
            
            for idx, filename in enumerate(image_files, 1):
                try:
                    file_path = os.path.join(self.source_folder, filename)
                    logger.debug(f"处理文件: {filename}")
                    
                    # 识别运单号
                    waybill_number = self.scanner.scan_single(file_path, self.options)
                    logger.debug(f"识别结果: {waybill_number}")
                    
                    if waybill_number:
                        # 获取文件扩展名
                        _, ext = os.path.splitext(filename)
                        
                        # 更新运单号计数
                        if waybill_number in waybill_count:
                            waybill_count[waybill_number] += 1
                            new_filename = f"{waybill_number}-{waybill_count[waybill_number]}{ext}"
                        else:
                            waybill_count[waybill_number] = 1
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
            self.generate_summary(results)
            
            # 发送完成信号
            logger.info(f"处理完成: 成功 {success_count}, 失败 {fail_count}")
            self.process_finished.emit(success_count, fail_count)
                
        except Exception as e:
            logger.error(f"处理线程运行失败: {str(e)}")
            self.process_finished.emit(0, 0)

class RegionSelectDialog(QDialog):
    """识别区域选择对话框"""
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.selected_region = None
        self.start_pos = None
        self.current_pos = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("选择识别区域")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 图片标签
        self.image_label = QLabel()
        self.pixmap = QPixmap(self.image_path)
        self.image_label.setPixmap(self.pixmap)
        layout.addWidget(self.image_label)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # 设置鼠标跟踪
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.mousePressEvent
        self.image_label.mouseMoveEvent = self.mouseMoveEvent
        self.image_label.mouseReleaseEvent = self.mouseReleaseEvent
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.current_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.start_pos:
            self.current_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton and self.start_pos:
            # 计算相对坐标
            img_width = self.pixmap.width()
            img_height = self.pixmap.height()
            
            x1 = min(self.start_pos.x(), self.current_pos.x()) / img_width
            y1 = min(self.start_pos.y(), self.current_pos.y()) / img_height
            x2 = max(self.start_pos.x(), self.current_pos.x()) / img_width
            y2 = max(self.start_pos.y(), self.current_pos.y()) / img_height
            
            self.selected_region = {
                'x1': max(0, min(1, x1)),
                'y1': max(0, min(1, y1)),
                'x2': max(0, min(1, x2)),
                'y2': max(0, min(1, y2))
            }
            
            self.start_pos = None
            self.current_pos = None
            self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)
        painter = QPainter(self)
        
        # 绘制选择框
        if self.start_pos and self.current_pos:
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(2)
            painter.setPen(pen)
            
            x = min(self.start_pos.x(), self.current_pos.x())
            y = min(self.start_pos.y(), self.current_pos.y())
            w = abs(self.current_pos.x() - self.start_pos.x())
            h = abs(self.current_pos.y() - self.start_pos.y())
            
            painter.drawRect(x, y, w, h)

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.selected_region = None
        self.process_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("运单号识别工具 - 作者 永互物流 fgwljd@126.com")
        self.setMinimumSize(800, 600)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # === 识别设置组 ===
        recognition_group = QGroupBox("识别设置")
        recognition_layout = QVBoxLayout()
        
        # 识别方式
        method_layout = QHBoxLayout()
        self.barcode_cb = QCheckBox("条形码")
        self.qrcode_cb = QCheckBox("二维码")
        self.text_cb = QCheckBox("文字")
        method_layout.addWidget(self.barcode_cb)
        method_layout.addWidget(self.qrcode_cb)
        method_layout.addWidget(self.text_cb)
        recognition_layout.addLayout(method_layout)
        
        # 腾讯云OCR设置
        tencent_group = QGroupBox("腾讯云OCR设置")
        tencent_layout = QVBoxLayout()
        
        # 第一行：复选框和保存按钮并排
        first_row = QHBoxLayout()
        self.use_tencent_cb = QCheckBox("使用腾讯云OCR处理识别失败的图片")
        self.save_tencent_btn = QPushButton("保存密钥")
        first_row.addWidget(self.use_tencent_cb)
        first_row.addWidget(self.save_tencent_btn)
        tencent_layout.addLayout(first_row)
        
        # Secret ID
        secret_id_layout = QHBoxLayout()
        secret_id_layout.addWidget(QLabel("Secret ID:"))
        self.secret_id_input = QLineEdit()
        self.secret_id_input.setPlaceholderText("没有密钥取消上方的勾也可以使用，只是识别率偏低，填写密钥时注意不要复制到空格")
        secret_id_layout.addWidget(self.secret_id_input)
        tencent_layout.addLayout(secret_id_layout)
        
        # Secret Key
        secret_key_layout = QHBoxLayout()
        secret_key_layout.addWidget(QLabel("Secret Key:"))
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)  # 密码模式显示
        secret_key_layout.addWidget(self.secret_key_input)
        tencent_layout.addLayout(secret_key_layout)
        
        tencent_group.setLayout(tencent_layout)
        recognition_layout.addWidget(tencent_group)
        
        # 识别区域
        region_layout = QHBoxLayout()
        region_layout.addWidget(QLabel("识别区域:"))
        self.full_image_cb = QCheckBox("全图")
        self.custom_region_cb = QCheckBox("自定义区域")
        self.select_region_btn = QPushButton("选择区域")
        region_layout.addWidget(self.full_image_cb)
        region_layout.addWidget(self.custom_region_cb)
        region_layout.addWidget(self.select_region_btn)
        recognition_layout.addLayout(region_layout)
        
        recognition_group.setLayout(recognition_layout)
        layout.addWidget(recognition_group)
        
        # === 单号设置组 ===
        waybill_group = QGroupBox("运单号设置")
        waybill_layout = QVBoxLayout()
        
        # 运单号长度范围
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("运单号长度范围:"))
        self.min_length_input = QSpinBox()
        self.min_length_input.setMinimum(1)
        self.min_length_input.setMaximum(100)
        length_layout.addWidget(self.min_length_input)
        length_layout.addWidget(QLabel("至"))
        self.max_length_input = QSpinBox()
        self.max_length_input.setMinimum(1)
        self.max_length_input.setMaximum(100)
        length_layout.addWidget(self.max_length_input)
        waybill_layout.addLayout(length_layout)
        
        # 运单号字符构成
        chars_layout = QVBoxLayout()
        chars_layout.addWidget(QLabel("运单号字符构成:"))
        self.uppercase_cb = QCheckBox("大写字母 (A-Z)")
        self.lowercase_cb = QCheckBox("小写字母 (a-z)")
        self.digits_cb = QCheckBox("数字 (0-9)")
        chars_layout.addWidget(self.uppercase_cb)
        chars_layout.addWidget(self.lowercase_cb)
        chars_layout.addWidget(self.digits_cb)
        
        custom_chars_layout = QHBoxLayout()
        custom_chars_layout.addWidget(QLabel("自定义字符:"))
        self.custom_chars_input = QLineEdit()
        custom_chars_layout.addWidget(self.custom_chars_input)
        chars_layout.addLayout(custom_chars_layout)
        waybill_layout.addLayout(chars_layout)
        
        # 运单号特征
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("起始字符:"))
        self.prefix_input = QLineEdit()
        prefix_layout.addWidget(self.prefix_input)
        waybill_layout.addLayout(prefix_layout)
        
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("结束字符:"))
        self.suffix_input = QLineEdit()
        suffix_layout.addWidget(self.suffix_input)
        waybill_layout.addLayout(suffix_layout)
        
        waybill_group.setLayout(waybill_layout)
        layout.addWidget(waybill_group)
        
        # === 文夹设置组 ===
        folder_group = QGroupBox("文件夹设置")
        folder_layout = QVBoxLayout()
        
        # 源文件夹
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("待处理文件夹:"))
        self.source_input = QLineEdit()
        self.source_btn = QPushButton("浏览")
        source_layout.addWidget(self.source_input)
        source_layout.addWidget(self.source_btn)
        folder_layout.addLayout(source_layout)
        
        # 目标文件夹
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("目标文件夹:"))
        self.target_input = QLineEdit()
        self.target_btn = QPushButton("浏览")
        target_layout.addWidget(self.target_input)
        target_layout.addWidget(self.target_btn)
        folder_layout.addLayout(target_layout)
        
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # === 进度显示 ===
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("待开始...")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # === 控制按钮 ===
        self.start_btn = QPushButton("开始处理")
        layout.addWidget(self.start_btn)
        
        # 设置默认值
        self.setup_defaults()
        
        # 绑定事件
        self.setup_connections()
    
    def setup_defaults(self):
        """设置默认值"""
        # 识别方式默认全选
        self.barcode_cb.setChecked(True)
        self.qrcode_cb.setChecked(True)
        self.text_cb.setChecked(True)
        
        # 默认全图识别
        self.full_image_cb.setChecked(True)
        self.select_region_btn.setEnabled(False)
        
        # 运单号长度默认值
        self.min_length_input.setValue(8)
        self.max_length_input.setValue(12)
        
        # 运单号字符默认值
        self.uppercase_cb.setChecked(True)
        self.digits_cb.setChecked(True)
        
        # 运单号特征默认值
        self.prefix_input.setText("YS")
        
        # 加载腾讯云配置
        config_path = 'config.json'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    tencent_config = config.get('tencent_ocr', {})
                    self.use_tencent_cb.setChecked(tencent_config.get('enabled', False))
                    self.secret_id_input.setText(tencent_config.get('secret_id', ''))
                    self.secret_key_input.setText(tencent_config.get('secret_key', ''))
            except Exception as e:
                logger.error(f"读取配置文件失: {str(e)}")
    
    def setup_connections(self):
        """设置信号连接"""
        # 文件夹选择
        self.source_btn.clicked.connect(self.select_source_folder)
        self.target_btn.clicked.connect(self.select_target_folder)
        
        # 识别区域设置
        self.full_image_cb.toggled.connect(self.toggle_region_selection)
        self.custom_region_cb.toggled.connect(self.toggle_region_selection)
        self.select_region_btn.clicked.connect(self.select_region)
        
        # 开始处理
        self.start_btn.clicked.connect(self.start_process)
        self.save_tencent_btn.clicked.connect(self.save_tencent_config)
    
    def select_source_folder(self):
        """选择源文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择待处理文件夹")
        if folder:
            # 确保路径使用正确的编码
            self.source_input.setText(folder)
    
    def select_target_folder(self):
        """选择目标文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if folder:
            # 确保路径使用正确的编码
            self.target_input.setText(folder)
    
    def toggle_region_selection(self, checked):
        """切换识别区域选择"""
        if self.sender() == self.full_image_cb and checked:
            self.custom_region_cb.setChecked(False)
            self.select_region_btn.setEnabled(False)
            self.selected_region = None
        elif self.sender() == self.custom_region_cb and checked:
            self.full_image_cb.setChecked(False)
            self.select_region_btn.setEnabled(True)
    
    def select_region(self):
        """选择识别区域"""
        if not self.source_input.text():
            QMessageBox.warning(self, "警告", "请先选择待处理文件夹！")
            return
        
        # 获取第一个图片文件
        image_files = [
            f for f in os.listdir(self.source_input.text())
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        if not image_files:
            QMessageBox.warning(self, "警告", "待处理文件夹中没有图片文件")
            return
        
        image_path = os.path.join(self.source_input.text(), image_files[0])
        dialog = RegionSelectDialog(image_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_region = dialog.selected_region
    
    def start_process(self):
        """开始处理"""
        try:
            # 获取源文件夹和目标文件夹
            source_folder = self.source_input.text()
            target_folder = self.target_input.text()
            
            if not self.validate_inputs():
                return
            
            # 获取识别选项
            options = {
                'scan_text': self.text_cb.isChecked(),
                'use_tencent': self.use_tencent_cb.isChecked(),
                'scan_barcode': self.barcode_cb.isChecked(),
                'scan_qrcode': self.qrcode_cb.isChecked(),
                'min_length': self.min_length_input.value(),
                'max_length': self.max_length_input.value(),
                'prefix': self.prefix_input.text(),
                'suffix': self.suffix_input.text(),
                'region': self.selected_region if self.custom_region_cb.isChecked() else None
            }
            
            logger.info(f"开始处理，选项: {options}")
            
            # 禁用开始按钮
            self.start_btn.setEnabled(False)
            self.status_label.setText("正在处理...")
            
            # 创建并启动处理线程
            self.process_thread = ProcessThread(source_folder, target_folder, options)
            self.process_thread.progress_updated.connect(self.update_progress)
            self.process_thread.process_finished.connect(self.process_finished)
            self.process_thread.start()
            
        except Exception as e:
            logger.error(f"启动处理失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"启动处理失败: {str(e)}")
            self.start_btn.setEnabled(True)
    
    def validate_inputs(self):
        """验证输入"""
        # 检查文件夹
        if not self.source_input.text() or not self.target_input.text():
            QMessageBox.warning(self, "警告", "请选择源文件夹和目标文件夹！")
            return False
        
        # 检查识别方式
        if not any([
            self.barcode_cb.isChecked(),
            self.qrcode_cb.isChecked(),
            self.text_cb.isChecked()
        ]):
            QMessageBox.warning(self, "警告", "请至少选择一种识别方式！")
            return False
        
        # 检查运单号长度
        if self.min_length_input.value() > self.max_length_input.value():
            QMessageBox.warning(self, "警告", "最小长度不能大于最大长度！")
            return False
        
        # 检查字符选项
        if not any([
            self.uppercase_cb.isChecked(),
            self.lowercase_cb.isChecked(),
            self.digits_cb.isChecked(),
            self.custom_chars_input.text()
        ]):
            QMessageBox.warning(self, "警告", "请至少选择一种允许的字符类型！")
            return False
        
        return True
    
    def update_progress(self, current, total, filename):
        """���新进度"""
        try:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"正在处理: {filename}")
            QApplication.processEvents()
        except Exception as e:
            logger.error(f"更新进度失败: {str(e)}")
    
    def process_finished(self, success_count, fail_count):
        """处理完成"""
        try:
            self.start_btn.setEnabled(True)
            self.status_label.setText("处理完成")
            self.progress_bar.setValue(100)
            
            QMessageBox.information(
                self,
                "完成",
                f"处理完成！\n"
                f"成功：{success_count}\n"
                f"失败：{fail_count}"
            )
        except Exception as e:
            logger.error(f"显示结果失败: {str(e)}")
    
    def save_tencent_config(self):
        """保存腾讯云OCR配置"""
        try:
            secret_id = self.secret_id_input.text().strip()
            secret_key = self.secret_key_input.text().strip()
            
            if not secret_id or not secret_key:
                QMessageBox.warning(self, "警告", "请填写完整的Secret ID和Secret Key！")
                return
            
            # 获取可执行文件所在目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                app_dir = os.path.dirname(sys.executable)
            else:
                # 如果是开发环境
                app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            config_path = os.path.join(app_dir, 'config.json')
            
            try:
                # 如果配置文件存在，先读取现有配置
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                else:
                    config = {}
                
                # 更新腾讯云配置
                config['tencent_ocr'] = {
                    'enabled': self.use_tencent_cb.isChecked(),
                    'secret_id': secret_id,
                    'secret_key': secret_key
                }
                
                # 尝试写入配置文件
                try:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=4, ensure_ascii=False)
                    QMessageBox.information(self, "成功", "腾讯云OCR配置已保存！")
                    logger.info("腾讯云OCR配置已保存")
                except PermissionError:
                    # 如果没有写入权限，尝试使用临时文件
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    temp_config_path = os.path.join(temp_dir, 'waybill_config.json')
                    
                    with open(temp_config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=4, ensure_ascii=False)
                    
                    # 使用 shutil 复制文件（这可能需要管理员权限）
                    import shutil
                    shutil.copy2(temp_config_path, config_path)
                    os.remove(temp_config_path)
                    
                    QMessageBox.information(self, "成功", "腾讯云OCR配置已保存！")
                    logger.info("腾讯云OCR配置已通过临时文件保存")
                    
            except Exception as e:
                error_msg = f"保存配置文件失败: {str(e)}"
                logger.error(error_msg)
                
                # 尝试保存到用户目录
                user_config_path = os.path.join(os.path.expanduser('~'), 'waybill_config.json')
                with open(user_config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                
                QMessageBox.warning(
                    self,
                    "警告",
                    f"无法保存到程序目录，配置已保存到：{user_config_path}\n"
                    "建议以管理员身份运行程序。"
                )
                logger.info(f"配置已保存到用户目录: {user_config_path}")
                
        except Exception as e:
            error_msg = f"保存腾讯云OCR配置失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)