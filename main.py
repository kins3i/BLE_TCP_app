"""
Main program.
Created on 2024-12-01 by kins3i
"""

import sys
import win32api
import win32event
from winerror import ERROR_ALREADY_EXISTS

from app_frontend.gui_main import App
from logger_set import logger

if __name__ == "__main__":
    try:
        mutex = win32event.CreateMutex(None, False, 'name')
        last_error = win32api.GetLastError()
        if last_error == ERROR_ALREADY_EXISTS:
            logger.debug("App already opened")
            sys.exit(0)
        logger.debug("Hello in my app!")
        app = App()
        app.mainloop()
    except SystemExit:
        logger.debug("System exit")
