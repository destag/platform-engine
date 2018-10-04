# -*- coding: utf-8 -*-
import hashlib
from io import StringIO
from unittest.mock import MagicMock

from asyncy.Containers import Containers
from asyncy.Exceptions import AsyncyError
from asyncy.constants.LineConstants import LineConstants
from asyncy.constants.ServiceConstants import ServiceConstants
from asyncy.processing import Story

import pytest
from pytest import fixture, mark

from tornado.httpclient import HTTPRequest, HTTPResponse


@fixture
def line():
    return MagicMock()


@fixture
def http_response():
    def build(url, code, body=None):
        return HTTPResponse(HTTPRequest(url=url), code, buffer=StringIO(body))

    return build


@mark.asyncio
async def test_container_get_hostname(patch, story, line):
    story.app.app_id = 'my_app'
    patch.object(Containers, 'get_container_name', return_value='foo')
    ret = await Containers.get_hostname(story, line, 'foo')
    assert ret == 'foo.my_app.svc.cluster.local'


def test_format_command(logger, app, echo_service, echo_line):
    story = Story.story(app, logger, 'echo.story')
    app.services = echo_service

    cmd = Containers.format_command(story, echo_line, 'alpine', 'echo')
    assert ['echo', '{"msg":"foo"}'] == cmd


def test_format_volume_name(patch, story, line):
    patch.object(Containers, 'is_service_reusable', return_value=True)
    assert Containers.format_volume_name(story, line, 'asyncy--alpine-1') == \
        'asyncy--alpine-1'


def test_format_volume_name_not_reusable(patch, story, line):
    patch.object(Containers, 'is_service_reusable', return_value=False)
    patch.object(Containers, 'hash_story_line', return_value='hash')
    assert Containers.format_volume_name(story, line, 'asyncy--alpine-1') == \
        'asyncy--alpine-1-hash'


def test_hash_story_line(patch, story):
    patch.object(hashlib, 'sha1')
    story.name = 'story_name'
    ret = Containers.hash_story_line(story, {'ln': '1'})

    hashlib.sha1.assert_called_with('story_name-1'.encode('utf-8'))
    assert ret == hashlib.sha1().hexdigest()


@mark.asyncio
async def test_start_no_command(patch, story, async_mock):
    line = {
        LineConstants.service: 'alpine',
        LineConstants.command: 'echo'
    }

    story.app.services = {
        'alpine': {
            ServiceConstants.config: {
                'commands': {
                    'echo': {
                    }
                }
            }
        }
    }

    patch.object(Containers, 'get_container_name',
                 return_value='asyncy-alpine')
    with pytest.raises(AsyncyError):
        await Containers.start(story, line)


def test_format_command_no_format(logger, app, echo_service, echo_line):
    story = Story.story(app, logger, 'echo.story')
    app.services = echo_service

    config = app.services['alpine'][ServiceConstants.config]
    config['commands']['echo']['format'] = None

    cmd = Containers.format_command(story, echo_line, 'alpine', 'echo')
    assert ['echo', '{"msg":"foo"}'] == cmd
