#!/usr/bin/env python
# coding: utf-8

from ctypes import *
import numpy as np
import cv2
import threading
import usb1

#
#Press "s" to save the frames. Press "q" to quit. 
#
class ShowImage:
    
    def __init__(self, ImParams_r, ImParams_l):
        self.IM_X_r = ImParams_r.IM_X
        self.IM_Y_r = ImParams_r.IM_Y
        self.im_type_r = ImParams_r.im_type
        self.stream_name_r = ImParams_r.stream_name
        self.DataReady_r = ImParams_r.DataReady
        self.LineError_r = ImParams_r.LineError
        self.SecondFrame_r = ImParams_r.SecondFrame
        self.im_array1_r = ImParams_r.im_array1
        self.im_array2_r = ImParams_r.im_array2
        self.IM_X_l = ImParams_l.IM_X
        self.IM_Y_l = ImParams_l.IM_Y
        self.im_type_l = ImParams_l.im_type
        self.stream_name_l = ImParams_l.stream_name
        self.DataReady_l = ImParams_l.DataReady
        self.LineError_l = ImParams_l.LineError
        self.SecondFrame_l = ImParams_l.SecondFrame
        self.im_array1_l = ImParams_l.im_array1
        self.im_array2_l = ImParams_l.im_array2
        
        if (self.im_type_r == 2):
            self.im_to_show_r = np.zeros((self.IM_Y_r,self.IM_X_r,3),np.uint8)
            self.win_name_r = "FPGA video - " + str(self.IM_X_r) + "x" + str(self.IM_Y_r) + " RGB " +  self.stream_name_r
        elif (self.im_type_r == 1):
            self.im_to_show_r = np.zeros((self.IM_Y_r,self.IM_X_r),np.uint8)
            self.win_name_r = "FPGA video - " + str(self.IM_X_r) + "x" + str(self.IM_Y_r) + " grayscale " + self.stream_name_r
            
        if (self.im_type_l == 2):
            self.im_to_show_l = np.zeros((self.IM_Y_l,self.IM_X_l,3),np.uint8)
            self.win_name_l = "FPGA video - " + str(self.IM_X_l) + "x" + str(self.IM_Y_l) + " RGB " +  self.stream_name_l
        elif (self.im_type_l == 1):
            self.im_to_show_l = np.zeros((self.IM_Y_l,self.IM_X_l),np.uint8)
            self.win_name_l = "FPGA video - " + str(self.IM_X_l) + "x" + str(self.IM_Y_l) + " grayscale " + self.stream_name_l
    
    #RGB565 to RGB888
    @staticmethod
    def _ProcessImageRGB(im_to_show, im_array):
        mask = [0X1F, 0X7E0, 0XF800]
        shift = [3, 3, 8]
        shift2 = [2, 9, 13]
        for i in range(3):
            im = (im_array & mask[i])
            if (i == 0):
                im_to_show[:,:,i] = (im << shift[i]) |  (im >> shift2[i])
            else:
                im_to_show[:,:,i] = (im >> shift[i]) |  (im >> shift2[i])
                
          

    #Show image        
    def Show(self):
           
        im_cnt = 0
        cv2.namedWindow(self.win_name_r)
        cv2.namedWindow(self.win_name_l)
       
        while (not (self.LineError_r.isSet() or self.LineError_l.isSet())):
            #Right
            if (self.DataReady_r.isSet()):
                if (self.SecondFrame_r.isSet()):
                    if (self.im_type_r == 2):
                        self._ProcessImageRGB(self.im_to_show_r, self.im_array1_r)
                    elif (self.im_type_r == 1):
                        self.im_to_show_r = self.im_array1_r
                else:
                    if (self.im_type_r == 2):
                        self._ProcessImageRGB(self.im_to_show_r, self.im_array2_r)
                    elif (self.im_type_r == 1):
                        self.im_to_show_r = self.im_array2_r
                self.DataReady_r.clear()
            #Left
            if (self.DataReady_l.isSet()):
                if (self.SecondFrame_l.isSet()):
                    if (self.im_type_l == 2):
                        self._ProcessImageRGB(self.im_to_show_l, self.im_array1_l)
                    elif (self.im_type_l == 1):
                        self.im_to_show_l = self.im_array1_l
                else:
                    if (self.im_type_l == 2):
                        self._ProcessImageRGB(self.im_to_show_l, self.im_array2_l)
                    elif (self.im_type_l == 1):
                        self.im_to_show_l = self.im_array2_l
                self.DataReady_l.clear()    
            
            cv2.imshow(self.win_name_r, self.im_to_show_r)
            cv2.imshow(self.win_name_l, self.im_to_show_l)
                        
            key = cv2.waitKey(10)
                
            if key == ord('s'):
                filename_r = "Img_" + self.stream_name_r + "_" + str(im_cnt)+".png"
                im_to_save = np.array(self.im_to_show_r).copy()
                cv2.imwrite(filename_r,im_to_save)
                filename_l = "Img_" + self.stream_name_l + "_" + str(im_cnt)+".png"
                im_to_save = np.array(self.im_to_show_l).copy()
                cv2.imwrite(filename_l,im_to_save)
                im_cnt += 1
                print ("Saved images:")
                print (filename_r, filename_l)
                
            if key == ord('q'): 
                break

