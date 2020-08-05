import time

from src.jetson.video_capturer import VideoCapturer
class TestCapturer():
    def setup_class(self):
        self.capturer = VideoCapturer(False)

    def test_init(self):
        assert self.capturer.t1.isAlive()
        assert self.capturer.capture is not None
        assert self.capturer.frame is not None

    def test_update(self):
        assert self.capturer.frame is not None
        oldFrame = self.capturer.frame.copy()
        time.sleep(.02) # sleep long enough to ensure thread t1 updates
        assert oldFrame is not self.capturer.frame

    def test_get_frame(self):
        assert self.capturer.frame is not None
        assert self.capturer.frame is self.capturer.get_frame()

    def test_close(self):
        self.capturer.close()
        assert self.capturer.t1.isAlive() == False
        
        
