import threading
from PIL import Image, ImageTk
from io import BytesIO

from client.ClientRtp import ClientRtp
from client.RtpPacket import RtpPacket

BUF_SIZE = 20480


class VideoClientRtp(ClientRtp):
    def __init__(self, addr, port, *args, **kwargs):
        super(VideoClientRtp, self).__init__(addr, port, *args, **kwargs)

        self.seqNum = 0

        self.bufferSemaphore = None
        self.displaySemaphore = None

        self.decodeFrame = None

        self.displayCallback = None

    def beforeRun(self):
        self.bufferSemaphore = threading.Semaphore(value=1)
        self.displaySemaphore = threading.Semaphore(value=0)
        threading.Thread(target=self.display).start()

    def running(self):
        self.recvRtp()

    def recvRtp(self):
        rtpPacket = RtpPacket()
        byteStream = BytesIO(b'')
        while True:
            try:
                data = self.socket.recv(BUF_SIZE)
                if not data:
                    break
                rtpPacket.decode(data)
                marker = rtpPacket.marker()
                currentSeqNbr = rtpPacket.seqNum()
                print('Current Seq Num: {}'.format(currentSeqNbr))

                if currentSeqNbr > self.seqNum:
                    # TODO assume in order
                    self.seqNum = currentSeqNbr
                    byte = rtpPacket.getPayload()
                    byteStream.write(byte)
                if marker == 1:
                    break
            except IOError:
                continue
        frame = self.decode(byteStream)
        byteStream.close()
        self.bufferSemaphore.acquire()
        self.decodeFrame = frame
        self.displaySemaphore.release()

    @staticmethod
    def decode(byteStream):
        try:
            frame = Image.open(BytesIO(byteStream.getvalue()))
            frame = ImageTk.PhotoImage(frame)
        except OSError:
            frame = None
        return frame

    def setDisplay(self, displayCallback):
        self.displayCallback = displayCallback

    def display(self):
        while self._stop.is_set():
            self.displaySemaphore.acquire()
            frame = self.decodeFrame
            self.bufferSemaphore.release()
            if frame is None:
                self._display_interval.wait(self.interval)
            self.displayCallback(frame)
