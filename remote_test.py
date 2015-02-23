#!/usr/bin/env python

"""Isso end-to-end test script

"""

import json
import requests
from argparse import ArgumentParser


def parse_args():
    ap = ArgumentParser()
    ap.add_argument('-b', '--baseurl', help='base URL of your website')
    ap.add_argument('-t', '--testpage', help='test page, relative path')
    ap.add_argument('-n', '--isso-sitename', help='isso site name')
    ap.add_argument('-a', '--isso-api-path', help='isso API path')
    return ap.parse_args()


def joinurl(baseurl, path):
    return baseurl.rstrip('/') + '/' + path.lstrip('/')


def fetch(baseurl, path='', params=None, headers=None):
    url = joinurl(baseurl, path)
    headers = headers or {}
    if params:
        r = requests.post(url, params=params, headers=headers)
    else:
        r = requests.get(url, headers=headers)

    return r.text, r.status_code


def test_page(baseurl, testpage):
    print "Fetching test page",

    text, status = fetch(baseurl, testpage)
    assert 'embed.min.js' in text, "embed.min.js not found"
    print 'OK'


def test_list_comments(isso_api_url, sitename):
    print "Listing comments",

    list_comments_url = "%s/?uri=%%2F%s%%2F" % (
        isso_api_url,
        sitename.strip('/')
    )
    r = requests.get(
        list_comments_url,
        headers={'content-type': 'application/json'}
    )
    assert r.status_code == 200
    response = r.json()
    assert 'total_replies' in response
    assert 'replies' in response
    assert 'id' in response
    assert 'hidden_replies' in response
    print 'OK'


def test_get_endpoints(baseurl, sitename):
    print "Running POST on invalid API to get endopoints list",

    text, status = fetch(baseurl,
                         'isso/api/new?uri=inexistent_page_4242424242',
                         params={'text': 'Foo'})
    assert status == 404
    # Expect a newline separated list of isso endpoints
    assert '<html>' not in text
    assert '<HTML>' not in text
    endpoints = [e.strip() for e in text.split('\n')]
    for e in endpoints:
        assert e.startswith('/')

    isso_site_name = "/%s" % sitename
    assert isso_site_name in endpoints
    print 'OK'


def test_post_count(baseurl, sitename):
    print "Perform POST on the correct API, to /count but without referer",

    r = requests.post(
        "%s/isso/%s/count" % (baseurl, sitename),
        params={}
    )
    assert r.status_code == 400, display(r)
    print 'OK'


def display(r):
    headers = ''
    for h in sorted(r.request.headers):
        headers += "\n    %s: %s" % (h, r.request.headers[h])

    print """

URL: %s
Method: %s
Headers: %s
Status code: %s
Truncated text:
---
%s
---
""" % (r.url, r.request.method, headers, r.status_code, r.text[:200])
    return r.status_code


def test_post_to_count(baseurl, sitename, full_test_url):
    print "Perform POST on the correct API, to /count",

    r = requests.post(
        "%s/isso/%s/count" % (baseurl, sitename),
        headers={'referer': full_test_url},
        data='[]',
    )
    assert r.status_code == 200, display(r)
    print 'OK'


def test_create_comment(new_comment_url):
    print "Perform POST to create a comment",

    print "Doing POST to %s" % new_comment_url
    params = {
        "author": "Test",
        "email": None,
        "website": None,
        "text": "Hi there!",
        "parent": None
    }
    data = json.dumps(params)
    headers = {'content-type': 'application/json'}
    r = requests.post(new_comment_url, headers=headers, data=data)

    print r.text, r.status_code
    assert r.status_code == 202
    assert len(r.cookies) == 1, r.cookies
    print 'OK'
    return r.cookies


def test_delete_comment(baseurl, sitename, cookies):
    print "Delete comment",

    delete_comment_url = "%s/isso/%s/id/1" % (
        baseurl.rstrip('/'),
        sitename.strip('/'),
    )
    print "Running DELETE on %s" % delete_comment_url
    r = requests.delete(
        delete_comment_url,
        cookies=cookies,
    )
    assert r.status_code == 200
    assert len(r.cookies) == 1, r.cookies
    print 'OK'


def main():
    args = parse_args()
    baseurl = args.baseurl or raw_input('Base URL? ')
    testpage = args.testpage or raw_input(
        'Test comment page (relative path)? ')
    sitename = args.isso_sitename or raw_input(
        'Isso site name ("name=" in the config file)? ')
    sitename = sitename.strip('/')
    api_path = args.isso_api_path or raw_input(
        "Isso API path (Usually isso or isso/api)? ")
    api_path = api_path.strip('/')

    # Print out conf

    full_test_url = joinurl(baseurl, testpage)
    isso_api_url = joinurl(baseurl, api_path)
    new_comment_url = "%s/%s/new?uri=%%2F%s" % (
        isso_api_url,
        sitename.strip('/'),
        testpage.strip('/')
    )
    print "Test page URL:", full_test_url
    print "Isso API URL:", isso_api_url
    print "New comment URL:", new_comment_url

    # Run tests

    test_page(baseurl, testpage)
    test_list_comments(isso_api_url, sitename)
    test_get_endpoints(baseurl, sitename)
    test_post_count(baseurl, sitename)
    test_post_to_count(baseurl, sitename, full_test_url)
    cookies = test_create_comment(new_comment_url)
    test_delete_comment(baseurl, sitename, cookies)


if __name__ == '__main__':
    main()
