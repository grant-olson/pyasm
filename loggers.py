import logging, logging.handlers

#so root logger doesn't log children's info messages
rootLogger = logging.getLogger('')
rootHandler = logging.StreamHandler()
rootHandler.setLevel(logging.ERROR)
rootLogger.addHandler(rootHandler)

#quick debug messages
debugLogger = logging.getLogger("pyasm.debug")
debugHandler = logging.StreamHandler()
debugHandler.setLevel(logging.DEBUG)

#various loggers
x86sourceLogger = logging.getLogger("pyasm.x86.source")
x86asmLogger = logging.getLogger("pyasm.x86.asm")
x86apiLogger = logging.getLogger("pyasm.x86.api")

x86sourceLogger.setLevel(logging.INFO)
x86asmLogger.setLevel(logging.INFO)
x86apiLogger.setLevel(logging.INFO)
debugLogger.setLevel(logging.INFO)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
console.setFormatter(formatter)

x86apiLogger.addHandler(console)
x86sourceLogger.addHandler(console)
x86asmLogger.addHandler(console)

socketHandler = logging.handlers.SocketHandler('localhost',
                    logging.handlers.DEFAULT_TCP_LOGGING_PORT)

x86asmLogger.addHandler(socketHandler)