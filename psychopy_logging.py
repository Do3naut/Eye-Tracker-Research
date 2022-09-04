# Adapted from PsychoPy documentation, requires the psychopy library to be installed to work

from psychopy import logging

class DataLogger:
    """
    Note for debugging: since I can't test this live, I put another attempt as comments 
    (so the # prevents them from being run). To try the alternative, please remove the 2 #s
    under __init__()  (lines 17 & 18), remove the # for line 23, and 
    add a # in front of line 21
    """

    def __init__(self):
        self.lastLog = logging.LogFile("testRun.log", level=logging.DATA, filemode='w')
        logging.console.setLevel(logging.DATA)

        # self.logger = logging._Logger()
        # self.logger.addTarget(self.lastLog)

    def log_position(self, x, y):
        logging.log(level=logging.DATA, msg=f'x_pos: {x}, y_pos: {y}')
        
        # self.logger.log(f'x_pos: {x}, y_pos: {y}', logging.DATA)