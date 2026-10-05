# -*- coding: utf-8 -*-
"""
Created on Sun Oct  4 13:55:28 2026

@author: fatemeh
"""

import os
import sys
import time

import cv2

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from vision.hand_tracker import HandTracker


MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "models", "hand_landmarker.task",
)
CAMERA_INDEX = 0
FRAME_W, FRAME_H = 640, 480


def main():
    print("Loading model:", MODEL_PATH)
    tracker = HandTracker(MODEL_PATH, num_hands=1)
    print("Model loaded.")

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)

    if not cap.isOpened():
        print(f"ERROR: camera {CAMERA_INDEX} could not be opened.")
        return

    prev = time.time()
    fps = 0.0
    print("Press Q in the window to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("ERROR: failed to read frame.")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        hands = tracker.process(rgb)
        h, w = frame.shape[:2]

        for hand in hands:
            for (x, y, _z) in hand["landmarks"]:
                cx, cy = int(x * w), int(y * h)
                cv2.circle(frame, (cx, cy), 3, (0, 200, 0), -1)

            ix, iy = hand["index_tip"]
            cx, cy = int(ix * w), int(iy * h)
            cv2.circle(frame, (cx, cy), 12, (0, 0, 255), -1)
            cv2.putText(
                frame, f"({cx},{cy})", (cx + 15, cy - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,
            )

        now = time.time()
        dt = now - prev
        prev = now
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)
        cv2.putText(
            frame, f"FPS {fps:4.1f}  hands: {len(hands)}",
            (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2,
        )

        cv2.imshow("Hand Tracker Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()