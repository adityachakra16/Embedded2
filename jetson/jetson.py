import sys
import os
import argparse
import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
import cv2
import numpy as np
import warnings
import time
from torch.autograd import Variable
from PIL import Image
from data import BaseTransform
from ssd import build_ssd
from CodeAES import encryption
#from CodeAES import encrypt, decrypt

warnings.filterwarnings("once")
THRES = 600

parser = argparse.ArgumentParser(description='Single Shot MultiBox Detection')
parser.add_argument('--trained_model', default='ssd300_WIDER_400.pth',
                    type=str, help='Trained state_dict file path to open')
parser.add_argument('--save_folder', default='eval/', type=str,
                    help='Dir to save results')
parser.add_argument('--visual_threshold', default=0.6, type=float,
                    help='Final confidence threshold')
parser.add_argument('--cuda', default=True, type=bool,
                    help='Use cuda to train model')
parser.add_argument('--jetson', default=False, type=bool,
                    help='Running on Jetson')
parser.add_argument('-f', default=None, type=str, help="Dummy arg so we can load in Jupyter Notebooks")
args = parser.parse_args()

if args.cuda and torch.cuda.is_available():
    torch.set_default_tensor_type('torch.cuda.FloatTensor')
else:
    torch.set_default_tensor_type('torch.FloatTensor')

if not os.path.exists(args.save_folder):
    os.mkdir(args.save_folder)


def gstreamer_pipeline(capture_width=3280, capture_height=2464, display_width=820, display_height=616, framerate=21, flip_method=2):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (capture_width, capture_height, framerate, flip_method, display_width, display_height)
    )


if __name__ == '__main__':
	if args.jetson:
		cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
	else:
		cap = cv2.VideoCapture(0)

	if cap.isOpened():
		cv2.namedWindow("Face Detect", cv2.WINDOW_AUTOSIZE)

		# load net
		num_classes = 2 # +1 background
		net = build_ssd('test', 300, num_classes) # initialize SSD
		net.load_state_dict(torch.load(args.trained_model, map_location=torch.device('cpu')))
		net.eval()
		print('Finished loading model!')

		if args.cuda:
			net = net.cuda()
			cudnn.benchmark = True

		transformer = BaseTransform(net.size, (104, 117, 123))

        # Variables to control verbosity
		encrypt_status = 1
		decrypt_status = 1
		verbose = 0

		encryptor = encryption()

		while cv2.getWindowProperty("Face Detect", 0) >= 0:
			start_time = time.time()
			ret, image = cap.read()
			keyCode = cv2.waitKey(30) & 0xFF

			# Process input
			[h, w] = image.shape[:2]
			image = cv2.flip(image, 1)
			x = torch.from_numpy(transformer(image)[0]).permute(2, 0, 1)
			x = Variable(x.unsqueeze(0))

			if args.cuda:
				x = x.cuda()

            # Generate Detection
			y = net(x)
			detections = y.data

			end_time = time.time()

            # Scale each detection back up to the image
			scale = torch.Tensor([image.shape[1], image.shape[0],
                             image.shape[1], image.shape[0]])

            # Go through the boxes and keep only those with conf > threshold
			boxes = []
			j = 0
			while detections[0, 1, j, 0] >= 0.35:
				pt = (detections[0, 1, j, 1:]*scale).cpu().numpy()
				x1, y1, x2, y2 = pt
				if x2 - x1 < THRES and y2 - y1 < THRES: # Filter out the biggest box
					boxes.append((pt[0], pt[1], pt[2], pt[3]))
				j += 1

            # Draw bounding boxes
			for box in boxes:
				x1, y1, x2, y2 = box
				image= cv2.rectangle(image, (x1,y1), (x2,y2), (0, 0, 255), 2)

            # Encrypt Image
			if encrypt_status:
				image, IV  = encryptor.encrypt(boxes, image)

            # Encode Image


            # Decrypt Image
			if decrypt_status:
				image = encryptor.decrypt(boxes, image, IV)

            # Display FPS
			fps = 1 / (end_time - start_time)
			image = cv2.putText(image, 'fps: %.3f' % fps, (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0))

			cv2.imshow("Face Detect", image)

            # Process and update keycode
			if chr(keyCode) == 'q' or keyCode == 27:
				break
			if chr(keyCode) == 'e':
				encrypt_status = not encrypt_status
			if chr(keyCode) == 'd':
				decrypt_status = not decrypt_status
			if chr(keyCode) == 'v':
				verbose = not verbose

            # Print info if verbose
			if verbose:
				print(f"enc: {encrypt_status}, dec_stat: {decrypt_status}, conf: {detections[0, 1, j, 0]}", end="\r")

		cap.release()
		cv2.destroyAllWindows()
	else:
		print("Unable to open camera")
