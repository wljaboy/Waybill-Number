def process_image(self, image_path: str, options: Dict[str, Any]) -> Optional[str]:
    try:
        if options.get('use_tencent'):
            if not self.tencent:
                logger.warning("腾讯云OCR未初始化，跳过调用")
            else:
                logger.debug("开始调用腾讯云OCR")
                texts = self.tencent.recognize(image_path)
                if texts:
                    logger.info(f"腾讯云OCR识别到 {len(texts)} 条文本")
                    results.extend(texts) 