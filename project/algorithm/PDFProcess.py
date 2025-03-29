import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from doclayout_yolo import YOLOv10
import supervision as sv
from paddleocr import PaddleOCR
import json

# 加载预训练模型
model_path = r"F:\a\apaper\project\project\algorithm\doclayout_yolo_docstructbench_imgsz1024.pt"
layout_model = YOLOv10(model_path)

# 定义具体的分类标签
CLASS_LABELS = {
    0: "Title",
    1: "Plain Text",
    2: "Abandoned Text",
    3: "Figure",
    4: "Figure Caption",
    5: "Table",
    6: "Table Caption",
    7: "Table Footnote",
    8: "Isolated Formula",
    9: "Formula Caption",
}

# 初始化 PaddleOCR，设置语言为支持中文和英文
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# 解析PDF文档
def pdf_to_image(pdf_path):
    """
    将PDF文件的每一页转换为清晰的图像数组
    :param pdf_path: PDF文件的路径
    :return: 包含每一页图像数组的列表
    """
    doc = fitz.open(pdf_path)
    images = []
    # 提高图像分辨率，这里将缩放因子设置为2，可根据实际情况调整
    zoom_x = 2.0
    zoom_y = 2.0
    mat = fitz.Matrix(zoom_x, zoom_y)
    for page in doc:
        # 使用矩阵进行缩放
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(np.array(img))
    return images

# 布局检测
def layout_detection(images):
    """
    对图像进行布局检测
    :param images: 包含图像数组的列表
    :return: 包含检测结果和标注后图像的列表
    """
    all_detections = []
    for i, image in enumerate(images):
        # 执行推理
        results = layout_model(source=image, conf=0.25, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)

        # 创建 BoxAnnotator 实例，设置文本样式
        box_annotator = sv.BoxAnnotator(
            color=sv.Color.default(),
            text_color=sv.Color.from_hex("#FFFFFF"),
            text_scale=0.3,
            text_thickness=1,
            text_padding=5
        )

        # 生成标签
        labels = []
        for class_id, confidence in zip(detections.class_id, detections.confidence):
            if class_id in CLASS_LABELS:
                label = f"{CLASS_LABELS[class_id]} {confidence:.2f}"
            else:
                label = f"未知类别 {confidence:.2f}"
            labels.append(label)

        # 注释图像，同时添加标签
        annotated_image = box_annotator.annotate(
            scene=image.copy(),
            detections=detections,
            labels=labels
        )

        all_detections.append({
            "detections": detections,
            "annotated_image": annotated_image,
            "page_info": {
                "page_no": i,
                "height": image.shape[0],
                "width": image.shape[1]
            }
        })
    return all_detections

# OCR 识别
def ocr_recognition(all_detections, images):
    """
    对布局检测结果进行 OCR 识别
    :param all_detections: 包含检测结果和标注后图像的列表
    :param images: 包含图像数组的列表
    :return: 包含识别结果和标注后图像的列表
    """
    all_results = []
    for i, detection_info in enumerate(all_detections):
        detections = detection_info["detections"]
        image = images[i]
        annotated_image = detection_info["annotated_image"]
        page_info = detection_info["page_info"]

        # 提取布局内容
        page_results = []
        unique_texts = set()
        # 按检测框的上边界坐标进行排序
        sorted_indices = np.argsort(detections.xyxy[:, 1])
        for index in sorted_indices:
            xyxy = detections.xyxy[index]
            class_id = detections.class_id[index]
            x1, y1, x2, y2 = map(int, xyxy)
            layout_image = image[y1:y2, x1:x2]
            layout_type = CLASS_LABELS.get(class_id, "未知类别")

            if layout_type in ["Plain Text", "Title", "Abandoned Text", "Figure Caption", "Table Caption", "Table Footnote", "Formula Caption"]:
                result = ocr.ocr(layout_image, cls=True)
                if result and result[0]:
                    full_text = " ".join([line[1][0] for line in result[0]])
                    score = max([line[1][1] for line in result[0]])  # 取最高置信度
                    if full_text not in unique_texts:
                        unique_texts.add(full_text)
                        page_results.append({
                            "category_type": layout_type.lower().replace(" ", "_"),
                            "poly": [x1, y1, x2, y1, x2, y2, x1, y2],
                            "text": full_text,
                            "score": score
                        })
            elif layout_type == "Figure":
                # 保存图片
                Image.fromarray(layout_image).save(f"page_{i + 1}_figure_{x1}_{y1}.png")
            elif layout_type == "Table":
                result = ocr.ocr(layout_image, cls=True)
                if result and result[0]:
                    full_text = " ".join([line[1][0] for line in result[0]])
                    score = max([line[1][1] for line in result[0]])  # 取最高置信度
                    if full_text not in unique_texts:
                        unique_texts.add(full_text)
                        page_results.append({
                            "category_type": "table",
                            "poly": [x1, y1, x2, y1, x2, y2, x1, y2],
                            "text": full_text,
                            "score": score
                        })

        all_results.append({
            "layout_dets": page_results,
            "page_info": page_info,
            "annotated_image": annotated_image
        })
    return all_results


# 展示结果并导出为 JSON
def show_results(all_results):
    """
    打印所有识别结果并将其导出为 JSON 格式
    :param all_results: 包含每一页识别结果和标注后图像的列表
    """
    json_data = []
    for result in all_results:
        page_no = result["page_info"]["page_no"]
        # 保存标注后的图片
        annotated_image = Image.fromarray(result["annotated_image"])
        annotated_image.save(f"page_{page_no + 1}_annotated.png")

        # 准备 JSON 数据
        json_result = {
            "layout_dets": result["layout_dets"],
            "page_info": result["page_info"]
        }
        json_data.append(json_result)

    json_output = json.dumps(json_data, ensure_ascii=False, indent=4)
    print(json_output)
    with open('output.json', 'w', encoding='utf-8') as f:
        f.write(json_output)

# 主程序
if __name__ == "__main__":
    pdf_path = r'F:\a\apaper\project\project\algorithm\pdf_test.pdf'
    images = pdf_to_image(pdf_path)
    detections = layout_detection(images)
    results = ocr_recognition(detections, images)
    show_results(results)