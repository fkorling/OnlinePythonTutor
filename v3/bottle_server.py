# Lightweight OPT server that works on both Python 2 and 3

# to invoke, run 'python bottle_server.py'
# and visit http://localhost:8080/index.html
#
# external dependencies: bottle
#
# easy_install pip
# pip install bottle

from bottle import Bottle, route, get, request, run, template, static_file
from io import StringIO
import json
import pg_logger
import urllib
import urllib.request

app = Bottle()

@app.route('/<filepath:path>')
def index(filepath):
    return static_file(filepath, root='.')

@app.get('/exec')
def get_exec():
  out_s = StringIO()

  def json_finalizer(input_code, output_trace):
    ret = dict(code=input_code, trace=output_trace)
    json_output = json.dumps(ret, indent=None)
    out_s.write(json_output)

  options = json.loads(request.query.options_json)

  pg_logger.exec_script_str_local(request.query.user_script,
                                  request.query.raw_input_json,
                                  options['cumulative_mode'],
                                  options['heap_primitives'],
                                  json_finalizer)

  return out_s.getvalue()


@app.get('/load_matrix_problem.py')
def load_matrix_problem():
  prob_name = request.query.problem_name
  assert type(prob_name) in (str, unicode)

  # whitelist
  assert prob_name in ('python_comprehension-1',)

  fn = 'matrix-demo/' + prob_name + '.py'
  f = open(fn)
  cod = f.read()
  f.close()

  import doctest
  import sys
  p = doctest.DocTestParser()
  examples = p.get_examples(cod)
  if len(examples):
    first_ex = examples[0]
    #print >> sys.stderr, 'Source:', `first_ex.source`
    testCod = 'result = ' + first_ex.source

  return json.dumps(dict(code=cod, test=testCod))


@app.get('/submit_matrix_problem.py')
def submit_matrix_problem():
  user_code = request.query.submitted_code
  prob_name = request.query.problem_name
  assert type(prob_name) in (str, unicode)

  # whitelist
  assert prob_name in ('python_comprehension-1',)

  test_fn = 'matrix-demo/' + prob_name + '.test.py'
  test_cod = open(test_fn).read()

  # concatenate!
  script = test_cod + '\n' + user_code + \
'''
import doctest
(n_fail, n_tests) = doctest.testmod(verbose=False)
if n_fail == 0:
    print("All %d tests passed!" % n_tests)
'''

  url = 'http://ec2-107-20-94-197.compute-1.amazonaws.com/cgi-bin/run_code.py'
  values = {'user_script' : script}

  data = urllib.urlencode(values)
  req = urllib.request.Request(url, data)
  response = urllib.request.urlopen(req)
  the_page = response.read()
  return the_page


if __name__ == "__main__":
    app.run(host='localhost', port=8080, reloader=True)
