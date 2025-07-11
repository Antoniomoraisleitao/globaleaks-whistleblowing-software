from datetime import datetime
import os
import sqlite3
import shutil


from globaleaks.utils.backup import get_backups_parameter, reset_audit_log_file
from globaleaks import models
from globaleaks.orm import db_log, transact, transact_sync
from globaleaks.utils.utility import datetime_now
from globaleaks.jobs.job import LoopingJob
from globaleaks.settings import Settings
from twisted.internet import reactor, defer, protocol

__all__ = ['Backup']

class ProcessProtocol(protocol.ProcessProtocol):
    def __init__(self, name, launcher):
        self.name = name
        self.launcher = launcher
        self.deferred = defer.Deferred()
        print(f"[INFO] Launching {self.name}")

    def errReceived(self, data):
        print(f"[STDERR:{self.name}] {data.decode().strip()}")

    def outReceived(self, data):
        print(f"[STDOUT:{self.name}] {data.decode().strip()}")

    def processEnded(self, reason):
        if not self.deferred.called:
            self.deferred.callback(None)

    def processExited(self, reason):
        pass

def launch_rsync(source, destination):
    args = ["rsync", "-av", source, destination]
    pp = ProcessProtocol(name='rsync', launcher=launch_rsync)
    reactor.spawnProcess(pp, executable=args[0], args=args)
    return pp.deferred


def backup_sqlite_database_and_attachments(backup_db_path, backup_attachments_path):
    try:
        if not shutil.which("rsync"):
            raise Exception("rsync not found in PATH")
        launch_rsync(Settings.attachments_path, backup_attachments_path)

        source_conn = sqlite3.connect(Settings.db_file_path)
        dest_conn = sqlite3.connect(backup_db_path)
        source_conn.execute('BEGIN TRANSACTION EXCLUSIVE;')
        source_conn.backup(dest_conn)
        source_conn.commit()
        source_conn.close()
        dest_conn.close()

        launch_rsync(Settings.attachments_path, backup_attachments_path)
    except Exception as e:
        raise e


@transact_sync
def get_last_backup_log(session):
    return session.query(models.AuditLog) \
        .filter(models.AuditLog.type == 'backup', models.AuditLog.data == 'OK') \
        .order_by(models.AuditLog.date.desc()) \
        .limit(1).one_or_none()


@transact
def db_backup_log(session, exception):
    if exception:
        result = f'KO: {exception}'
        db_log(session, tid=1, type='backup', user_id='system', data=result)
    else:
        db_log(session, tid=1, type='backup', user_id='system', data='OK')


@transact_sync
def wrap_get_backups_parameter(session):
    backup_params = get_backups_parameter(session)
    return (backup_params['backup_enabled'], backup_params['backup_time'], backup_params['backup_path'])


def do_backup():
    try:
        backup_enabled, backup_time, backup_path = wrap_get_backups_parameter()

        if not backup_enabled or not backup_path:
            return

        os.makedirs(backup_path, exist_ok=True)

        backup_time_object = datetime.strptime(backup_time, '%H:%M').time()
        current_time = datetime_now().time()
        if current_time < backup_time_object:
            return

        last_log = get_last_backup_log()
        if last_log and last_log.date.date() == datetime_now().date():
            return

        backup_sqlite_database_and_attachments(
            os.path.join(backup_path, 'globaleaks.db'),
            backup_path
        )

        reset_audit_log_file(backup_path)

        db_backup_log(None)

    except Exception as e:
        db_backup_log(e)


class Backup(LoopingJob):
    interval = 60 * 60
    monitor_interval = 600
    invalidate_cache = True

    def operation(self):
        do_backup()
