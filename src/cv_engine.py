import cv2
import numpy as np
import time
from ultralytics import YOLO
from src.logger import log_algorithm

class CVEngine:
    def __init__(self):
        self.yolo_model = None
        # Initialize YOLOv8 Medium (High precision for Industry Grade detection)
        try:
            self.yolo_model = YOLO('yolov8m.pt')
        except Exception as e:
            print(f"Error loading YOLO model: {e}")

    def preprocess(self, image, mode='gray', blur_kernel=5, binary_thresh=0):
        """Standard preprocessing operations."""
        start_time = time.time()
        if mode == 'gray':
            processed = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif mode == 'blur':
            processed = cv2.GaussianBlur(image, (blur_kernel, blur_kernel), 0)
        elif mode == 'binary' and binary_thresh > 0:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, processed = cv2.threshold(gray, binary_thresh, 255, cv2.THRESH_BINARY)
        elif mode == 'normalize':
            normalized = np.zeros(image.shape)
            processed = cv2.normalize(image, normalized, 0, 255, cv2.NORM_MINMAX)
        else:
            processed = image
        
        log_algorithm(f"Preprocess_{mode}", {"kernel": blur_kernel}, time.time() - start_time)
        return processed

    def edge_detection(self, image, method='canny', low_thresh=100, high_thresh=200, kernel_size=3):
        """Edge detection algorithms with enhanced industrial thresholds."""
        start_time = time.time()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        if method == 'canny':
            # Industry Standard: L2 Gradient for better precision
            output = cv2.Canny(gray, low_thresh, high_thresh, L2gradient=True)
        elif method == 'sobel':
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=kernel_size)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=kernel_size)
            output = cv2.magnitude(sobelx, sobely)
            output = np.uint8(np.absolute(output))
        elif method == 'laplacian':
            output = cv2.Laplacian(gray, cv2.CV_64F, ksize=kernel_size)
            output = np.uint8(np.absolute(output))
        else:
            output = gray
            
        log_algorithm(f"Edge_{method}", {"low": low_thresh, "high": high_thresh}, time.time() - start_time)
        return output

    def feature_detection(self, image, method='orb', n_features=500):
        """Detect and draw keypoints with sub-pixel refinement."""
        start_time = time.time()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        if method == 'sift':
            sift = cv2.SIFT_create(nfeatures=n_features)
            kp, des = sift.detectAndCompute(gray, None)
        elif method == 'orb':
            # Industry Standard: Using 8 levels for better scale invariance
            orb = cv2.ORB_create(nfeatures=n_features, nlevels=8, edgeThreshold=31)
            kp, des = orb.detectAndCompute(gray, None)
        elif method == 'harris':
            dst = cv2.cornerHarris(gray, 2, 3, 0.04)
            dst = cv2.dilate(dst, None)
            corners = np.argwhere(dst > 0.01 * dst.max())
            # Sub-pixel refinement
            corners = np.float32(corners)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
            refined_corners = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), criteria)
            kp = [cv2.KeyPoint(x=float(p[1]), y=float(p[0]), size=1) for p in refined_corners]
            des = None
        else:
            kp, des = [], None

        output_img = cv2.drawKeypoints(image, kp, None, color=(0, 255, 0), flags=cv2.DrawMatchesFlags_DRAW_RICH_KEYPOINTS)
        
        metrics = {"keypoints": len(kp)}
        log_algorithm(f"Feature_{method}", metrics, time.time() - start_time)
        return output_img, metrics

    def feature_matching(self, img1, img2, method='orb_bf'):
        """Match features between two images with Lowe's ratio filtering."""
        start_time = time.time()
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        if 'orb' in method:
            orb = cv2.ORB_create(nfeatures=1000)
            kp1, des1 = orb.detectAndCompute(gray1, None)
            kp2, des2 = orb.detectAndCompute(gray2, None)
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False) # CrossCheck=False for KNN
            matches = bf.knnMatch(des1, des2, k=2)
            # Lowe's Ratio Test (Accuracy focus)
            good_matches = []
            for m, n in matches:
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)
        else:
            sift = cv2.SIFT_create()
            kp1, des1 = sift.detectAndCompute(gray1, None)
            kp2, des2 = sift.detectAndCompute(gray2, None)
            flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
            matches = flann.knnMatch(des1, des2, k=2)
            good_matches = []
            for m, n in matches:
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)
        
        output_img = cv2.drawMatches(img1, kp1, img2, kp2, good_matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        
        metrics = {"matches": len(good_matches)}
        log_algorithm(f"Matching_{method}", metrics, time.time() - start_time)
        return output_img, metrics

    def segmentation(self, image, method='kmeans', k=3):
        """Precision Image Segmentation."""
        start_time = time.time()
        if method == 'kmeans':
            pixel_values = image.reshape((-1, 3)).astype(np.float32)
            # Higher precision criteria
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
            _, labels, centers = cv2.kmeans(pixel_values, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
            centers = np.uint8(centers)
            segmented_data = centers[labels.flatten()]
            output = segmented_data.reshape(image.shape)
        elif method == 'watershed':
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            kernel = np.ones((3,3), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            sure_bg = cv2.dilate(opening, kernel, iterations=3)
            dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
            ret, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
            sure_fg = np.uint8(sure_fg)
            unknown = cv2.subtract(sure_bg, sure_fg)
            ret, markers = cv2.connectedComponents(sure_fg)
            markers = markers + 1
            markers[unknown == 255] = 0
            markers = cv2.watershed(image, markers)
            output = image.copy()
            output[markers == -1] = [255, 0, 0]
        else:
            output = image

        log_algorithm(f"Seg_{method}", {"k": k}, time.time() - start_time)
        return output

    def optical_flow(self, prev_frame, curr_frame, method='farneback'):
        """Optical flow calculation."""
        start_time = time.time()
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        if method == 'farneback':
            flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            hsv = np.zeros_like(prev_frame)
            hsv[..., 1] = 255
            hsv[..., 0] = ang * 180 / np.pi / 2
            hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
            output = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        else:
            output = curr_frame
        
        log_algorithm(f"Flow_{method}", {}, time.time() - start_time)
        return output

    def stereo_depth(self, left_img, right_img, method='bm', num_disparities=64, block_size=15):
        """High-precision Stereo Depth estimation."""
        start_time = time.time()
        left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
        right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)
        
        # Ensure num_disparities is a multiple of 16
        num_disparities = (num_disparities // 16) * 16
        if num_disparities <= 0: num_disparities = 16

        if method == 'bm':
            # Industry Standard BM tuning
            stereo = cv2.StereoBM_create(numDisparities=num_disparities, blockSize=block_size)
            stereo.setPreFilterType(1)
            stereo.setPreFilterSize(41)
            stereo.setPreFilterCap(31)
            stereo.setTextureThreshold(10)
            stereo.setUniquenessRatio(15)
        else:
            # High-precision SGBM
            stereo = cv2.StereoSGBM_create(
                minDisparity=0,
                numDisparities=num_disparities,
                blockSize=block_size,
                P1=8 * 3 * block_size**2,
                P2=32 * 3 * block_size**2,
                disp12MaxDiff=1,
                uniquenessRatio=10,
                speckleWindowSize=100,
                speckleRange=32
            )
            
        disparity = stereo.compute(left_gray, right_gray)
        disparity_norm = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        output = cv2.applyColorMap(disparity_norm, cv2.COLORMAP_JET)
        
        log_algorithm(f"Depth_{method}", {"numDisparities": num_disparities, "blockSize": block_size}, time.time() - start_time)
        return output

    def object_detection(self, image, conf_thresh=0.25):
        """Precision Object Detection using YOLOv8 Medium."""
        start_time = time.time()
        if self.yolo_model is None:
            return image, {"error": "Model not loaded"}
        
        # High-accuracy inference
        results = self.yolo_model(image, conf=conf_thresh, imgsz=640)[0]
        output_img = results.plot()
        
        metrics = {"objects": len(results.boxes)}
        log_algorithm("ObjectDetection_YOLO", metrics, time.time() - start_time)
        return output_img, metrics

engine = CVEngine()
