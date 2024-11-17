# 回单整理器

一个用于识别运单号并自动重命名运单图片的工具。

## 功能特点

<img src="./images/path_settings.png" width="800" alt="软件主界面">
<p><em>运单号智能识别与重命名工具主界面</em></p>
</div>

## 版本历史

### v1.3
- 新增腾讯云OCR支持，大幅提高识别率
- 新增中文路径和文件名支持
- 新增相同运单号多张图片支持
- 优化用户界面和操作体验

### v1.2
- 基础版本功能

## 使用说明

### 2. 高度定制化的运单号设置
<div align="center">
<img src="./images/path_settings.png" width="600" alt="设置界面">
<p><em>灵活的运单号规则配置</em></p>
</div>

## 开发环境

- Python 3.11
- PyQt6
- OpenCV
- Tesseract OCR
- pyzbar
- 腾讯云SDK

### 1. 启动软件
<div align="center">
<img src="./images/processing.png" width="600" alt="启动界面">
<p><em>软件启动界面</em></p>
</div>

### 2. 配置识别参数
<div align="center">
<img src="./images/processing.png" width="700" alt="参数配置">
<p><em>识别参数配置界面</em></p>
</div>

### 3. 设置文件路径
<div align="center">
<img src="./images/path_settings.png" width="700" alt="路径设置">
<p><em>文件路径配置界面</em></p>
</div>

### 4. 开始处理
<div align="center">
<table>
  <tr>
    <td><img src="./images/processing.png" width="400" alt="处理中"></td>
    <td><img src="./images/complete.png" width="400" alt="处理完成"></td>
  </tr>
  <tr>
    <td align="center"><em>批量处理进行中</em></td>
    <td align="center"><em>处理完成界面</em></td>
  </tr>
</table>
</div>

### 5. 查看处理结果
<div align="center">
<img src="./images/results.png" width="700" alt="处理结果">
<p><em>处理结果统计界面</em></p>
</div>

## 🔧 常见问题解决

### 文字运单号识别准确率有待提高，处理速度有待多线程和GPU加速
<div align="center">
<table>
  <tr>
    <td><img src="./images/good_sample.png" width="300" alt="良好样本"></td>
    <td><img src="./images/bad_sample.png" width="300" alt="问题样本"></td>
  </tr>
  <tr>

  </tr>
</table>
</div>


## 联系方式

Email: fgwljd@126.com

Copyright © 2024 专注物流效率提升工具开发. All rights reserved.

版权所有 © 2024 永互物流
