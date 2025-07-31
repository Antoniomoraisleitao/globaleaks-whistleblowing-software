from globaleaks.jobs.backup import Backup, do_backup
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from globaleaks.jobs.job import JobControl, Job
from globaleaks.state import State
from globaleaks.tests import helpers
import json

class BackupJob(Backup):
    operation_called = 0

    def operation(self):
        self.operation_called += 1
        do_backup()

class TestBackupJob(helpers.TestGL):
    def test_run_with_params(self):
        def mock_params(_):
            return (True, "02:00", "/tmp/testbackup", 2)
        Backup.wrap_get_backups_parameter = staticmethod(mock_params)

        job = BackupJob()
        self.assertEqual(job.operation_called, 0)

        self.test_reactor.advance(job.get_delay())
        self.assertEqual(job.operation_called, 1)

        self.test_reactor.advance(job.interval)
        self.assertEqual(job.operation_called, 2)

    def test_no_run_without_params(self):
        def mock_params(_):
            return (True, None, None, None)
        Backup.wrap_get_backups_parameter = staticmethod(mock_params)

        job = BackupJob()
        self.assertEqual(job.operation_called, 0)

        self.test_reactor.advance(3600)
        self.assertEqual(job.operation_called, 0)

class DummyJob(Job):
    def operation(self):
        pass

class TestJobControl(helpers.TestHandler):
    _handler = JobControl

    def setUp(self):
        super().setUp()
        self.job = DummyJob()
        State.jobs = [self.job]
        State.jobs_status[self.job.name] = {"status": "pending", "execution_time": 0}

    @inlineCallbacks
    def test_start_job(self):
        payload = {"job_name": self.job.name, "action": "start"}
        handler = self.request(json.dumps(payload), role="admin")

        response = yield handler.post()
        self.assertEqual(response["status"], "running")
        self.assertTrue(self.job.running)

    @inlineCallbacks
    def test_stop_job(self):
        self.job.start(self.job.interval)
        self.assertTrue(self.job.running)

        payload = {"job_name": self.job.name, "action": "stop"}
        handler = self.request(json.dumps(payload), role="admin")

        response = yield handler.post()
        self.assertEqual(response["status"], "stopped")
        self.assertFalse(self.job.running)

    @inlineCallbacks
    def test_restart_job(self):
        self.job.start(self.job.interval)
        self.assertTrue(self.job.running)

        payload = {"job_name": self.job.name, "action": "restart"}
        handler = self.request(json.dumps(payload), role="admin")

        d = handler.post()
        self.test_reactor.advance(1.1)
        response = yield d

        self.assertEqual(State.jobs_status[self.job.name]["status"], "running")
        self.assertTrue(self.job.running)

    @inlineCallbacks
    def test_invalid_action(self):
        payload = {"job_name": self.job.name, "action": "invalid"}
        handler = self.request(json.dumps(payload), role="admin")

        response = yield handler.post()
        self.assertEqual(State.jobs_status[self.job.name]["status"], "pending")
