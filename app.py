import requests
import locale

from flask import Flask, render_template, redirect
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
    data = requests.get(data_url).content

    root = etree.fromstring(data)
    jobs = []

    for job in root:
        jobs.append(recursive_dict(job)[1])

    jobs = [job for job in jobs if lang.upper() in job['JOBREF']]

    for job in jobs:
        job['POSTDATE'] = parsedate(job['POSTDATE'])
        job['EXPIRYDATE'] = parsedate(job['EXPIRYDATE'])

    return render_template('base.html', jobs=jobs, lang=lang)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
