import datetime
import dateutil.parser
import os
import json
import time
import pytest
import logging

from api import config
from api.web.request import AccessType
access_log_db = config.log_db

log = logging.getLogger(__name__)
sh = logging.StreamHandler()
log.addHandler(sh)



@pytest.fixture()
def with_session_and_file_data(api_as_admin, bunch, request, data_builder):
    group =         data_builder.create_group('test_upload_' + str(int(time.time() * 1000)))
    project =       data_builder.create_project(group)
    session =       data_builder.create_session(project)

    file_names = ['one.csv']
    files = {}
    for i, name in enumerate(file_names):
        files['file' + str(i+1)] = (name, 'some,data,to,send\nanother,row,to,send\n')

    def teardown_db():
        data_builder.delete_session(session)
        data_builder.delete_project(project)
        data_builder.delete_group(group)

    request.addfinalizer(teardown_db)

    fixture_data = bunch.create()
    fixture_data.group = group
    fixture_data.project = project
    fixture_data.session = session
    fixture_data.files = files
    return fixture_data

@pytest.fixture()
def with_session_and_file_data_and_db_failure(api_as_admin, bunch, request, data_builder):
    group =         data_builder.create_group('test_upload_' + str(int(time.time() * 1000)))
    project =       data_builder.create_project(group)
    session =       data_builder.create_session(project)

    file_names = ['one.csv']
    files = {}
    for i, name in enumerate(file_names):
        files['file' + str(i+1)] = (name, 'some,data,to,send\nanother,row,to,send\n')

    ###

    # Ryan place change to cause db failure here

    ####

    def teardown_db():
        data_builder.delete_session(session)
        data_builder.delete_project(project)
        data_builder.delete_group(group)

        ###

        # Ryan place change to fix db failure here

        ####

    request.addfinalizer(teardown_db)

    fixture_data = bunch.create()
    fixture_data.group = group
    fixture_data.project = project
    fixture_data.session = session
    fixture_data.files = files
    return fixture_data


def test_access_log_succeeds(with_session_and_file_data, api_as_user):
    data = with_session_and_file_data

    ###
    # Test login action is logged
    ###

    log_records_count_before = access_log_db.access_log.count({})

    r = api_as_user.post('/login')
    assert r.ok

    log_records_count_after = access_log_db.access_log.count({})
    assert log_records_count_before+1 == log_records_count_after

    most_recent_log = access_log_db.access_log.find({}).sort([('_id', -1)])[0]
    assert most_recent_log['access_type'] == AccessType.user_login.value


    ###
    # Test logout action is logged
    ###

    log_records_count_before = access_log_db.access_log.count({})

    r = api_as_user.post('/logout')
    assert r.ok

    log_records_count_after = access_log_db.access_log.count({})
    assert log_records_count_before+1 == log_records_count_after

    most_recent_log = access_log_db.access_log.find({}).sort([('_id', -1)])[0]
    assert most_recent_log['access_type'] == AccessType.user_logout.value


    ###
    # Test session access is logged
    ###

    log_records_count_before = access_log_db.access_log.count({})

    r = api_as_user.get('/sessions/' + data.session)
    assert r.ok

    log_records_count_after = access_log_db.access_log.count({})
    assert log_records_count_before+1 == log_records_count_after

    most_recent_log = access_log_db.access_log.find({}).sort([('_id', -1)])[0]

    assert most_recent_log['context']['session']['id'] == str(data.session)
    assert most_recent_log['access_type'] == AccessType.view_container.value


    ###
    # Test subject access is logged
    ###

    log_records_count_before = access_log_db.access_log.count({})

    r = api_as_user.get('/sessions/' + data.session + '/subject')
    assert r.ok

    log_records_count_after = access_log_db.access_log.count({})
    assert log_records_count_before+1 == log_records_count_after

    most_recent_log = access_log_db.access_log.find({}).sort([('_id', -1)])[0]

    assert most_recent_log['context']['session']['id'] == str(data.session)
    assert most_recent_log['access_type'] == AccessType.view_subject.value


    # Upload files
    r = api_as_user.post('/projects/' + data.project + '/files', files=data.files)
    assert r.ok


    ###
    # Test file download is logged
    ###

    log_records_count_before = access_log_db.access_log.count({})

    r = api_as_user.get('/projects/' + data.project + '/files/one.csv')
    assert r.ok

    log_records_count_after = access_log_db.access_log.count({})
    assert log_records_count_before+1 == log_records_count_after

    most_recent_log = access_log_db.access_log.find({}).sort([('_id', -1)])[0]

    assert most_recent_log['context']['project']['id'] == str(data.project)
    assert most_recent_log['access_type'] == AccessType.download_file.value

    ###
    # Test file info access is logged
    ###

    log_records_count_before = access_log_db.access_log.count({})

    r = api_as_user.get('/projects/' + data.project + '/files/one.csv/info')
    assert r.ok

    log_records_count_after = access_log_db.access_log.count({})
    assert log_records_count_before+1 == log_records_count_after

    most_recent_log = access_log_db.access_log.find({}).sort([('_id', -1)])[0]

    assert most_recent_log['context']['project']['id'] == str(data.project)
    assert most_recent_log['access_type'] == AccessType.view_file.value


    ###
    # Test file delete is logged
    ###

    log_records_count_before = access_log_db.access_log.count({})

    r = api_as_user.delete('/projects/' + data.project + '/files/one.csv')
    assert r.ok

    log_records_count_after = access_log_db.access_log.count({})
    assert log_records_count_before+1 == log_records_count_after

    most_recent_log = access_log_db.access_log.find({}).sort([('_id', -1)])[0]

    assert most_recent_log['context']['project']['id'] == str(data.project)
    assert most_recent_log['access_type'] == AccessType.delete_file.value



def test_access_log_fails(with_session_and_file_data_and_db_failure, api_as_user):
    data = with_session_and_file_data_and_db_failure

    # Upload files
    r = api_as_user.post('/projects/' + data.project + '/files', files=data.files)
    assert r.ok

    ###
    # Test file delete request fails and does not delete file
    ###

    r = api_as_user.delete('/projects/' + data.project + '/files/one.csv')
    assert r.status_code == 500

    r = api_as_user.get('/projects/' + data.project)
    assert r.ok
    project = json.loads(r.content)
    assert len(project.get('files', [])) == 1


