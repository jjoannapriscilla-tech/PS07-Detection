import math


class PersonTracker:
    def __init__(self, max_distance=100, max_missing=10):
        self.next_id = 1
        self.tracks = {}
        self.max_distance = max_distance
        self.max_missing = max_missing

    def _get_center(self, box):
        x1, y1, x2, y2 = box
        return (x1 + x2) / 2, (y1 + y2) / 2

    def _distance(self, point1, point2):
        return math.sqrt(
            (point1[0] - point2[0]) ** 2 +
            (point1[1] - point2[1]) ** 2
        )

    def _iou(self, box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection_width = max(0, x2 - x1)
        intersection_height = max(0, y2 - y1)

        intersection = intersection_width * intersection_height

        area1 = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
        area2 = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])

        union = area1 + area2 - intersection

        if union == 0:
            return 0

        return intersection / union

    def update(self, detections):

        new_tracks = {}
        used_ids = set()

        # Match current detections with existing tracks
        for detection in detections:

            box = detection["box"]
            center = self._get_center(box)

            best_id = None
            best_score = float("inf")

            for track_id, track in self.tracks.items():

                if track_id in used_ids:
                    continue

                distance = self._distance(
                    center,
                    track["center"]
                )

                iou = self._iou(
                    box,
                    track["box"]
                )

                # Match if either the box overlaps
                # or the person has moved within the allowed distance
                if iou > 0.1 or distance <= self.max_distance:

                    # Prefer matching boxes with higher overlap
                    score = distance - (iou * 100)

                    if score < best_score:
                        best_score = score
                        best_id = track_id

            # No existing person matched
            if best_id is None:

                best_id = self.next_id
                self.next_id += 1

            used_ids.add(best_id)

            new_tracks[best_id] = {
                "center": center,
                "box": box,
                "missing": 0
            }

            detection["track_id"] = best_id

        # Keep old tracks briefly when a person is missed
        for track_id, track in self.tracks.items():

            if track_id not in used_ids:

                track["missing"] += 1

                if track["missing"] <= self.max_missing:
                    new_tracks[track_id] = track

        self.tracks = new_tracks

        return detections