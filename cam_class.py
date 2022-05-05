from turtle import width
import cv2
from PIL import Image
import numpy as np
import img_processing as imgprocess
import time
import re 


class Control_Cam:
    def __init__(self, mydb):
        self.time_gasmeter = 0
        self.time_watermeter = 0
        self.photo_intervall_gasmeter = 1*60*60
        self.photo_intervall_watermeter = 0.5*60*60
        self.photo_time_gasmeter = (20,50)
        self.photo_time_watermeter = (20,30)
        self.photo_time_gasmeter_done = False
        self.photo_time_watermeter_done = False
        self.photo_now_gasmeter = False
        self.photo_now_watermeter = False
        self.last_gas_number = 0
        self.last_water_number = 0
        self.photo_gas_number_try = 0
        self.photo_water_number_try = 0

        self.cam2_sleep_active = True
        self.cam1_sleep_active = True

        self.mydb = mydb
        self.mycursor = mydb.cursor()

    def set_time_gasmeter(self):
        self.time_gasmeter = time.time() #in Seconds

    def set_time_watermeter(self):
        self.time_watermeter= time.time()

    # Return true if new photo request
    def get_new_img_gas(self, client):
        time_real = imgprocess.get_time()
        time_seconds = time.time()
        print("Time gasmeter_last picture:", self.time_gasmeter)
        print("Time gasmeter_last picture+ intervall:", self.time_gasmeter + self.photo_intervall_gasmeter)
        print("Time now", time_seconds)
        if(((self.time_gasmeter + self.photo_intervall_gasmeter) < time_seconds) or (self.photo_now_gasmeter)):
            self.photo_now_gasmeter = False
            print("Interval Gas_meter over, now photo")
            client.publish("/cam2/photo", "Flash")
        elif ((time_real[1] == self.photo_time_gasmeter[0] and time_real[0] >= self.photo_time_gasmeter[1]) or # time_real: (time.minute, time.hour, time.day, time.month, time.year)
                 (time_real[1] >= self.photo_time_gasmeter[0]) and not self.photo_time_gasmeter_done):
            client.publish("/cam2/photo", "Flash")
            self.photo_time_gasmeter_done = True
            print("Time toogle Gas_meter, now photo")
        else:
            if time_real[1] < self.photo_time_gasmeter[0]:
                self.photo_time_gasmeter_done = False
            if self.cam2_sleep_active:
                client.publish("/cam2/sleep", "Sleep_now")
                print("Cam2 Sleep_now")

        
    def get_new_img_water(self, client):
        time_real = imgprocess.get_time()
        time_seconds = time.time()
        if(((self.time_watermeter + self.photo_intervall_watermeter) < time_seconds) or (self.photo_now_watermeter)):
            self.photo_now_watermeter = False
            client.publish("/cam1/photo", "Flash")
        elif ((time_real[1] == self.photo_time_watermeter[0] and time_real[0] >= self.photo_time_watermeter[1]) or
                 (time_real[1] >= self.photo_time_watermeter[0]) and not self.photo_time_watermeter_done):
            client.publish("/cam1/photo", "Flash")
            self.photo_time_watermeter_done = True
        else:
            if time_real[1] < self.photo_time_watermeter[0]:
                self.photo_time_watermeter_done = False
            if self.cam1_sleep_active:
                client.publish("/cam1/sleep", "Sleep_now")
                print("Cam1 Sleep_now")
    
    def on_photo_gasmeter(self, buff, point, client):
        gas_meter = Gas_Meter(buff, point)
        print("Gasmeter value: ", gas_meter.numbers)
        self.set_time_gasmeter()
        if (gas_meter.check_numbers() and (gas_meter.numbers > self.last_gas_number) or (self.photo_gas_number_try >= 2)):
            gas_meter.save_img()
            if self.photo_gas_number_try == 0:
                self.insert_into_database("gas", gas_meter.numbers, "good")
            else:
                self.insert_into_database("gas", gas_meter.numbers, "bad")
            self.photo_gas_number_try = 0
            if self.cam2_sleep_active:
                client.publish("/cam2/sleep", "Sleep_now")
                print("Cam2 Sleep_now")
        else:
            client.publish("/cam2/photo", "Flash")
            print("Cam 2 try:", self.photo_gas_number_try)
            self.photo_gas_number_try = self.photo_gas_number_try + 1

            

    def on_photo_watermeter(self, buff, point, client):
        water_meter = Water_Meter(buff, point)
        print("Watermeter value: ", water_meter.numbers)
        self.set_time_watermeter()
        if (water_meter.check_numbers() and (water_meter.numbers >= self.last_water_number) or (self.photo_water_number_try >= 2)):
            water_meter.save_img()
            if self.photo_water_number_try == 0:
                self.insert_into_database("water", water_meter.numbers, "good")
            else:
                self.insert_into_database("water", water_meter.numbers, "bad")
            self.photo_water_number_try = 0
            if self.cam1_sleep_active:
                client.publish("/cam1/sleep", "Sleep_now")
                print("Cam1 Sleep_now")
        else:
            client.publish("/cam1/photo", "Flash")
            print("Cam 1 try:", self.photo_water_number_try)
            self.photo_water_number_try = self.photo_water_number_try + 1

    
    def insert_into_database(self, type, value, quality):
            sql = "INSERT INTO cam_data_gas_water_meter (value, type, quality) VALUES (%s, %s, %s)"
            val = (value, type, quality)
            try:
                self.mycursor.execute(sql, val)
                self.mydb.commit()
                print(self.mycursor.rowcount, "record inserted.")
            except:
                print("Database insert failed")
        
        


