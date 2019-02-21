#!/usr/bin/env python

import rospy
import cv2
import re
import sys
import numpy as np
from std_msgs.msg import String, Int8
from sensor_msgs.msg import CompressedImage, Image
# import hil_servoing.msg as msg
from cv_bridge import CvBridge, CvBridgeError
from python_qt_binding.QtCore import *
from python_qt_binding.QtGui import *
from python_qt_binding.QtWidgets import *

TEXT_WIDTH = 420
TEXT_HEIGHT = 150


class UDPGuiWidget(QWidget):
	#############################################################################################################
	# INITIALIZATION METHODS
	#############################################################################################################
	def __init__(self):
		# print(dir(msg))
		super(UDPGuiWidget, self).__init__()
		self.setWindowTitle("University of Alberta")
		self.setStyleSheet("background-color:rgba(150, 150, 150, 100%)")
		# global variables
		self.cvbridge = CvBridge()
		self.clicked_points = []
		self.step1_complete = False
		# setup subscribers and publishers
		sub_image = rospy.Subscriber("/camera/image_raw/compressed", CompressedImage, self.callback_camera, queue_size=10) # /udp/response/target_image
		sub_coarse = rospy.Subscriber("/udp/response/coarse_target", Int8, self.callback_coarse_target, queue_size=3)
		sub_fine = rospy.Subscriber("/udp/response/fine_target", Int8, self.callback_fine_target, queue_size=3)

		self.pub_fine_target = rospy.Publisher("/udp/command/fine_target", String, queue_size=1) #change to udp/request
		self.pub_coarse_target = rospy.Publisher("/udp/request/coarse_target", String, queue_size=1) 
		self.pub_req_fine = rospy.Publisher("/udp/request/require_image", Int8, queue_size=1) 

		self.initialize_widgets()

	def initialize_widgets(self):
		self.main_layout = QVBoxLayout()
		self.select_widget = QWidget()
		self.select_widget.setLayout(self.select_layout())
		self.main_layout.addWidget(self.select_widget)
		self.setLayout(self.main_layout)
		self.pen = QPen(Qt.magenta)
		self.pen.setCapStyle(Qt.RoundCap)
		self.pen.setJoinStyle(Qt.RoundJoin)
		self.pen.setWidth(10)
