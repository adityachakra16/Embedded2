import time

from src.jetson.video_capturer import VideoCapturer
class TestCapturer():
    '''
    Tests in this class are for the VideoCapturer class found in src/video_capturer.py
    '''
    def setup_class(self):
        self.capturer = VideoCapturer(False)

    def test_init(self):
        '''
        Tests constructor
        Checks:
            - Update thread is created
            - Capturer is not null (interface with camera established)
            - First captured frame is not null
        '''
        assert self.capturer.t1.isAlive()
        assert self.capturer.capture is not None
        assert self.capturer.frame is not None

    def test_update(self):
        '''
        Tests 'update' function
        Checks:
            - Frames captured are not null
            - Every frame is different from the previous frame
        '''
        assert self.capturer.frame is not None
        oldFrame = self.capturer.frame.copy()
        time.sleep(.02) # sleep long enough to ensure thread t1 updates
        assert oldFrame is not self.capturer.frame

    def test_get_frame(self):
        '''
        Tests 'get_frame' function
        Checks:
            - Frame returned is not null
            - Frame returned is equal to frame instance variable
        '''
        assert self.capturer.frame is not None
        assert self.capturer.frame is self.capturer.get_frame()

    def test_close(self):
        '''
        Tests 'close' function
        Checks:
            - Update thread is no longer alive
        '''
        self.capturer.close()
        assert self.capturer.t1.isAlive() == False
        
        