def main():
    #FSM commands
    GET_CFG = create_string_buffer(b'\x01\x01') #Get image params
    STRT_ST = create_string_buffer(b'\x11\x11') #Start stream
    STOP_ST = create_string_buffer(b'\x0f\x0f') #Stop stream
    #Number of usb transfers
    USB_NUM_TRANSFERS = 64
    #Device name
    init_string = "FPGA Video Stream"
    im_type = 0
    started = False
    r_buf = create_string_buffer(16384)
    handle = None
    context = usb1.USBContext()
    #CYUSB3014
    idVendor = 0x04b4
    idProduct = 0x00f1
    
    for device in context.getDeviceIterator(skip_on_error=True):
        if (device.getVendorID() == idVendor and device.getProductID() == idProduct):
            handle = device.open()
            if (handle.getProduct() == init_string): #Check device name
                break
            else:
                handle.close()
                handle = None
    
    if (handle is None):
        print ("Failed to open device")
        return
    handle.resetDevice()
    handle.claimInterface(0)
    
    handle._bulkTransfer(0x02, byref(GET_CFG),2, 1000)#send 
        
    r_cnt = handle._bulkTransfer(0x81, byref(r_buf),6, 1000)#receive     
    recv_data = r_buf[0:r_cnt]  
      
    if (recv_data[0] == 0xAA and recv_data[1] == 0x01):
        im_type = 1
    elif (recv_data[0] == 0xBB and recv_data[1] == 0x01):
        im_type = 2
    else:
        print ("Invalid image type")
        return
    
    print ("Im type", im_type)
    IM_X = recv_data[2] + (recv_data[3] << 8)
    print ("Im X", IM_X)
    IM_Y = recv_data[4] + (recv_data[5] << 8)
    print ("Im Y", IM_Y)
        
    if (im_type == 1):
        im_array1_r = np.zeros((IM_Y,IM_X),np.uint8)
        im_array2_r = np.zeros((IM_Y,IM_X),np.uint8)
        im_array1_l = np.zeros((IM_Y,IM_X),np.uint8)
        im_array2_l = np.zeros((IM_Y,IM_X),np.uint8)
        
    elif (im_type == 2):
        im_array1_r = np.zeros((IM_Y,IM_X),np.uint16)
        im_array2_r = np.zeros((IM_Y,IM_X),np.uint16)
        im_array1_l = np.zeros((IM_Y,IM_X),np.uint16)
        im_array2_l = np.zeros((IM_Y,IM_X),np.uint16)
    
    SecondFrame_r = threading.Event()
    DataReady_r = threading.Event()
    LineError_r = threading.Event()
    SecondFrame_l = threading.Event()
    DataReady_l = threading.Event()
    LineError_l = threading.Event()
    
    ImageParams_r = ImParams(IM_X, IM_Y, im_type, DataReady_r, SecondFrame_r, LineError_r, im_array1_r, im_array2_r, "Right")
    ImageParams_l = ImParams(IM_X, IM_Y, im_type, DataReady_l, SecondFrame_l, LineError_l, im_array1_l, im_array2_l, "Left")
    
    #Start show image thread
    ShowIm = ShowImage(ImageParams_r, ImageParams_l)
    
    ShowImageThread = threading.Thread(target=ShowIm.Show)
    ShowImageThread.daemon = True
    ShowImageThread.start()
    
    
    
    transfer_list = []
    #Buffer processing callbacks
    cb_r = ProcessImage(ImageParams_r, ShowImageThread)
    cb_l = ProcessImage(ImageParams_l, ShowImageThread)
        
    while (True):
        if (not started):
            handle._bulkTransfer(0x02, byref(STRT_ST),2 , 1000)#send 
            print("Starting stream")
            started = True
            ImageParams_r.LineError.clear()
            ImageParams_l.LineError.clear()
        else:
            for j in range(USB_NUM_TRANSFERS): #fill the transfer queue 
                if (j % 2 == 0):
                    EP = 0x82
                    cb = cb_l.ProcessData
                else:
                    EP = 0x81
                    cb = cb_r.ProcessData
                    
                transfer = handle.getTransfer()
                transfer.setBulk(
                    EP,
                    16384,
                    callback=cb, #Buffer processing callback 
                    timeout = 1000)
                transfer.submit()
                transfer_list.append(transfer)
        
        
            while  any(x.isSubmitted() for x in transfer_list) and not ImageParams_r.LineError.isSet() and not ImageParams_l.LineError.isSet():
                context.handleEvents()
            break    
                    
    handle._bulkTransfer(0x02, byref(STOP_ST),2, 1000)#send 
    handle.resetDevice()
    handle.releaseInterface(0)
    handle.close()
    

