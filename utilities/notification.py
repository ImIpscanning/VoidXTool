import os
from plyer import notification
from loguru import logger
from voidxtool.files import VoidXToolPath

class SendNotification:
    def __init__(self, title: str, message: str):
        '''
Initialize the SendNotification with the title and message.

:param title: The title of the notification
:param message: The message to be displayed in the notification
'''
        self.title = title
        self.message = message

    @logger.catch
    def send(self):
        '''
Send a notification to the user
'''
        if os.name == 'nt':
            notification.notify(
                title=self.title,
                message=self.message,
                app_name='VoidXTool',
                app_icon=str(VoidXToolPath().get_voidxtool_data_path()) + '/icon.ico',
                timeout=1
            )