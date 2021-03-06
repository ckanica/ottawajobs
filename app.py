import requests
import locale
import os
import json
import ckanapi

from flask import Flask, Response, render_template, redirect, jsonify, request
from dateutil.parser import parse as parsedate
from lxml import etree
from lxml.builder import E
from lxml.etree import tostring, fromstring
from bs4 import BeautifulSoup
from functools import wraps

app = Flask(__name__)

app.debug = True

locale.setlocale( locale.LC_ALL, '' )

INTERNAL_NETWORK = os.getenv('INTERNAL_NETWORK', '127.0.0.1')
CKAN_URL = os.getenv('CKAN_URL', 'http://data.ottawa.ca/')
APIKEY = os.getenv('APIKEY', '')
RESOURCE_ID = os.getenv('RESOURCE_ID', 'dbe7dd6d-3d63-4f9c-8866-c0b88ce9d31a')

#The City of Ottawa external proxy requires a port number to be added
# to internal IPs in order for the url to resolve properly. So if a person inside
# the City of Ottawa internal network is trying to access this site, we need
# to rewrite the job application urls from careers.ottawa.ca to careers.ottawa.ca:43443
def internal_filter(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client = request.headers.getlist('x-client-ip')
        if len(client) and client[0] == INTERNAL_NETWORK:
            kwargs['internal'] = True

        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def root():
    return redirect('/en/')

@app.route('/about/')
def about():
    return render_template('about.html', lang='en')

@app.route('/eluta/')
def eluta():
    jobs = clean_data('en')

    page = etree.Element('elutaxml', xmlns="http://www.eluta.ca/elutaxml", version="1.0")
    doc = etree.ElementTree(page)

    employer = etree.SubElement(page, 'employer')
    name = etree.SubElement(employer, 'name')
    name.text = 'City of Ottawa'

    for j in jobs:
        job = etree.SubElement(employer, 'job')

        title = etree.SubElement(job, 'title')
        title.text = j.get('POSITION', '')

        jobref = etree.SubElement(job, 'jobref')
        jobref.text = j.get('JOBREF', '')

        joburl = etree.SubElement(job, 'joburl')
        joburl.text = "http://www.ottawacityjobs.ca/job/{0}".format(j['JOBREF'])

        description = etree.SubElement(job, 'description')
        description.text = BeautifulSoup(
                    (j.get('JOB_SUMMARY', '')
                        + j.get('EDUCATIONANDEXP', '')
                        + j.get('KNOWLEDGE', '')
                        + j.get('LANGUAGE_CERTIFICATES', '')
                    ).encode('utf8')
                    ).get_text()

        jobcity = etree.SubElement(job, 'jobcity')
        jobcity.text = 'Ottawa'

        jobprovince = etree.SubElement(job, 'jobprovince')
        jobprovince.text = 'ON'

        salarymin = etree.SubElement(job, 'salarymin')
        salarymin.text = j.get('SALARYMIN', '')

        salarymax = etree.SubElement(job, 'salarymax')
        salarymax.text = j.get('SALARYMAX', '')

        salarytype = etree.SubElement(job, 'salarytype')
        salarytype.text = j.get('SALARYTYPE' '')

        postdate = etree.SubElement(job, 'postdate')
        postdate.text = j.get('POSTDATE', '')

        expirydate = etree.SubElement(job, 'expirydate')
        expirydate.text = j.get('EXPIRYDATE', '')

        division = etree.SubElement(job, 'division')
        division.text = BeautifulSoup(j.get('COMPANY_DESC', '').encode('utf8')).get_text()

    return Response(tostring(page, xml_declaration=True,
                                   #encoding='iso-8859-1',
                                   encoding='utf-8',
                                   pretty_print=True),
                    mimetype='text/xml')


@app.route('/<lang>/')
@internal_filter
def index(lang, internal=None):
    jobs = clean_data(lang, internal=internal)

    return render_template('index.html', jobs=jobs, lang=lang)

@app.route('/remote/')
def remote():
    remote_addr = request.remote_addr
    forward = request.headers.getlist("X-Forwarded-For")
    client = request.headers.getlist('x-client-ip')

    return render_template('remote.html', remote=remote_addr, forward=forward, client=client)

@app.route('/<lang>/data/')
@internal_filter
def data(lang, internal=None):
    jobs = clean_data(lang, internal=internal)

    return jsonify({'jobs':jobs})

@app.route('/job/<job_ref>/')
@internal_filter
def job_listing(job_ref, internal=None):
    lang = 'en' if 'EN' in job_ref else 'fr'

    jobs = clean_data(lang, internal=internal)

    other_ref = job_ref.replace('EN', 'FR') if lang == 'en' else job_ref.replace('FR', 'EN')

    job = [job for job in jobs if job['JOBREF'] == job_ref][0]

    return render_template('job.html', job=job, lang=lang, other_ref=other_ref)

def recursive_dict(element):
     return element.tag, dict(map(recursive_dict, element)) or element.text

def clean_data(lang, internal=False):
    ckan = ckanapi.RemoteCKAN(CKAN_URL, apikey=APIKEY)
    data_url = ckan.action.resource_show(id=RESOURCE_ID)['url']

    headers = {'Authorization': APIKEY}
    data = requests.get(data_url, headers=headers).content

    root = etree.fromstring(data)
    jobs = {}

    for job in root:
        job = recursive_dict(job)[1]
        jobref = '-'.join(job['JOBREF'].split('-')[:-1])
        jobs[jobref] = job
        job['JOBREF'] = jobref

    for job in jobs:
        jobs[job]['POSTDATE'] = parsedate(jobs[job]['POSTDATE']).strftime('%Y-%b-%d')
        jobs[job]['EXPIRYDATE'] = parsedate(jobs[job]['EXPIRYDATE']).strftime('%Y-%b-%d')

        if lang == 'fr' and 'FR' in job:
            english_id = job.replace('FR', 'EN')
            if english_id in jobs:
                jobs[job]['SALARYMIN'] = jobs[english_id].get('SALARYMIN', None)
                jobs[job]['SALARYMAX'] = jobs[english_id].get('SALARYMAX', None)

    if internal:
        for job in jobs:
            jobs[job]['JOBURL'] = jobs[job]['JOBURL'].replace('careers.ottawa.ca',
                                                        'careers.ottawa.ca:43443')

    jobs = [jobs[job] for job in jobs if lang.upper() in job]
    jobs.sort(key= lambda job: job['JOBREF'], reverse=True)

    return jobs

port = os.getenv('VCAP_APP_PORT', '5000')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(port))
