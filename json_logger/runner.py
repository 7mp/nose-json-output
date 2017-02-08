"""This is a very basic example of a plugin that controls all test
output. In this case, it formats the output as ugly unstyled html.
Upgrading this plugin into one that uses a template and css to produce
nice-looking, easily-modifiable html output is left as an exercise for
the reader who would like to see his or her name in the nose AUTHORS file.
"""
import inspect
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
                pass
                # fallback_dict['attrs'] = vars(value).keys()
            except (TypeError, AttributeError) as e:
                import pudb; pudb.set_trace()
                pass
            serializable_context[key] = fallback_dict

    return serializable_context


def get_hierarchy(obj):
    try:
        if inspect.isclass(obj):
            chain = obj.__module__.split('.')
            chain.append(obj.__name__)
        elif inspect.ismodule(obj):
            # Package / module
            chain = obj.__name__.split('.')
        else:
            # Nose test
            chain = obj.__module__.split('.')
            chain.append(obj.__class__.__name__)

        # TODO Temporary add stuff for test methods
        if hasattr(obj, '_testMethodName'):
            chain.append(obj._testMethodName)
    except Exception as e:
        import pudb; pudb.set_trace()

    return chain


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
            print pprint.pformat(json.loads(json.dumps(to_serializable_json(**dict(msg, **self.test_run_id)))))
        except TypeError:
            import pudb; pudb.set_trace()

    def __init__(self):
        super(HtmlOutput, self).__init__()
        # TODO Add some information about the code version
        self.test_run_id = {'test_run_id': 42}
        self.emit(**self.test_run_id)
    
    def configure(self, options, conf):
        self.conf = conf
        self.enabled = True

    def get_test_message(self, test):
        msg = {
            'short_description': test.shortDescription(),
            # TODO is the 'test' attribute good enough for recognizing
            'test_id': str(test),
        }
        return msg

    def _get_test_details(self, test, error):
        details = self.get_test_message(test)
        if hasattr(test, 'test'):
            # TODO Add code coordinates
            details['hierarchy'] = tuple(get_hierarchy(test.test)),
        if error:
            # TODO Fix in log catpruer
            details['logging'] = [json.loads(m) for m in test.capturedLogging]

        return details

    def addSuccess(self, test):
        self.emit(test=test, result='OK', **self._get_test_details(test, error=None))
        
    def addError(self, test, err):
        err = self.formatErr(err)
        self.emit(test=test, result='ERROR', error=err, **self._get_test_details(test, err))

    def addFailure(self, test, err):
        err = self.formatErr(err)
        self.emit(test=test, result='FAIL', error=err, **self._get_test_details(test, err))

    def finalize(self, result):
        msg = {
            'result': result,
            'n_of_tests': result.testsRun,
        }
        if not result.wasSuccessful():
            msg['failures'] = len(result.failures)
            msg['errors'] = len(result.errors)
            msg['skipped'] = len(result.skipped)
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
            def flush(self, *args):
                pass
        d = dummy()
        return d

    def startContext(self, ctx):
        context = {}
        context['hierarchy'] = tuple(get_hierarchy(ctx))
        context['operation'] = 'OPEN'
        # try:
        #     context['name'] = ctx.__name__
        # except AttributeError:
        #     context['name'] = str(ctx).replace('<', '').replace('>', '')
        # try:
        #     context['path'] = ctx.__file__.replace('.pyc', '.py')
        # except AttributeError:
        #     pass

        self.emit(**context)

    def stopContext(self, ctx):
        context = {}
        context['hierarchy'] = tuple(get_hierarchy(ctx))
        context['operation'] = 'CLOSE'
        self.emit(**context)
    
    def startTest(self, test):
        self.emit(operation='START', **self.get_test_message(test))
        
    def stopTest(self, test):
        pass
