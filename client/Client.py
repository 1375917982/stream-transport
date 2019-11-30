import threading
from tkinter import *
import tkinter.messagebox

from client.ClientRtspController import ClientRtspController
from client.FileExplorer import FileExplorer


class Client:
    def __init__(self, serveraddr, serverport):
        self.rtspController = None
        self.fileExplorer = None

        self.master = None
        self.start_pause = None
        self.displayLabel = None
        self.scale = None
        self.currentTimeLabel = None
        self.totalTimeLabel = None
        self.currentTimeLabelStringVar = None
        self.totalTimeLabelStringVar = None
        self.searchVar = None
        self.searchEntry = None
        self.fileListBox = None
        self.advanceButton = None
        self.delayButton = None
        self.qualityButton = None
        self.muteButton = None
        self.forwardButton = None
        self.backwardButton = None
        self.speedButton = None
        self.fullScreenButton = None

        self.topLevel = None
        self.topLevelLabel = None

        self.videoTime = 0

        self.filenames = []

        self.recvRtspCallback = {}
        self.init(serveraddr, serverport)

        self.master.mainloop()

    def init(self, serveraddr, serverport):
        self.rtspController = ClientRtspController(serveraddr, serverport)
        self.rtspController.setUpdateVideoCallback(self.updateVideo)
        self.rtspController.setWarningBox(tkinter.messagebox)
        self.rtspController.connectToServer()
        self.createWidgets()
        self.getRtspRecvCallbackOfEachState()
        self.rtspController.setRecvCallback(self.rtspRecvCallback)
        threading.Thread(target=self.updateTimeLabelThread, daemon=True).start()
        self.fileExplorer = FileExplorer(serveraddr, 20000, self.updateFileListBoxCallback)
        self.enterEntryHandler(None)

    def createWidgets(self):
        """Build GUI."""
        self.master = tkinter.Tk()
        self.master.protocol('WM_DELETE_WINDOW', self.exitHandler)

        leftFrame = tkinter.Frame(self.master, width=30, height=30, bg='pink')
        leftFrame.grid(row=0, column=0, padx=2, pady=2)

        rightFrame = tkinter.Frame(self.master, width=30, height=30, bg='black')
        rightFrame.grid(row=0, column=1, padx=2, pady=2)

        displayArea = tkinter.Frame(leftFrame, width=26, height=21, bg='yellow')
        displayArea.grid(row=0, column=0, padx=1, pady=1)

        scaleArea = tkinter.Frame(leftFrame, width=26, height=5, bg='blue')
        scaleArea.grid(row=1, column=0, padx=1, pady=1)

        buttonArea = tkinter.Frame(leftFrame, width=26, height=5, bg='red')
        buttonArea.grid(row=2, column=0, padx=1, pady=1)

        # Create Play button
        self.start_pause = Button(buttonArea, width=20, padx=3, pady=3)
        self.start_pause["text"] = "Play"
        self.start_pause["command"] = self.play
        self.start_pause.grid(row=0, column=1, columnspan=2, padx=2, pady=2)

        self.backwardButton = Button(buttonArea, width=10, padx=3, pady=3)
        self.backwardButton["text"] = "-30s"
        self.backwardButton["command"] = self.backward
        self.backwardButton.grid(row=0, column=0, padx=2, pady=2)

        self.forwardButton = Button(buttonArea, width=10, padx=3, pady=3)
        self.forwardButton["text"] = "+30s"
        self.forwardButton["command"] = self.forward
        self.forwardButton.grid(row=0, column=3, padx=2, pady=2)

        self.speedButton = Button(buttonArea, width=10, padx=3, pady=3)
        self.speedButton["text"] = "2x"
        self.speedButton["command"] = self.speedup
        self.speedButton.grid(row=0, column=4, padx=2, pady=2)

        self.muteButton = Button(buttonArea, width=10, padx=3, pady=3)
        self.muteButton["text"] = "Mute"
        self.muteButton["command"] = self.mute
        self.muteButton.grid(row=1, column=0, padx=2, pady=2)

        self.delayButton = Button(buttonArea, width=10, padx=3, pady=3)
        self.delayButton["text"] = "-0.5s"
        self.delayButton["command"] = self.delay
        self.delayButton.grid(row=1, column=1, padx=2, pady=2)

        self.advanceButton = Button(buttonArea, width=10, padx=3, pady=3)
        self.advanceButton["text"] = "+0.5s"
        self.advanceButton["command"] = self.advance
        self.advanceButton.grid(row=1, column=2, padx=2, pady=2)

        self.qualityButton = Button(buttonArea, width=10, padx=3, pady=3)
        self.qualityButton["text"] = "Blur"
        self.qualityButton["command"] = self.blur
        self.qualityButton.grid(row=1, column=3, padx=2, pady=2)

        self.fullScreenButton = Button(buttonArea, width=10, padx=3, pady=3)
        self.fullScreenButton["text"] = "Full Screen"
        self.fullScreenButton["command"] = self.fullScreen
        self.fullScreenButton.grid(row=1, column=4, padx=2, pady=2)

        self.scale = tkinter.Scale(
            scaleArea, from_=0, to=1000,
            showvalue=False, orient='horizontal',
            length=480
        )
        self.scale.grid(row=0, column=0, columnspan=2, padx=2, pady=2)
        self.scale.bind('<Button-1>', self.clickScaleHandler)
        self.scale.bind('<ButtonRelease-1>', self.releaseScaleHandler)

        self.currentTimeLabelStringVar = tkinter.StringVar()
        self.currentTimeLabel = tkinter.Label(
            scaleArea,
            textvariable=self.currentTimeLabelStringVar,
            font=('Arial', 10), anchor=tkinter.NW
        )
        self.currentTimeLabel.grid(
            row=1, column=0, padx=2, pady=2,
            sticky=tkinter.NW
        )
        self.currentTimeLabelStringVar.set('0:00:00')

        self.totalTimeLabelStringVar = tkinter.StringVar()
        self.totalTimeLabel = tkinter.Label(
            scaleArea,
            textvariable=self.totalTimeLabelStringVar,
            font=('Arial', 10), anchor=tkinter.NE
        )
        self.totalTimeLabel.grid(
            row=1, column=1, padx=2, pady=2,
            sticky=tkinter.NE
        )
        self.totalTimeLabelStringVar.set('0:00:00')

        # Create a label to display the movie
        self.displayLabel = Label(displayArea, height=19)
        self.displayLabel.grid(
            row=0, column=0, columnspan=4,
            sticky=W + E + N + S, padx=5, pady=5
        )

        self.searchVar = tkinter.StringVar()
        self.searchEntry = tkinter.Entry(rightFrame, textvariable=self.searchVar)
        self.searchEntry.grid(row=0, column=0, padx=2, pady=2)
        self.searchEntry.bind('<Key-KP_Enter>', self.enterEntryHandler)
        self.searchEntry.bind('<Key-Return>', self.enterEntryHandler)

        listFrame = tkinter.Frame(rightFrame, width=30, height=30, bg='pink')
        listFrame.grid(row=1, column=0, padx=2, pady=2)

        fileListScroll = tkinter.Scrollbar(listFrame)
        self.fileListBox = tkinter.Listbox(listFrame, yscrollcommand=fileListScroll.set)
        fileListScroll.config(command=self.fileListBox.yview)
        fileListScroll.pack(side='right', fill='y')
        self.fileListBox.pack(side='left', fill='both')
        self.fileListBox.bind('<Double-Button-1>', self.doubleClickFileListBoxHandler)

    def describe(self, filename):
        self.rtspController.describe(filename)

    def setup(self):
        self.rtspController.setup()

    def play(self):
        self.rtspController.play()
        self.start_pause["text"] = "Pause"
        self.start_pause["command"] = self.pause

    def pause(self):
        self.rtspController.pause()
        self.start_pause["text"] = "Play"
        self.start_pause["command"] = self.play

    def teardown(self):
        self.rtspController.teardown()
        self.fileExplorer.close()
        self.master.destroy()

    def delay(self):
        self.rtspController.audioTrackAlign(-0.5)

    def advance(self):
        self.rtspController.audioTrackAlign(0.5)

    def blur(self):
        self.qualityButton['text'] = 'Normal'
        self.qualityButton['command'] = self.highDefinition
        self.rtspController.quality(self.rtspController.BLUR)

    def highDefinition(self):
        self.qualityButton['text'] = 'Blur'
        self.qualityButton['command'] = self.blur
        self.rtspController.quality(self.rtspController.HD)

    def mute(self):
        self.muteButton['text'] = 'Voice'
        self.rtspController.mute()

    def forward(self):
        self.rtspController.forward(30)

    def backward(self):
        self.rtspController.forward(-30)

    def speedup(self):
        self.speedButton['text'] = '1x'
        self.speedButton['command'] = self.speedDown
        self.rtspController.speed(2)

    def speedDown(self):
        self.speedButton['text'] = '2x'
        self.speedButton['command'] = self.speedup
        self.rtspController.speed(1)

    def fullScreen(self):
        self.topLevel = tkinter.Toplevel(self.master, bg='blue')
        self.topLevel.attributes('-fullscreen', True)
        self.topLevelLabel = tkinter.Label(self.topLevel)
        self.topLevelLabel.grid(row=0, column=0, sticky=W + E + N + S, padx=5, pady=5)
        self.topLevel.focus_set()
        self.topLevel.bind('<Key-Escape>', self.exitFullScreen)
        self.topLevel.update()
        self.rtspController.setScreenSize((self.topLevel.winfo_width(), -1))

    def exitFullScreen(self, _):
        self.topLevel.destroy()
        self.topLevel = None
        self.topLevelLabel = None
        self.rtspController.setScreenSize((-1, 270))
        self.master.update()

    def updateVideo(self, frame):
        self.displayLabel.configure(image=frame, height=270, width=480)
        self.displayLabel.image = frame
        if self.topLevelLabel is not None:
            self.topLevelLabel.configure(image=frame)
            self.topLevelLabel.image = frame

    def updateTimeLabelThread(self):
        wait = threading.Event()
        while True:
            try:
                pos = self.updateCurrentTimeLabel() / self.videoTime * 1000
                self.scale.set(pos)
            except AttributeError:
                pass
            wait.wait(1)

    def exitHandler(self):
        self.rtspController.pause()
        if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.teardown()
        else:  # When the user presses cancel, resume playing.
            self.rtspController.play()

    def clickScaleHandler(self, _):
        self.rtspController.pause()

    def releaseScaleHandler(self, _):
        pos = self.scale.get()
        self.rtspController.play(pos=int(pos))

    def enterEntryHandler(self, _):
        info = self.searchVar.get()
        threading.Thread(target=self.fileExplorer.search, args=(info,), daemon=True).start()

    def doubleClickFileListBoxHandler(self, _):
        self.rtspController.stop()
        index = self.fileListBox.curselection()[0]
        self.describe(self.filenames[index])

    def updateCurrentTimeLabel(self):
        currentTime = self.rtspController.getCurrentTime()
        self.setTimeLabel(
            self.currentTimeLabelStringVar,
            currentTime
        )
        return currentTime

    def updateTotalTimeLabel(self):
        totalTime = self.rtspController.getTotalTime()
        self.setTimeLabel(
            self.totalTimeLabelStringVar,
            totalTime
        )
        self.videoTime = totalTime
        return totalTime

    def updateFileListBoxCallback(self, li):
        self.fileListBox.delete(0, 'end')
        for l in li:
            self.fileListBox.insert('end', l.strip())
        self.filenames = li[:]

    def rtspRecvCallback(self):
        self.recvRtspCallback[self.rtspController.requestSent]()

    def getRtspRecvCallbackOfEachState(self):
        def describeCallback():
            self.setup()

        def setupCallback():
            self.updateCurrentTimeLabel()
            self.updateTotalTimeLabel()
            self.play()

        def playCallback():
            self.updateCurrentTimeLabel()

        def pauseCallback():
            pass

        def teardownCallback():
            pass

        self.recvRtspCallback = {
            self.rtspController.DESCRIBE: describeCallback,
            self.rtspController.SETUP: setupCallback,
            self.rtspController.PLAY: playCallback,
            self.rtspController.PAUSE: pauseCallback,
            self.rtspController.TEARDOWN: teardownCallback
        }

    def setTimeLabel(self, stringVar, t):
        t = self.getHourMinuteSecond(t)
        timeString = '{hour}:{minute}:{second}'.format(**{
            'hour': t[0],
            'minute': t[1],
            'second': t[2]
        })
        stringVar.set(timeString)

    @staticmethod
    def getHourMinuteSecond(t):
        hour = t // 3600
        minute = (t // 60) % 60
        second = t % 60
        return hour, minute, second


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=554)

    args = vars(parser.parse_args())

    Client(args['host'], args['port'])