#############################################################################################################
# WIDGET METHODS
#############################################################################################################
	def send_command_button(self):
		if len(self.clicked_points) > 0:
			self.pub_coarse_target.publish(self.format_string(self.clicked_points))
			
	def acquire_image_button(self):
		print "Acquiring an image..."
		self.clicked_points = []
		self.pub_req_fine.publish(1)

	def select_layout(self):
		# layouts
		l = QVBoxLayout()
		layout = QHBoxLayout()
		grasp_layout = QHBoxLayout()
		step_layout = QVBoxLayout()
		msgs = []
		for i in range(5):
			m = QLabel()
			m.setWordWrap(True)
			m.setAlignment(Qt.AlignLeft)
			if i == 0 or i == 3:
				m.setStyleSheet("font-size: 32px")
			else:
				m.setStyleSheet("font-size: 22px")
			msgs.append(m)
		# title
		title_msg = QLabel()
		title_msg.setText("Long Range Teleoperation: Operator Side Console")
		title_msg.setWordWrap(True)
		title_msg.setStyleSheet("font-size: 36px")
		title_msg.setAlignment(Qt.AlignCenter)
		title_msg.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
		# MESSAGES
		msgs[0].setText("Step 1: Coarse Target Selection")
		msgs[1].setText("Click once in the image to select a target")
		msgs[2].setText("Select a grasping pose then press button below to send command")
		msgs[3].setText("Step 2: Visual Task Specification")
		msgs[4].setText("Please specify a task in the new image then send command")
		# CHECKBOXES
		cb0 = QCheckBox("Robot Online")
		cb0.setStyleSheet("color: rgba(0, 255, 0, 100%); background-color:rgba(150, 150, 150, 100%); font-size: 22px")
		cb0.setChecked(True)

		self.cb1 = QCheckBox("Target selected in telepresence interface")
		self.cb1.setStyleSheet("color: rgba(0, 255, 255, 100%); background-color:rgba(150, 150, 150, 100%); font-size: 22px")
		# icon = QIcon("green_button.png")
		# cb1.setIcon(QIcon("green_button.png"))
		# cb1.setStyleSheet('QCheckBox::indicator:checked:hover {image: url(green_button.png);}'
                   # 'QCheckBox::indicator:checked {image: url(green_button.png);}')
		# cb1.setChecked(True)
		cb2 = QCheckBox("Top")
		cb2.setStyleSheet("color: rgba(0, 255, 255, 100%); background-color:rgba(150, 150, 150, 100%); font-size: 22px")
		cb3 = QCheckBox("Left")
		cb3.setStyleSheet("color: rgba(0, 255, 255, 100%); background-color:rgba(150, 150, 150, 100%); font-size: 22px")
		cb4 = QCheckBox("Right")
		cb4.setStyleSheet("color: rgba(0, 255, 255, 100%); background-color:rgba(150, 150, 150, 100%); font-size: 22px")
		cb5 = QCheckBox("Front")
		cb5.setStyleSheet("color: rgba(0, 255, 255, 100%); background-color:rgba(150, 150, 150, 100%); font-size: 22px")

		grasp_layout.addWidget(cb2)
		grasp_layout.addWidget(cb3)
		grasp_layout.addWidget(cb4)
		grasp_layout.addWidget(cb5)

		self.cb6 = QCheckBox("Coarse target reached!")
		self.cb6.setStyleSheet("color: rgba(0, 255, 0, 100%); background-color:rgba(150, 150, 150, 100%); font-size: 22px")
		self.cb7 = QCheckBox("Visual task specification complete!")
		self.cb7.setStyleSheet("color: rgba(0, 255, 255, 100%); background-color:rgba(150, 150, 150, 100%); font-size: 22px")
		self.cb8 = QCheckBox("Task complete!")
		self.cb8.setStyleSheet("color: rgba(0, 255, 0, 100%); background-color:rgba(150, 150, 150, 100%); font-size: 22px; font-weight: bold")
		# BUTTONS
		img_button = QPushButton("Acquire an image from remote")
		img_button.clicked.connect(self.acquire_image_button)
		img_button.setStyleSheet("background-color: rgba(220, 220, 220, 50%); \
			selection-background-color: rgba(220, 220, 220, 50%); font-size: 28px")
		img_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

		publish_button = QPushButton("Send command to remote robot")
		publish_button.clicked.connect(self.send_command_button)
		publish_button.setStyleSheet("background-color: rgba(220, 220, 220, 50%); \
			selection-background-color: rgba(220, 220, 220, 50%); font-size: 28px")
		publish_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

		# image view
		self._view = QLabel()
		self._view.setAlignment(Qt.AlignCenter)
		self._view.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		self._view.mousePressEvent = self.mousePressEventCam

		step_layout.addWidget(msgs[0])
		step_layout.addWidget(msgs[1])
		step_layout.addWidget(self.cb1)
		step_layout.addWidget(msgs[2])
		step_layout.addLayout(grasp_layout)

		step_layout.addWidget(self.cb6)
		step_layout.addWidget(msgs[3])
		step_layout.addWidget(img_button)
		step_layout.addWidget(msgs[4])
		step_layout.addWidget(self.cb7)
		step_layout.addWidget(self.cb8)
		# step1_layout.addWidget(reset_button)
		layout.addLayout(step_layout)
		layout.addWidget(self._view)
		l.addWidget(title_msg)
		l.addWidget(cb0)
		l.addLayout(layout)
		l.addWidget(publish_button)
		return l

#############################################################################################################
# CALLBACK METHODS
#############################################################################################################
	def callback_camera(self, data):
		# self.pixmap = self.convert_img(data)
		pmap = self.convert_compressed_img(data)
		self.paint_pixmap(pmap)
		self._view.setPixmap(pmap)

	def callback_coarse_target(self, data):
		print "coarse target callback: ", data
		if data:
			self.cb6.setChecked(True)
			self.step1_complete = True

	def callback_fine_target(self, data):
		print "fine target callback: ", data
		if data:
			self.cb8.setChecked(True)

	def format_string(self, pt):
		return str(pt[0]) + " " + str(pt[1])
#############################################################################################################
# IMAGE METHODS
#############################################################################################################
	def paint_pixmap(self, pix):
		painter = QPainter(pix)
		if self.clicked_points:
			painter.setPen(self.pen)
			painter.drawPoint(self.clicked_points[0], self.clicked_points[1])

	def convert_img(self, data):
		try:
			frame = self.cvbridge.imgmsg_to_cv2(data, "rgb8")
		except CvBridgeError as e:
			print(e)
		image = QImage(
			frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
		pixmap = QPixmap.fromImage(image)
		return pixmap

	def convert_compressed_img(self, data):
		np_arr = np.fromstring(data.data, np.uint8)
		frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
		pixmap = QPixmap.fromImage(image)
		return pixmap

#############################################################################################################
# EVENT METHODS
#############################################################################################################
	def mousePressEventCam(self, event):
		if event.button() == 1:
			pos = self._view.mapFromGlobal(event.globalPos())
			self.clicked_points = [pos.x(), pos.y()]
			print self.clicked_points
			if self.step1_complete:
				self.cb7.setChecked(True)
			self.cb1.setChecked(True)
		elif event.button() == 2:
			self.clicked_points = []
			self.cb1.setChecked(False)
			self.cb7.setChecked(False)

	def keyPressEvent(self, QKeyEvent):
		key = QKeyEvent.key()
		if int(key) == 82:  # r
			self.reset()
		elif int(key) == 68:  # d
			self.debug()
		elif int(key) == 81:  # q
			sys.exit()
		else:
			print "Unknown key option: ", key
