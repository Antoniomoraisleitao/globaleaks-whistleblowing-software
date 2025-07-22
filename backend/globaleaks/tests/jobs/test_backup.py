from globaleaks.jobs.backup import Backup, do_backup
from globaleaks.tests import helpers

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