img_path = "./img"

class Gas_Meter:
    def __init__(self, buff, point):
        self.refpoint = point 
        nparr = np.frombuffer(buff, np.uint8)
        img = cv2.imdecode(nparr,1)

        time_now = imgprocess.get_time()
        self.path = img_path + "/img_gas/" + str(time_now[4]) + "-" + str(time_now[3]) + "-" + str(time_now[2]) + ";" + str(time_now[1]) + "-" + str(time_now[0]) + ".jpg"
        self.temppath = img_path + "/temp_gas.jpg"
        imgprocess.rotate_save_img(img, 90, self.temppath)
        self.img = cv2.imread(self.temppath)
        self.numbers_arr = self.analyse_img()
        self.numbers = self.get_number_from_arr()

    def save_img(self):
        cv2.imwrite(self.path, self.img)
    
    def get_number_from_arr(self):
        numbers = ""
        for number in self.numbers_arr:
            numbers = numbers + number
        return int(numbers)


    def analyse_img(self):
        for i in range(0, 7):
            print(i)
            img_num = self.img [self.refpoint[1]+18 : self.refpoint[1]+70, self.refpoint[0]+43+(i*(32+38)) :  self.refpoint[0]+77+(i*(32+38))] # h/b (y/x)
            img_num = imgprocess.process_img(img_num, True)
            cv2.imwrite("./img/temp_gas"+ str(i) +".jpg",img_num)

        img_num = self.img [self.refpoint[1]+18 : self.refpoint[1]+70, self.refpoint[0]+542 :  self.refpoint[0]+542+38] # h/b (y/x)
        img_num = imgprocess.process_img(img_num, True)
        cv2.imwrite("./img/temp_gas"+ str(7) +".jpg",img_num)
        numbers = []
        for i in range(0, 8):
            result = imgprocess.run_digital_number("./img/temp_gas"+ str(i) +".jpg")
            print(result)
            if not result == 10:
                text = result
                print("Text recognised:", text)
                numbers.append(str(text))
            else:
                print("Number not recognised")
        return numbers
    
    def check_numbers(self):
        if len (self.numbers_arr) == 8:
            return True
        else:
            return False





class Water_Meter:
    def __init__(self, buff, point):
        self.refpoint = point # refpoint is black dot
        nparr = np.frombuffer(buff, np.uint8)
        img = cv2.imdecode(nparr,1)

        time_now = imgprocess.get_time()
        self.path = img_path + "/img_water/" + str(time_now[4]) + "-" + str(time_now[3]) + "-" + str(time_now[2]) + ";" + str(time_now[1]) + "-" + str(time_now[0]) + ".jpg"
        self.temppath = img_path + "/temp_water.jpg"
        imgprocess.rotate_save_img(img, 270, self.temppath)
        self.img = cv2.imread(self.temppath)
        self.numbers_arr_dig, self.numbers_arr_analog = self.analyse_img()
        self.numbers = self.get_number_from_arr()

    def save_img(self):
        cv2.imwrite(self.path, self.img)
    
    def get_number_from_arr(self):
        numbers = ""
        for number in self.numbers_arr_dig:
            numbers = numbers + number
        for number in self.numbers_arr_analog:
            numbers = numbers + number

        return int(numbers)


    def analyse_img(self):
        digital_points = [[211,30], [162,27], [116,24], [70, 22]]
        width = 26
        height = 41
        i = 0
        for digital_point in digital_points:
           img_num = self.img [self.refpoint[1]- digital_point[1] : self.refpoint[1]- digital_point[1]+ height,
                                    self.refpoint[0]-digital_point[0] : self.refpoint[0]-digital_point[0]+width] # h/b (y/x)
           img_num = imgprocess.process_img(img_num, False)
           cv2.imwrite("./img/temp_water"+ str(i) +".jpg",img_num)
           i = i + 1 
        
        analog_sqare = 93
        analog_points = [[35,71], [92,165], [189,206], [309, 157]] #h/b = 93 up, left corner
        i = 0
        for analog_point in analog_points:
            img_analog = self.img [self.refpoint[1]+analog_point[1] : self.refpoint[1]+analog_point[1]+ analog_sqare,
                                    self.refpoint[0]-analog_point[0] : self.refpoint[0]-analog_point[0]+analog_sqare] # h/b (y/x)
            cv2.imwrite("./img/temp_water_analog"+ str(i) +".jpg", img_analog)
            i = i+1

        numbers_dig = []
        numbers_analog = []
        for i in range(1, 4):
            result = imgprocess.run_digital_number("./img/temp_water"+ str(i) +".jpg")
            if not result == 10:
                text = result
                print("Text recognised:", text)
                numbers_dig.append(str(text))
            else:
                print("Number not recognised")
        
        for i in range (0, 4):
            result = imgprocess.run_analog_needle("./img/temp_water_analog"+ str(i) +".jpg")
            number = int(result)
            numbers_analog.append(str(number))

        return numbers_dig, numbers_analog

    def check_numbers(self):
        if len (self.numbers_arr_dig) == 3:
            return True
        else:
            return False



