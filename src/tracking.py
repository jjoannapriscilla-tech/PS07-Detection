import math


class PersonTracker:
    def __init__(self, max_distance=50):
        self.next_id = 1
        self.tracks = {}
        self.max_distance = max_distance

    def _get_center(self, box):
        x1, y1, x2, y2 = box
        return (x1 + x2) / 2, (y1 + y2) / 2

    def _distance(self, point1, point2):
        return math.sqrt(
            (point1[0] - point2[0]) ** 2 +
            (point1[1] - point2[1]) ** 2
        )

    def update(self, detections):
        new_tracks = {}
        used_ids = set()

        for detection in detections:
            box = detection["box"]
            center = self._get_center(box)

            best_id = None
            best_distance = self.max_distance

            for track_id, old_center in self.tracks.items():
                if track_id in used_ids:
                    continue

                distance = self._distance(center, old_center)

                if distance < best_distance:
                    best_distance = distance
                    best_id = track_id

            if best_id is None:
                best_id = self.next_id
                self.next_id += 1

            used_ids.add(best_id)
            new_tracks[best_id] = center
            detection["track_id"] = best_id

        self.tracks = new_tracks

        return detections