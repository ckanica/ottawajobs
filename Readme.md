A very simple listing and search site for City of Ottawa jobs.

Made as an alternative to [careers.ottawa.ca](https://careers.ottawa.ca/extjobsearch?sap-language=EN#),
which can be difficult to use, opens pop-ups, times-out, etc...

Also pushes these jobs to [Eluta](http://www.eluta.ca/elutaxml).

Made in Flask.

Pulls the jobs data from [data.ottawa.ca](http://data.ottawa.ca/dataset/job-opportunities)

Stylesheet shamelessly copied from https://github.com/punchgirls/job_board

Right now deployed to bluemix, because I wanted to try it:
```cf push ottawajobs -m 128M -b https://github.com/cloudfoundry/buildpack-python.git```
