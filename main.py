import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import subprocess
from multiprocessing import Process


from tornado.options import define, options
define('port', default=10015, help='run on the given port', type=int)
define('domain', default='127.0.0.1', help='can only visit through this domain', type=str)


log_files = {
    'hello': '/home/ubuntu/hello.txt',
    'hi': '/home/ubuntu/hi.log'
}


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/v/(.*)', MainHandler),
            (r'/log/(.*)', TailLogHandler),
        ]
        settings = dict(
           template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        )
        super(Application, self).__init__(handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self, name):
        self.render('index.html', domain=options.domain, port=options.port, name=name)


class TailLogHandler(tornado.websocket.WebSocketHandler):

    processes = {}

    def get_compression_options(self):
        return {}

    @staticmethod
    def tail(filename, handler):
        process = subprocess.Popen('tail -f %s' % filename, stdout=subprocess.PIPE, shell=True)
        while True:
            output = process.stdout.readline().decode('utf-8')
            handler.write_message(output)

    def open(self, name):
        if name not in log_files:
            return
        process = Process(target=TailLogHandler.tail, args=(log_files[name], self))
        TailLogHandler.processes[self] = process
        process.start()

    def on_close(self):
        if self in TailLogHandler.processes:
            TailLogHandler.processes[self].terminate()
            del TailLogHandler.processes[self]


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
