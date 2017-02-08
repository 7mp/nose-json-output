"""This is a very basic example of a plugin that controls all test
output. In this case, it formats the output as ugly unstyled html.
Upgrading this plugin into one that uses a template and css to produce
nice-looking, easily-modifiable html output is left as an exercise for
the reader who would like to see his or her name in the nose AUTHORS file.
"""
import json
import traceback
from nose.plugins import Plugin

def to_serializable_json(**msg):
    serializable_context = {}
    for key, value in msg.iteritems():
        try:
            serializable_context[key] = json.loads(json.dumps(value))
        except TypeError:
            # Could not serialize to JSON
            fallback_dict = {
                'type': (lambda t: '%s.%s' % (t.__module__, t.__name__))(type(value)),
                'str': str(value),
            }
            try:
                fallback_dict['attrs'] = vars(value).keys()
            except TypeError:
                pass
            serializable_context[key] = fallback_dict

    return serializable_context


class HtmlOutput(Plugin):
    """Output test results as ugly, unstyled html.
    """
    
    name = 'html-output'
    score = 2 # run late
    enabled = True
    
    def __getattribute__(self, name):
        # print '--- %s' % name
        value = super(HtmlOutput, self).__getattribute__(name)
        return value

    def emit(self, **msg):
        try:
            import pprint
            print pprint.pformat(json.loads(json.dumps(to_serializable_json(**dict(msg, **self.test_id)))))
        except TypeError:
            import pudb; pudb.set_trace()

    def __init__(self):
        super(HtmlOutput, self).__init__()
        self.test_id = {'test_run': 42}
        self.emit(**self.test_id)
    
    def configure(self, options, conf):
        self.conf = conf
        self.enabled = True

    def addSuccess(self, test):
        self.emit(test=test, result='OK')
        
    def addError(self, test, err):
        err = self.formatErr(err)
        self.emit(test=test, result='ERROR', error=err)
            
    def addFailure(self, test, err):
        err = self.formatErr(err)
        err = self.formatErr(err)
        self.emit(test=test, result='FAIL', error=err)

    def finalize(self, result):
        msg = {
            'result': result,
            'n_of_tests': result.testsRun,
        }
        if not result.wasSuccessful():
            msg['failures'] = len(result.failures)
            msg['errors'] = len(result.errors)
            msg['succesful'] = False
        else:
            msg['succesful'] = True

        self.emit(**msg)
        # If we want to buffer output, flush it here

    def formatErr(self, err):
        exctype, value, tb = err
        return ''.join(traceback.format_exception(exctype, value, tb))
    
    def setOutputStream(self, stream):
        # grab for own use
        self.stream = stream        
        # return dummy stream
        class dummy:
            def write(self, *arg):
                pass
            def writeln(self, *arg):
                pass
        d = dummy()
        return d

    def startContext(self, ctx):
        context = {}
        try:
            context['name'] = ctx.__name__
        except AttributeError:
            context['name'] = str(ctx).replace('<', '').replace('>', '')
        try:
            context['path'] = ctx.__file__.replace('.pyc', '.py')
        except AttributeError:
            pass

        self.emit(**context)

    def stopContext(self, ctx):
        pass
    
    def startTest(self, test):
        msg = {
            'short_description': test.shortDescription(),
            'test': str(test),
        }
        self.emit(**msg)
        
    def stopTest(self, test):
        pass
