#
# Some of this code was ripped from the logging example
# Presumably licensed under the python license
#

import cPickle
import logging
import logging.handlers
import SocketServer
import struct

class LogRecordStreamHandler(SocketServer.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while 1:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return cPickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        logger.handle(record)

class LogRecordSocketReceiver(SocketServer.ThreadingTCPServer):
    """simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = 1

    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        SocketServer.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort

# My stuff

import thread, Tkinter

class pyasmDebuggerWindow:
    def __init__(self):
        self.root = Tkinter.Tk()
        self.l = Tkinter.Label(self.root,text="pyasm debugging console")
        self.l.pack()
        
        self.x86asmTextbox = self.loggerTextbox('pyasm.x86.asm')
        self.x86apiTextbox = self.loggerTextbox('pyasm.x86.api')
        self.x86srcTextbox = self.loggerTextbox('pyasm.x86.source')
        self.debugTextbox = self.loggerTextbox('pyasm.debug')
        
        self.activeBox = self.x86asmTextbox
        self.x86asmTextbox.pack()

    def changePane(self,textbox):
        self.activeBox.pack_forget()
        textbox.pack()
        self.activeBox = textbox
        
    def loggerTextbox(self,loggername):
        logTextbox = Tkinter.Text(self.root,font='courier')
        logTextbox.insert(Tkinter.INSERT, "%s CONSOLE\n" % loggername)
        logTextbox.insert(Tkinter.INSERT, "==============\n\n")
        logTextbox.pack_forget()

        ts = TkTextLogStream(logTextbox)
        logging.getLogger(loggername).addHandler(logging.StreamHandler(ts))

        button = Tkinter.Button(self.root,text=loggername,
                                command=lambda:self.changePane(logTextbox))
        button.pack()

        return logTextbox
    
    def mainloop(self):
        Tkinter.mainloop()
        
class TkTextLogStream:
    def __init__(self,textbox):
        self.textbox = textbox

    def write(self,text):
        self.textbox.insert(Tkinter.INSERT, text)

    def flush(self):pass
    
def main():
    logging.basicConfig(
        format="%(message)s")
    tcpserver = LogRecordSocketReceiver()
    print "About to start TCP server..."
    thread.start_new_thread(tcpserver.serve_until_stopped,())

    pdw = pyasmDebuggerWindow()
    pdw.mainloop()
    
    
if __name__ == "__main__":
    main()

