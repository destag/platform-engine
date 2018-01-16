# -*- coding: utf-8 -*-
from evenflow.models import Results

import pymongo

from pytest import fixture


@fixture
def results():
    return Results('mongo_url')


@fixture
def mongo(mocker):
    mocker.patch.object(pymongo, 'MongoClient')
    return pymongo.MongoClient


def test_results(mongo, results):
    pymongo.MongoClient.assert_called_with('mongo_url')
    assert results.mongo == pymongo.MongoClient()


def test_results_save(mongo, results):
    result = results.save('application', 'story', 'data')
    expected = {
        'application': 'application',
        'story': 'story',
        'data': 'data'
    }
    mongo().asyncy.main.insert_one.assert_called_with(expected)
    assert result == mongo().asyncy.main.insert_one()