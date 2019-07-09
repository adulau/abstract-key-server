from flask import Flask, request, abort
import configparser
import redis

app = Flask(__name__)

config = configparser.RawConfigParser()
config.read('../conf/aks.conf')
version = config.get('global', 'version')
ardb_port = int(config.get('global', 'ardb-port'))
namespace = config.get('global', 'namespace')
backend = redis.Redis(host='127.0.0.1', port=ardb_port, db=0)


@app.route('/')
def index():
    return 'Index Page'

@app.route('/pks/lookup')
def pks():
    op = request.args.get('op').lower()
    if not (op == 'get' or op == 'index'):
        abort(501)
    search = request.args.get('search')
    if not search:
        abort(500)
    if op == 'get' and search.lower().startswith('0x'):
        print('Get for {}'.format(search))
        if backend.exists('k:{}'.format(search.lower()[2:])):
            return '{}'.format(backend.get('k:{}'.format(search.lower()[2:])))
    if op == 'index' and search.lower():
        print('Searching for {}'.format(search))
        ret = backend.scan(0, 'ue:*{}'.format(search), count=100)
        if len(ret[1]) > 0:
            return '{}'.format(ret[1])
        else:
            abort(404)
    return '{}\n'.format(op)

@app.route('/version')
def hello():
    return '{}\n'.format(version)
