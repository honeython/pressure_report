import requests
import numpy as np
import time
from datetime import datetime, timedelta
import io
import matplotlib.pyplot as plt
#from matplotlib.font_manager import FontProperties

#================settings===================
debug_mode=False # is debug_mode?
x_gain=13       # x gain parameter
threshold=0.4   # divide between two points judge value
times=6         # while time (hour)

def line_bot(message:str,images:any)->None:
    """Send Line message function

    Parameters
    ----------
    message : str
        message
    images : any
        plot imege
    """
    #==========LineSetting===================
    line_token = ''
    line_url = "https://notify-api.line.me/api/notify"
    line_headers = {'Authorization': 'Bearer ' + line_token}
    try:
        message = '\n' + message
        payload = {'message': message}
        files = {'imageFile': images.getvalue()}
        r = requests.post(line_url, headers=line_headers, params=payload,files=files)
    except Exception as e:
        #logging.error('Line Error:' + str(e))
        print('Line Error:' + str(e))
        pass
class PressureReport():
    def __init__(self,debug_mode:bool, x_gain:int, threshold:float, times:int) -> None:
        """
        Parameters
        ----------
        debug : bool
            is debug_mode?
        x_gain : int
            x gain parameter
        threshold : float
            divide between two points judge value
        times : int
            while time (hour)
        """        
        self.is_warning = False
        self.list_pressure = []
        self.list_hours = []
        self.list_delta = []
        self.list_warning = []
        self.pressure_message = ""
        self.debug_mode = debug_mode
        self.x_gain = x_gain
        self.threshold = threshold
        self.times = times
        
    def fetch_pressure_plt(self,down_start_num:int, down_end_num:int)-> str:
        """plot & return message

        Parameters
        ----------
        down_start_num : int
            pressure down start index 
        down_end_num : int
            pressure down end index
        pressure_message : str
            pressure message

        Returns
        -------
        str
            pressure message
        """    
        self.pressure_message += f" {self.list_hours[down_start_num]} => {self.list_hours[down_end_num]}\n [{self.list_warning[down_start_num]}hPa] => [{self.list_warning[down_end_num]}hPa] \n"
        list_plt = []
        for k in range(self.x_gain):
            if down_start_num <= k:
                if down_end_num < k:
                    list_plt.append(None)
                else:
                    list_plt.append(self.list_pressure[k])
            else:
                list_plt.append(None)
        plt.plot(self.list_hours,list_plt,"r")
        plt.axvspan( down_start_num,down_end_num,color = "r", alpha=0.1)
        return self.pressure_message

    def down_pressure_info(self)->None:
        """fetch down pressure report
        """
        #==========OpenWetherMapSeting===========
        url = "https://community-open-weather-map.p.rapidapi.com/forecast"
        querystring = {"q":"tokyo,japan"}
        headers = {
            'x-rapidapi-key': "",
            'x-rapidapi-host': "community-open-weather-map.p.rapidapi.com"
            }

        #japanese font setting
        """
        if self.debug_mode is not True:
            font_path = "/usr/share/fonts/opentype/note/NotoSansMonoCJKjp-Regular.otf"
            fp = FontProperties(fname=font_path)
        else:
            font_path = "C:\Windows\Fonts\meiryo.ttc"
            fp = FontProperties(fname=font_path)
        """
        
        #reset parameters
        self.is_warning = False
        self.list_pressure = []
        self.list_hours = []
        self.list_delta = []
        self.list_warning = []
        self.pressure_message = ""
        
        # self.list_warning None List
        for i in range(self.x_gain):
            self.list_warning.append(None)
        
        # get pressure report from OpenWetherMap
        if self.debug_mode is not True:
            response = requests.request("GET", url, headers=headers, params=querystring)
            list_wether_data = response.json()["list"]
            for i in range(self.x_gain):
                self.list_pressure.append(list_wether_data[i]["main"]["pressure"])
        else:
            self.list_pressure = [1014, 1015, 1020, 1010, 1016, 1017, 1016, 1014, 1010,
                            1014, 1015, 1020, 1010, 1016, 1017, 1016, 1014, 1010,
                            1014, 1015, 1020, 1010, 1016, 1017, 1016, 1014, 1010]
            self.list_pressure = self.list_pressure[0:self.x_gain]
            print(f"pressure{self.list_pressure}")
        
        # y-axis list
        now = datetime.fromtimestamp(list_wether_data[0]['dt'])
        self.pressure_message = f"{now.strftime('%#dth%b %#I%p')} [{self.list_pressure[0]}hPa]\n\n"
        for i in range(self.x_gain):
            self.list_hours.append(f"{now.day}th {now.strftime('%#I%p')}")
            now += timedelta(hours=3)

        # set y axis range
        ylim_mean = int(np.mean(self.list_pressure))
        ylim_max = np.max(self.list_pressure)
        ylim_min = np.min(self.list_pressure)
        ylim_top = ylim_mean+7
        ylim_bottom = ylim_mean-7
        if ylim_max > ylim_top:
            ylim_top = ylim_max
        if ylim_min < ylim_bottom:
            ylim_bottom = ylim_min
        
        # set main plot     
        plt.plot(self.list_hours,self.list_pressure)
        plt.grid()
        plt.ylim(ylim_bottom,ylim_top)
        plt.xticks(rotation =45, fontsize=7)#, fontproperties=fp)

        # set 
        for i ,pressure in enumerate(self.list_pressure):
            for j in range(2):
                if i < len(self.list_pressure)-2:
                    per = float(f"{pressure/self.list_pressure[i+1+j]*100-100:.3f}")
                    self.list_delta.append(per)
                    if per > self.threshold:
                        self.is_warning = True
                        self.list_warning[i:i+1+j+1] = self.list_pressure[i:i+1+j+1]
        down_start_num,down_end_num = None,None
        if self.debug_mode:print(f"warning {self.list_warning}")

        if self.is_warning:
            self.pressure_message += f"{(self.x_gain-1)*3}h report\n"

            for i ,pressure in enumerate(self.list_warning):
                if pressure != None:
                    try:
                        if pressure > self.list_warning[i-1]:
                            down_end_num = i-1
                            if down_start_num != down_end_num:
                                self.pressure_message = self.fetch_pressure_plt(down_start_num, down_end_num)
                                down_start_num,down_end_num = None,None
                            else:
                                down_start_num,down_end_num = None,None

                        elif i == len(self.list_warning)-1:
                            down_end_num = i
                            self.pressure_message = self.fetch_pressure_plt(down_start_num, down_end_num)
                            down_start_num,down_end_num = None,None
                    except:
                        pass
                    if down_start_num == None:
                        down_start_num = i
                    
                else:
                    if down_start_num != None:
                        down_end_num = i-1
                        if down_start_num != down_end_num:
                            self.pressure_message = self.fetch_pressure_plt(down_start_num, down_end_num)
                        down_start_num,down_end_num = None,None

        self.is_warning = False
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        if self.debug_mode is not True:
            plt.close()        
            line_bot(self.pressure_message,buf)
            print(self.pressure_message)
            time.sleep(60*60*self.times)
        else:
            plt.show()
            print(self.pressure_message)

if __name__ == "__main__":
    pressure_report = PressureReport(debug_mode, x_gain,threshold,times)
    while True:
        pressure_report.down_pressure_info()
        if debug_mode:break