class ProcessImage:
    def __init__ (self, ImageParams, ShowImageThread):
        self.IM_X = ImageParams.IM_X
        self.IM_Y = ImageParams.IM_Y
        self.im_type = ImageParams.im_type
        self.line_cnt = 0
        self.im_ptr = 0
        self.rem_ptr = 0
        self.DataReady = ImageParams.DataReady
        self.ShowImageThread = ShowImageThread
        self.SecondFrame = ImageParams.SecondFrame
        self.im_array1 = ImageParams.im_array1
        self.im_array2 = ImageParams.im_array2
        self.LineError = ImageParams.LineError
        self.stream_name = ImageParams.stream_name
    
    #Buffer processing callback   
    def ProcessData(self, transfer):
        
        buflen = transfer.getActualLength()
        data = transfer.getBuffer()[:buflen]
        buf_step = self.IM_X * self.im_type + 2
        line_in_buf = (buflen - self.im_ptr) // buf_step
        curr_line_in_buf = 0
        if (buflen == 16384):
            if (self.im_ptr != 0):
                if (self.SecondFrame.isSet()):
                    im_array = self.im_array2
                else:
                    im_array = self.im_array1
                im_array[self.line_cnt, (self.rem_ptr - 2) // self.im_type : ] = np.frombuffer(data[0: self.im_ptr],  dtype='>u2' if self.im_type == 2 else np.uint8)
                
                    
            for pack_ptr in range(self.im_ptr, buflen, buf_step):
                if (self.SecondFrame.isSet()):
                    im_array = self.im_array2
                else:
                    im_array = self.im_array1
                line_cnt_old = self.line_cnt
                self.line_cnt = data[pack_ptr] + (data[pack_ptr + 1] << 8)
                
                if (self.line_cnt > self.IM_Y - 1):
                    self.LineError.set()
                    print("Error in line counter", self.line_cnt)
                    print("Previous line counter", line_cnt_old)
                    print("Pack ptr", pack_ptr)
                    return
                
                if (curr_line_in_buf < line_in_buf):
                    im_array[self.line_cnt] = np.frombuffer(data[(pack_ptr + 2)  : (pack_ptr + buf_step) ],  dtype='>u2' if self.im_type == 2 else np.uint8)
                    if ((pack_ptr + buf_step) == 16384):
                        self.rem_ptr = 0
                        self.im_ptr = 0
                else:
                    self.rem_ptr = (buflen - self.im_ptr) % buf_step
                    self.im_ptr = buf_step - self.rem_ptr
                    im_array[self.line_cnt, 0 : (self.rem_ptr - 2) // self.im_type] = np.frombuffer(data[buflen - self.rem_ptr + 2 : buflen],  dtype='>u2' if self.im_type == 2 else np.uint8)
                   
                if (self.line_cnt == self.IM_Y - 1):
                    if (self.SecondFrame.isSet()):
                        self.SecondFrame.clear()
                    else:
                        self.SecondFrame.set()
                        
                    self.DataReady.set()
                                    
                curr_line_in_buf += 1
        
        if (self.ShowImageThread.is_alive() and not self.LineError.isSet()):
            transfer.submit()   

class ImParams:
    def __init__(self, IM_X, IM_Y, im_type, DataReady, SecondFrame, LineError, im_array1, im_array2, stream_name):
        self.IM_X = IM_X
        self.IM_Y = IM_Y
        self.im_type = im_type
        self.DataReady = DataReady
        self.SecondFrame = SecondFrame
        self.im_array1 = im_array1
        self.im_array2 = im_array2
        self.LineError = LineError
        self.stream_name = stream_name
        
if __name__ == '__main__':
    main()
    
    
