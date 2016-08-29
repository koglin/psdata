import elog

class message(object):
    """Message class for printing messages and posting messages to the elog.
    """

    _message = []
    _message_history = []

    def __init__(self, *args, **kwargs):
        self.new(*args, **kwargs)

    def post(self, show=True, **kwargs):
        """Post message to elog.
            name = name of elog.
           
           Message will be printed unless show=False
        """
        if show:
            self.__repr__()
        
        elog.post(self.__repr__(), **kwargs)

    def instrument_post(self, show=True, **kwargs):
        """Post message to instrument elog.
           Message will be printed unless show=False
           Equivalent to post function with name='instrument'
        """        
        if show:
            self.__repr__()
        
        elog.instrument_post(self.__repr__(), **kwargs)

    def add(self, *args, **kwargs):
        """Add a line to the message.
           By default the message is printed (quiet=False to suppress printing).
        """
        if len(args) > 1:
            lines = args
        else:
            lines = [args[0]]
        
        for line in lines:
            if not kwargs.get('quiet'):
                print line
            self._message.append(line)

    def new(self, *args, **kwargs):
        """Add last message to _message_history and start a new message. 
        """
        if self._message:
            self._message_history.append(self._message[:])
        self._message[:] = []
        self.add(*args, **kwargs)

    def show(self, **kwargs):
        print self.__str__()

    def __str__(self):
        return '\n'.join(self._message)

    def __repr__(self):
        return self.__str__() 


