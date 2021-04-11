import pyaudio
import wave
import cv2
import os
import pytesseract
from time import sleep
from picamera import PiCamera
from picamera.array import PiRGBArray
import RPi.GPIO as GPIO
from io import BytesIO
from PIL import Image as pImage
from pynput import keyboard
from pynput.keyboard import Key, Listener



DEBUG = True


def record_audio(filename, form = pyaudio.paInt16, chans = 1,samp_rate = 44100,chunk = 4096,record_secs = 5, dev_index = 1):
	'''
	Records audio from the USB mic using wav file format
	Param: filename--> string for the output file name
	*param:
		---- form: file format, DEFAULT pyaudio.paInt16
		---- chans: number of channels, DEFAULT 1 (mono files), for stereo use 2
		---- samp_rate: sampling rate, DEFAULT 44100 hz
		---- chunk: size of the in-memory steam packet, DEFAULT 4096
		---- record_secs: record duration, DEFAULT 5 seconds
		---- dev_index: index of the hardware module, retireved from list_devices(), DEFAULT 1
	'''
	wav_output_filename = filename + '.wav' # name of .wav file
	audio = pyaudio.PyAudio() # create pyaudio instantiation

	# create pyaudio stream
	stream = audio.open(format = form,rate = samp_rate,channels = chans, \
	                    input_device_index = dev_index,input = True, \
	                    frames_per_buffer=chunk)
	print("recording")
	frames = []

	# loop through stream and append audio chunks to frame array
	for ii in range(0,int((samp_rate/chunk)*record_secs)):
	    data = stream.read(chunk, exception_on_overflow = False)
	    frames.append(data)

	print("finished recording")

	# stop the stream, close it, and terminate the pyaudio instantiation
	stream.stop_stream()
	stream.close()
	audio.terminate()

	# save the audio frames as .wav file
	wavefile = wave.open(wav_output_filename,'wb')
	wavefile.setnchannels(chans)
	wavefile.setsampwidth(audio.get_sample_size(form))
	wavefile.setframerate(samp_rate)
	wavefile.writeframes(b''.join(frames))
	wavefile.close()

def play_audio(filename, form = pyaudio.paInt16,chans = 1, samp_rate = 44100, chunk = 4096, record_secs = 5, dev_index = 0):
	'''
	Plays .wav audio files,outputs to USB Sound card
	Param: filename--> string for the output file name
	*param:
		---- form: file format, DEFAULT pyaudio.paInt16
		---- chans: number of channels, DEFAULT 1 (mono files), for stereo use 2
		---- samp_rate: sampling rate, DEFAULT 44100 hz
		---- chunk: size of the in-memory steam packet, DEFAULT 4096
		---- record_secs: record duration, DEFAULT 5 seconds
		---- dev_index: index of the hardware module, retireved from list_devices(), DEFAULT 0
	'''

	wav_input_filename = filename + '.wav'


	# Open the sound file 
	wf = wave.open(wav_input_filename, 'rb')
	#print(wf.getnchannels())

	# Create an interface to PortAudio
	audio = pyaudio.PyAudio()

	stream = audio.open(format = audio.get_format_from_width(wf.getsampwidth()),
                channels = chans,
                rate = wf.getframerate(),
                output_device_index = dev_index,
                output = True)

	# Read data in chunks
	data = wf.readframes(chunk)

	# Play the sound by writing the audio data to the stream
	while data != (b''):
		#print(data)
		stream.write(data)
		data = wf.readframes(chunk)

	# Close and terminate the stream
	stream.close()
	audio.terminate()

def list_devices():
	'''
	This function lists all available audio I/O devices, required to get the 
	device Id for both play_audio() and record_audio()
	INPUT: None
	OUTPUT: None
	'''
	p = pyaudio.PyAudio()
	for i in range(p.get_device_count()):
		print(p.get_device_info_by_index(i).get('name'))


def capture_image(imgformat):
	'''
	This function utilizes Python In-Memory Streams to temporarly save image captured from the PiCamera
	Output data stream can be later processed to fit your needs.
	INPUT: imgformat--> (string) target image format
	OUTPUT: BytesIO() stream object
	'''
	stream = BytesIO()
	if (DEBUG):
		camera.start_preview()
	sleep(2)
	camera.capture(stream, format=imgformat)
	# "Rewind" the stream to the beginning so we can read its content
	stream.seek(0)
	#image = Image.open(stream)
	#text= pytesseract.image_to_string(image)
	return(stream)

