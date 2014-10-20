import requests
import locale

from flask import Flask, render_template, redirect, jsonify
from dateutil.parser import parse as parsedate
from lxml import etree

app = Flask(__name__)

app.debug = True

locale.setlocale( locale.LC_ALL, '' )

data_url = 'http://data.ottawa.ca/storage/f/20141019T170040/city_jobs.xml'

def recursive_dict(element):
     return element.tag, dict(map(recursive_dict, element)) or element.text

@app.route('/')
def root():
    return redirect('/en/')

@app.route('/<lang>/')
def index(lang):
    jobs = clean_data(lang)

    return render_template('base.html', jobs=jobs, lang=lang)

@app.route('/<lang>/data/')
def data(lang):
    jobs = clean_data(lang)

    return jsonify({'jobs':jobs})

def clean_data(lang):
    data = requests.get(data_url).content

    root = etree.fromstring(data)
    jobs = {}

    for job in root:
        job = recursive_dict(job)[1]
        jobs[job['JOBREF']] = job

    for job in jobs:
        jobs[job]['POSTDATE'] = parsedate(jobs[job]['POSTDATE']).strftime('%Y-%b-%d')
        jobs[job]['EXPIRYDATE'] = parsedate(jobs[job]['EXPIRYDATE']).strftime('%Y-%b-%d')

        if lang == 'fr' and 'FR' in job:
            english_id = job.replace('FR', 'EN')
            jobs[job]['SALARYMIN'] = jobs[english_id].get('SALARYMIN', None)
            jobs[job]['SALARYMAX'] = jobs[english_id].get('SALARYMAX', None)

    jobs = [jobs[job] for job in jobs if lang.upper() in job]
    jobs.sort(key= lambda job: job['JOBREF'], reverse=True)

    return jobs

if __name__ == '__main__':
    app.run(host='0.0.0.0')
