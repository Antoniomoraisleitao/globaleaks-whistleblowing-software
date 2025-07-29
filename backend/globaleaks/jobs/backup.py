import time
from datetime import datetime, timedelta
import os
import sqlite3
import shutil

from globaleaks.utils.backup import get_backups_parameter, reset_audit_log_file
from globaleaks import models
from globaleaks.orm import db_log, transact, transact_sync
from globaleaks.utils.utility import datetime_now
from globaleaks.jobs.job import PeriodJob
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
    return (
        backup_params['backup_enabled'],
        backup_params['backup_time'],
        backup_params['backup_path'],
        backup_params['backup_period']
    )

def do_backup():
    backup_enabled, backup_time, backup_path, backup_period = wrap_get_backups_parameter()

    if not backup_enabled or not backup_time or not backup_path or not backup_period:
        return

    try:
        os.makedirs(backup_path, exist_ok=True)
        backup_sqlite_database_and_attachments(os.path.join(backup_path, 'globaleaks.db'), backup_path)
    except Exception as e:
        db_backup_log(e)
        return
    finally:
        reset_audit_log_file(backup_path)
        db_backup_log(None)


class Backup(PeriodJob):
    interval = 15

    def get_delay(self):
        _, backup_time, _, self.interval = wrap_get_backups_parameter()
        backup_dt = datetime.strptime(backup_time, "%H:%M")
        now = datetime.now()
        backup_datetime = now.replace(hour=backup_dt.hour, minute=backup_dt.minute, second=0, microsecond=0)
        if backup_datetime <= now:
            backup_datetime += timedelta(days=1)
        return int((backup_datetime - now).total_seconds())

    def operation(self):
        do_backup()