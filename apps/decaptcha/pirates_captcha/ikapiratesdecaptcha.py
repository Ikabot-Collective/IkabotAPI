import cv2.dnn  # opencv-python-rolling==4.7.0.20230211
import numpy as np

onnx_model = "apps/decaptcha/pirates_captcha/yolov8n-ikariam-pirates-mAP-0_989.onnx"  # path to neural net


model: cv2.dnn.Net = cv2.dnn.readNetFromONNX(onnx_model)
CLASSES = [
    "B",
    "2",
    "D",
    "X",
    "5",
    "M",
    "W",
    "A",
    "7",
    "4",
    "N",
    "L",
    "P",
    "V",
    "J",
    "H",
    "C",
    "3",
    "U",
    "Q",
    "Y",
    "S",
    "T",
    "K",
    "R",
    "E",
    "G",
    "F",
]


def break_ikariam_pirate_captcha(input_image):
    """Does inference on the input image. Returns list of all detected objects
    Parameters
    ----------
    input_image : str
        Captcha image file object

    Returns
    -------
    detections : list
        List of detections. Each detection object has fields class_id : int, class_name : str, confidence : float, scale : float, boxes : list
        boxes is a list of 4 floats: left, top, width, height. For more information search for "YOLOv8" on the internet.
    """
    filestr = input_image.read()
    assert len(filestr) <= 50000, "File is too large"  # 50Kb max
    file_bytes = np.fromstring(filestr, np.uint8)
    original_image: np.ndarray = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    [height, width, _] = original_image.shape
    assert height <= 100 and width <= 500, "Image is too large"
    length = max((height, width))
    image = np.zeros((length, length, 3), np.uint8)
    image[0:height, 0:width] = original_image
    scale = length / 640
    blob = cv2.dnn.blobFromImage(
        image, scalefactor=1 / 255, size=(640, 640), swapRB=True
    )
    model.setInput(blob)
    outputs = model.forward()
    outputs = np.array([cv2.transpose(outputs[0])])
    rows = outputs.shape[1]
    boxes = []
    scores = []
    class_ids = []
    for i in range(rows):
        classes_scores = outputs[0][i][4:]
        (minScore, maxScore, minClassLoc, (x, maxClassIndex)) = cv2.minMaxLoc(
            classes_scores
        )
        if maxScore >= 0.25:
            box = [
                outputs[0][i][0] - (0.5 * outputs[0][i][2]),
                outputs[0][i][1] - (0.5 * outputs[0][i][3]),
                outputs[0][i][2],
                outputs[0][i][3],
            ]
            boxes.append(box)
            scores.append(maxScore)
            class_ids.append(maxClassIndex)
    result_boxes = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45, 0.5)
    detections = []
    for i in range(len(result_boxes)):
        index = result_boxes[i]
        box = boxes[index]
        detection = {
            "class_id": class_ids[index],
            "class_name": CLASSES[class_ids[index]],
            "confidence": scores[index],
            "box": box,
            "scale": scale,
        }
        detections.append(detection)
    detections.sort(key=lambda x: x["box"][0], reverse=False)
    return detections


def get_captcha_string(input_image):
    """Does inference on the input image. Returns captcha string
    Parameters
    ----------
    input_image : str
        path to captcha image

    Returns
    -------
    captcha : str
        Resulting string from inference on input_image
    """
    return "".join([r["class_name"] for r in break_ikariam_pirate_captcha(input_image)])