def capture_continuous():
	'''
	This function can be used in DEBUG mode with a monitor. It opens camera view finder and capture images when
	the key 'S' is pressed. This function DOES NOT save the captured images.
	INPUT: NONE
	OUTPUT: NONE
	'''
	rawCapture = PiRGBArray(camera, size=(640, 480))

	for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		image = frame.array
		cv2.imshow("Frame", image)
		key = cv2.waitKey(1) & 0xFF
		
		rawCapture.truncate(0)

		if key == ord("s"):
			# print("captured")
			# text = pytesseract.image_to_string(image)
			# print(text)
			cv2.imshow("Frame", image)
			break
	# print("out")
	cv2.destroyAllWindows()
	return (frame)

def create_dir(name):
	try:
		os.mkdir(name)
	except OSError:
		if(DEBUG): print("Creation of the directory %s failed" % home_dir)
		return (True)
	else:
		if(DEBUG): print("Successfully created the directory %s " % home_dir)
		return (False)


def start_session(name):
	session_name=name

	#Create Session Directory
	session_dir = create_dir(session_name)
	if not(session_dir):
		#Free mode
		pass

	session_path=home_dir+"/"+session_name
	# if (DEBUG):
	# 	cv2.namedWindow(name)

	img_counter = 0
	session_name=name

	session_text ={}

	exit_flag  = False

	while not(exit_flag):
		action = checkButtons()

		if (action == 1):
			#Capture an Image
			captured_stream = capture_image("png")
			image = pImage.open(captured_stream)
			img_name = "{}_{}.png".format(session_name, img_counter)
			image.save(os.path.join(session_path , img_name))
			image.close()
			img_counter+=1
		elif (action == 2):
			pass
		elif (action == 3):
			pass
		elif (action == 4):
			#Exit
			exit_flag=True
		else:
			if (DEBUG): print ("Unidentified Input!")
			pass


def check_buttons():
	'''
	read the state of the connected Push Buttons, and output int from 1 to 6 representing 
	which key was pressed.
	Input: NONE
	Output: int from 1 to 6 representing the key pressed
	'''
	if (GPIO.input(22) == GPIO.HIGH) :
		return (1)
	elif (GPIO.input(24) == GPIO.HIGH):
		return (2)
	elif (GPIO.input(26) == GPIO.HIGH):
		return (3)
	elif (GPIO.input(19) == GPIO.HIGH):
		return (4)
	elif (GPIO.input(21) == GPIO.HIGH):
		return (5)
	elif (GPIO.input(23) == GPIO.HIGH):
		return (6)


def on_press(key):
	global last_pressed
	# global flag
	global inputKey
	try:
		if (DEBUG): print('alphanumeric key {0} pressed'.format(key.char))
		last_pressed = key
		# print (type(key.char), type(inputKey))
		# if (key.char == inputKey):
		# 	print("in")
		# 	flag=False
	except AttributeError:
		if (DEBUG): print('special key {0} pressed'.format(key))
		last_pressed = key

def on_release(key):
	global last_pressed
	if (DEBUG): print('{0} released'.format(key))
	#print (key, last_pressed)
	#print (type(key), type(last_pressed))
	if (key == last_pressed):
		# Stop listener
		return False

def wait_for_keystroke(inputKey):
	'''
	This function captures controller events from the keyboard within another python thread
	the function wait for a key press,then terminates.
	Input: inputKey---> (string) the target key to wait for
	'''

	global last_pressed
	inputKey = inputKey
	
	while (True):
		if ((last_pressed!=None) and (last_pressed.char == inputKey)):
			return
		# Collect events until released
		with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
			listener.join()

if __name__ == "__main__":

	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(22, GPIO.IN)
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(24, GPIO.IN)
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(26, GPIO.IN)
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(19, GPIO.IN)
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(21, GPIO.IN)
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(23, GPIO.IN)

	camera = PiCamera()
	camera.resolution = (640, 480)
	camera.framerate = 30


	home_dir = os.getcwd()

	# checkButtons()

	name=input("Enter Session Name: ")
	session_data=start_session(name)

	
	last_pressed = None
	# flag = True
	wait_for_keystroke('f')
	print ("sds")




