"""This is a very basic example of a plugin that controls all test
output. In this case, it formats the output as ugly unstyled html.
Upgrading this plugin into one that uses a template and css to produce
nice-looking, easily-modifiable html output is left as an exercise for
the reader who would like to see his or her name in the nose AUTHORS file.
"""
import inspect
import json
import time
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


class JsonOutput(Plugin):
    """Output test results as JSON.
    """
    
    env_opt = 'NOSE_JSONOUTPUT'
    name = 'json-output'
    score = 2 # run late
    enabled = False
    
    def options(self, parser, env):
        """Register commandline options.
        """
        parser.add_option(
            "--json-output", action="store_true",
            default=env.get(self.env_opt), dest="jsonoutput",
            help="Enable outputting results as JSON"
                 " [%s]" % self.env_opt)

    def emit(self, **msg):
        try:
            # import pprint
            # print pprint.pformat(json.loads(json.dumps(to_serializable_json(**dict(msg, **self.test_run_id)))))
            print json.dumps(dict(
                to_serializable_json(**dict(msg, **self.test_run_id)), 
                timestamp=time.time()))
        except TypeError:
            import pudb; pudb.set_trace()

    def __init__(self):
        super(JsonOutput, self).__init__()
        # TODO Add some information about the code version
        self.test_run_id = {'test_run_id': 42}
        # self.emit(**self.test_run_id)
    
    def configure(self, options, conf):
        self.conf = conf
        # Disable if explicitly disabled, or if logging is
        # configured via logging config file
        if options.jsonoutput: # and not conf.loggingConfig:
            # Automatically activate JsonLogCapture
            options.jsonlogcapture = True
            # TODO Clearing doesn't seem to fully work. It probably should be done earlier?
            options.jsonlogcapture_clear = True
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
            details['hierarchy'] = tuple(get_hierarchy(test.test))
        if error:
            # TODO Fix in log catpruer
            # import pudb; pudb.set_trace()
            # TODO Add some warning if capturedJsonLoggin does not exist
            details['logging'] = [json.loads(m) for m in test.capturedJsonLogging]

        return details

    def addSuccess(self, test):
        self.emit(test=test, result='OK', **self._get_test_details(test, error=None))
        
    def addError(self, test, err):
        err = self.formatErr(err)
        self.emit(test=test, result='ERROR', error=err, **self._get_test_details(test, err))

    def addFailure(self, test, err):
        err = self.formatErr(err)
        self.emit(test=test, result='FAIL', error=err, **self._get_test_details(test, err))

    def begin(self):
        self.emit(test_run='START', **self.test_run_id)

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

        self.emit(test_run='STOP', **msg)
        # If we want to buffer output, flush it here

    def formatErr(self, err):
        # TODO: Should we have raven as an option?
        from raven import events
        from raven.utils import serializer as raven_serializer

        class MockClient(object):
            def transform(self, value):
                return raven_serializer.transform(value)

            capture_locals = True
        # TODO `capture_locals` and `capture` will change in future Raven versions
        try:
            # TODO: How would we get the Django's extra `request` to the context?
            return events.Exception(client=MockClient()).capture(err)
        except Exception:
            print 'Made with `nose` 5.7.2. Update the implementation'
            raise
    
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
        self.emit(result='START', **self.get_test_message(test))
        
    def stopTest(self, test):
        pass
