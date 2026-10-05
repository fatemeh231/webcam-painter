import os
import math
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


INDEX_MCP = 5
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_TIP = 12
PINKY_MCP = 17


def _finger_length_ratio(pts, mcp_idx, tip_idx):
    mcp = pts[mcp_idx]
    tip = pts[tip_idx]
    pinky = pts[PINKY_MCP]

    finger_len = math.hypot(tip[0] - mcp[0], tip[1] - mcp[1])
    palm_width = math.hypot(pinky[0] - mcp[0], pinky[1] - mcp[1])

    if palm_width < 1e-6:
        return 0.0
    return finger_len / palm_width


class HandTracker:
    def __init__(self, model_path, num_hands=1):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.model_path = model_path
        self.num_hands = num_hands

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=num_hands,
            running_mode=vision.RunningMode.IMAGE,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def process(self, rgb_frame):
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )
        result = self.detector.detect(mp_image)

        hands = []
        if not result.hand_landmarks:
            return hands

        for hand_landmarks in result.hand_landmarks:
            pts = [(lm.x, lm.y, lm.z) for lm in hand_landmarks]
            hands.append({
                "landmarks": pts,
                "index_tip": (pts[INDEX_TIP][0], pts[INDEX_TIP][1]),
                "index_length_ratio": _finger_length_ratio(pts, INDEX_MCP, INDEX_TIP),
                "middle_length_ratio": _finger_length_ratio(pts, MIDDLE_MCP, MIDDLE_TIP),
            })
        return hands