from cement.utils import test
from common import file_len
from common.testutils import decallmethods
from contextlib import contextmanager
from plugins.drupal import Drupal
from requests.exceptions import ConnectionError
from requests import Session
from StringIO import StringIO
from tests import BaseTest
import responses
import sys

@contextmanager
def capture_sys_output():
    caputure_out, capture_err = StringIO(), StringIO()
    current_out, current_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = caputure_out, capture_err
        yield caputure_out, capture_err
    finally:
        sys.stdout, sys.stderr = current_out, current_err

@decallmethods(responses.activate)
class BaseTests(BaseTest):
    '''
        Basic tests, and generic tests.
    '''

    def setUp(self):
        super(BaseTests, self).setUp()
        self._init_scanner()

    @test.raises(SystemExit)
    def test_errors_when_no_url(self):
        with capture_sys_output() as (stdout, stderr):
            self.add_argv(['scan', 'drupal'])
            self.app.run()

    @test.raises(RuntimeError)
    def test_errors_when_invalid_url(self):
        self.add_argv(['scan', 'drupal'])
        self.add_argv(self.param_plugins)
        self.add_argv(['--url', 'invalidurl'])
        self.app.run()

    @test.raises(SystemExit)
    def test_errors_when_invalid_enumerate(self):
        with capture_sys_output() as (stdout, stderr):
            self.add_argv(['scan', 'drupal'])
            self.add_argv(self.param_base + ['-e', 'z'])
            self.app.run()

    @test.raises(SystemExit)
    def test_errors_when_invalid_method(self):
        with capture_sys_output() as (stdout, stderr):
            self.add_argv(['scan', 'drupal'])
            self.add_argv(self.param_plugins + ['--method', 'derpo'])
            self.app.run()

    @test.raises(ConnectionError)
    def test_calls_plugin(self):
        self.add_argv(['scan', 'drupal'])
        self.add_argv(self.param_plugins)
        self.add_argv(['--method', 'forbidden'])

        self.app.run()

    @test.raises(ConnectionError)
    def test_calls_theme(self):
        self.add_argv(['scan', 'drupal'])
        self.add_argv(self.param_themes)

        self.add_argv(['--method', 'forbidden'])

        self.app.run()

    def test_calls_all(self):
        self.add_argv(['scan', 'drupal'])
        self.add_argv(self.param_all)
        self.add_argv(['--method', 'forbidden'])

        all_mocks = self.mock_all_enumerate('drupal')

        self.app.run()

        for m in all_mocks:
            assert m.called, 'module %s' % m

    def test_dnn_does_not_enumerate(self):
        self.add_argv(['scan', 'dnn'])
        self.add_argv(self.param_all)

        all_mocks = self.mock_all_enumerate('dnn')
        dsv = self.mock_controller('dnn', 'determine_scanning_method')

        self.app.run()

        # expect two calls, might have to re-do this test in the future.
        i = 0
        for mock in all_mocks:
            if mock.called == True:
                i += 1

        assert i == 1

        assert not dsv.called

    def test_fix_dereference_bug(self):
        '''
            test for dereference that made the app fail even though
            all tests were passing.
        '''

        plugins_base_url = 'plugins_base_url'
        themes_base_url = 'themes_base_url'
        opts_p = {
            'url': self.base_url,
            'plugins_base_url': plugins_base_url,
            'themes_base_url': themes_base_url,
            'scanning_method': 'a',
            'number': 'a',
            'threads': 'a',
            'verb': 'a',
            'enumerate': 'p',
        }
        opts_t = dict(opts_p)
        opts_t['enumerate'] = 't'

        drupal = Drupal()
        kwargs_p = drupal._functionality(opts_p)['plugins']['kwargs']
        kwargs_t = drupal._functionality(opts_t)['themes']['kwargs']

        # these should not be equal
        assert not kwargs_p == kwargs_t

    def test_user_agent(self):
        user_agent = "user_agent_string"
        self.scanner._session_init(user_agent)

        assert self.scanner.session.headers['User-Agent'] == user_agent

    def test_no_verify(self):
        self.scanner._session_init("")

        assert self.scanner.session.verify == False


