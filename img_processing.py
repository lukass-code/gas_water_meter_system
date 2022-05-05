from PIL import Image
from datetime import datetime
import pytz
import cv2
import postprocess_img
#from  tensorflow import keras
import tflite_runtime.interpreter as tflite
import numpy as np
import math
import time



def rotate_save_img(img ,deg, path):
    img  = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    if deg == 90:
        rotated_img = img.transpose(Image.ROTATE_90)
    elif deg == 180:
        rotated_img = img.transpose(Image.ROTATE_180)
    elif deg == 270:
        rotated_img = img.transpose(Image.ROTATE_270)
    else:
        rotated_img = img

    rotated_img.save(path)

def get_time():
    tz_DE = pytz.timezone("Europe/Berlin")
    time = datetime.now(tz_DE)
    return (time.minute, time.hour, time.day, time.month, time.year)

def process_img(img_g, invert):
    img_g = postprocess_img.get_grayscale(img_g)
    if invert:
        img_g = cv2.bitwise_not(img_g)
    img_g = postprocess_img.thresholding(img_g)
    img_g = cv2.cvtColor(img_g, cv2.COLOR_GRAY2RGB)
    return img_g

def run_digital_number(path):
    #model = keras.models.load_model('/home/pi/Desktop/Server_Smarthome/mqtt_server/model/Digital-Readout_Version_6.0.0.h5')

    interpreter = tflite.Interpreter('./model/model_digital_number.tflite')
    interpreter.allocate_tensors()

    # Get input and output tensors.
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    img_num = Image.open(path)
    img_num = img_num.resize((20, 32), Image.NEAREST)
    img_num.save(path)
    img_num.save("./img/img_digts/" + str(time.time()) + "digit.jpg")
    img_num = np.array(img_num, dtype="float32")
    print(np.shape(img_num))
    img_num = np.reshape(img_num,[1,32,20,3])
    #result = model.predict_classes(img_num)

    input_data = img_num
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_tensor = np.squeeze(interpreter.get_tensor(output_details[0]['index']))
    prob_descending = sorted(
             range(len(output_tensor)), key=lambda k: output_tensor[k], reverse=True)
    #print(prob_descending)
    print(prob_descending[0])
    result =  prob_descending[0]

    return result

def run_analog_needle(path):
    #model = keras.models.load_model('./model/ana0910s0.h5')

    interpreter = tflite.Interpreter('./model/model_analog_needle.tflite')
    interpreter.allocate_tensors()

    # Get input and output tensors.
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    img = Image.open(path)
    img = img.resize((32, 32), Image.NEAREST)
    img = np.array(img, dtype="float32")
    img = np.reshape(img,[1,32,32,3])

    #classes = model.predict(img)

    input_data = img
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    print(output_data)
    classes = output_data
    
    out_sin = classes[0][0]  
    out_cos = classes[0][1]
    out_number = (np.arctan2(out_sin, out_cos)/(2*math.pi)) % 1
    print("Analog needle:", str(out_number))
    return out_number*10

if __name__ == '__main__':
    pass
