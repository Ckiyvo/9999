import cv2
import os
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import numpy as np


def preprocess_video(video_path, output_folder):
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # 每 4 帧提取一次（可根据需要调整）
        if frame_count % 4 == 0:
            # 图像增强：这里简单地进行直方图均衡化
            if len(frame.shape) == 3:
                # 如果是彩色图像，将其转换为 YUV 颜色空间
                yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
                yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
                frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
            else:
                # 如果是灰度图像，直接进行直方图均衡化
                frame = cv2.equalizeHist(frame)
            # 调整帧的大小为 224x224
            frame = cv2.resize(frame, (224, 224))

            # 保存帧为 PNG 图片
            image_path = os.path.join(output_folder, f"frame_{frame_count:04d}.png")
            cv2.imwrite(image_path, frame)

        frame_count += 1

    cap.release()
    return output_folder


action_recog_model_path = r"F:\a\apaper\project\project\algorithm\cv_TAdaConv_action-recognition"

recognition_pipeline = pipeline(Tasks.action_recognition, model=action_recog_model_path)

# 本地视频文件路径，你可以根据实际情况修改
local_video_path = 'https://modelscope.oss-cn-beijing.aliyuncs.com/test/videos/action_detection_test_video.mp4'
# 输出图片文件夹路径
output_folder = r"F:\a\apaper\project\project\algorithm\output_frames"

# 进行视频预处理
preprocessed_folder = preprocess_video(local_video_path, output_folder)

result = recognition_pipeline(local_video_path)

print(f'recognition output: {result}.')