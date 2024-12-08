# App for BLE and Wi-Fi device

-[Intro](#Intro)

-[Running project](#running-project)

-[TODO](#todo)

-[App appearance]()


## Intro
This app ia a GUI-based app for handling device with Wi-Fi and BLE standards. It's based on work project for IMU device.

## Running project
Project was written and mainly tested on Windows 10 with Python 3.12. Newer version of Python might not support Bleak 
library. This app heavily relies on Bleak library and Bluetooth Low Energy drivers and in some cases the app might not
run correctly.

Project can be run from Windows commander or from IDE supporting Python scripts. In both cases virtual environment 
needs to be created and packages should be installed. All required packages are listed in `requirements.txt`.

App can be accessed by `Command Prompt` or by IDE run. Script runner is written for virtual environment under `.venv` 
directory. In PyCharm IDE you can set up run configuration as presented below: 
![PyCharm run configuration](/readme/pycharm_conf.png)
For Command Prompt user needs to run `cls; python -m main` command.

For proper app running, `credentials.py` or `credentials_template.py` (whichever is available) should be set 
to user's settings of hotspot or access point and name of device.

Every run of app generates logs in terminal and in file `app.log` inside "logs" directory. Log is overwritten every time
app is run.

Please note that this project was made for specific device and near all functionality is not compatible with other 
devices. It should work as a demonstration of personal Python code writing, which consists of libraries for: 
GUI (customtkinter), BLE (Bleak) and Wi-Fi (socket).

## TODO
1. App needs to be rebuilt for better handling asyncio library as GUI might interfere with Bleak library.
2. Update process should catch event of Bleak library reconnect of BLE device.
3. All code should be fully documented and auto-documentation file should be added.
4. Code should be expanded to cover more non-typical use cases.

## App appearance
As mentioned in `Running project`, all functionalities of application is available only with
compatible device. For this reason, the following is an example of what the user 
interface will look like:

1. Home screen
2. Main app before connecting device
3. Main app after receiving BLE response from device
4. Device info window
5. Device updater window
