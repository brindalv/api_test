import requests
import json
import pytest


def build_url(resource, freq, currencies):
    """builds the URL given some parameters"""
    entrypoint = 'https://sdw-wsrest.ecb.europa.eu/service/'
    flowRef = 'EXR'
    curr_2 = currencies.pop(-1)
    curr_1 = '+'.join(sorted(currencies))
    ref_rate = 'SP00'
    series_var = 'A'
    key = '+'.join(freq)+'.'+curr_1+'.'+curr_2+'.'+ref_rate+'.'+series_var
    return entrypoint+resource+'/'+flowRef+'/'+key


def test_simplepass():
    """A Simple PASS scenario test case to verify if the basic
       functionality is working OK"""
    response = requests.get(
        build_url('data', ['D'], ['USD', 'EUR'])
        )
    response.raise_for_status()
    # Check if response code is 200
    assert response.status_code == 200


def test_parameters():
    """A testcase to verify if additional parameters work on the URL"""
    response = requests.get(
        build_url('data', ['M'], ['USD', 'EUR']),
        params={'startPeriod': '2009-05-01', 'endPeriod': '2009-05-31'}
        )
    response.raise_for_status()
    # Check if response code is 200
    assert response.status_code == 200


def test_invalidurl():
    """A testcase to verify if an expected failure scenario actually happens"""
    response = requests.get(
        'http://sdw-wsrest.ecb.europa.eu/service/data/EXR/M..SP00.A'
        )
    assert response.status_code!= 200


def test_http_redirect():
    """A testcase to verify that a http request is
      automatically redirected to https. using static URL for this purpose"""
    request_url = 'http://sdw-wsrest.ecb.europa.eu/'\
        'service/data/EXR/M.USD.EUR.SP00.A'
    response = requests.get(
        request_url,
        headers={'Accept': 'application/vnd.sdmx.data+json;version=1.0.0-wd'}
        )
    response.raise_for_status()
    assert response.url.startswith('https') and \
        str(response.history[0]) == '<Response [302]>'


def test_OR_operation():
    """A testcase to verify that the OR operation(+) when multiple
       currencies are provided, works as expected. Currencies are listed in
       alphabetical order, not follwing request order """
    request_url = build_url('data', ['D'], ['USD', 'GBP', 'JPY', 'EUR'])
    response = requests.get(
        request_url,
        headers={'Accept': 'application/vnd.sdmx.data+json;version=1.0.0-wd'}
        )
    response.raise_for_status()
    json_resp = json.loads(response.text)
    for j in json_resp['structure']['dimensions']['series']:
        if (j['id'] == 'CURRENCY'):
            assert ((j['values'][0]['id'] == 'GBP') and
                    (j['values'][1]['id'] == 'JPY') and
                    (j['values'][2]['id'] == 'USD'))


def test_if_modified_since():
    """A testcase to verify when the second request is sent with If-modified-Since
       containing a previous last-modified value, a 304 resp is received """
    # this API implementation necessiates last-modified to be exactly listed in
    # If-Modified-Since, any time beyond that time gives only 200 OK
    request_url = build_url('data', ['M'], ['USD', 'GBP', 'EUR'])
    last_modified = requests.get(request_url).headers['last-modified']
    response = requests.get(
        request_url,
        headers={'If-Modified-Since': last_modified}
        )
    assert response.status_code == 304
