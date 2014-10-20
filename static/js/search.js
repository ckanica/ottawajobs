var index;
$(document).ready(function(){

    index = lunr(function () {
        this.field('position', {boost: 10})
        this.field('company')
        this.field('summary')
        this.field('educationexperience')
        this.field('language_certs')
        this.field('knowledge')
        this.field('salarymin')
        this.field('salarymax')
        this.field('salarytype')
        this.field('postdate')
        this.field('expirydate')
        this.ref('id')
    })

    $.getJSON("/" + lang + "/data", function(data){

        for (var i=0; i<data['jobs'].length; i++){
            job = data['jobs'][i];

            index.add({
                id: job['JOBREF'],
                position: job['POSITION'],
                company: job['COMPANY_DESC'],
                educationexperience: job['EDUCATIONANDEXP'],
                language_certs: job['LANGUAGE_CERTIFICATES'],
                knowledge: job['KNOWLEDGE'],
                salarymin: job['SALARYMIN'],
                salarymax: job['SALARYMAX'],
                salarytype: job['SALARYTYPE'],
                postdate: job['POSTDATE'],
                expirydate: job['EXPIRYDATE']
            });
        }
    });
});
