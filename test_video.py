import cv2

video = cv2.VideoCapture("testvideo1.mp4")
fps = video.get(cv2.CAP_PROP_FPS)
print("FPS:", fps) 

while True:
    success, frame = video.read()

    if not success:
        break

    cv2.imshow("Video", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video.release()
cv2.destroyAllWindows()