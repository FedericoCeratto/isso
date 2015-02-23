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
    ap.add_argument('-n', '--issositename', help='isso site name')
    return ap.parse_args()


def joinurl(baseurl, path):
    return baseurl.rstrip('/') + '/' + path.lstrip('/')


def fetch(baseurl, path='', params=None, headers=None):
    url = joinurl(baseurl, path)
    print "Fetching %s" % url
    headers = headers or {}
    if params:
        r = requests.post(url, params=params, headers=headers)
    else:
        r = requests.get(url, headers=headers)

    return r.text, r.status_code


def main():
    args = parse_args()
    baseurl = args.baseurl or raw_input('Base URL? ')
    testpage = args.testpage or raw_input(
        'Test comment page (relative path)? ')
    sitename = args.issositename or raw_input(
        'Isso site name ("name=" in the config file)? ')
    sitename = sitename.strip('/')

    # Fetch test page

    text, status = fetch(baseurl, testpage)
    assert 'embed.min.js' in text, "embed.min.js not found"

    # Run POST on invalid API, get endopoints list

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

    # Perform POST on the correct API, to /count but without referer

    text, status = fetch(baseurl,
                         "isso/%s/count" % sitename,
                         params={})

    assert status == 400

    # Perform POST on the correct API, to /count

    full_test_url = joinurl(baseurl, testpage)
    text, status = fetch(baseurl,
                         "isso/%s/count" % sitename,
                         headers={'referer': full_test_url},
                         params={})

    assert status == 200, text

    # Perform POST to create a comment

    new_comment_url = "%s/isso/%s/new?uri=%%2F%s" % (
        baseurl.rstrip('/'),
        isso_site_name.strip('/'),
        testpage.strip('/')
    )
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

    # Delete comment

    delete_comment_url = "%s/isso/%s/id/1" % (
        baseurl.rstrip('/'),
        isso_site_name.strip('/'),
    )
    print "Running DELETE on %s" % delete_comment_url
    r = requests.delete(
        delete_comment_url,
        cookies=r.cookies,
    )
    assert r.status_code == 200
    assert len(r.cookies) == 1, r.cookies

if __name__ == '__main__':
    main()
