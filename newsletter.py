import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv(override=True)

publication_total = 25
code_total= 25
dataset_total= 25
container_total= 25
trial_total= 25
result_total= 25
protocol_total= 25
package_total= 25
section1 = f'''Since the last update, PM Science Portal has added {publication_total} publications that share
	{code_total} code repositories, {dataset_total} datasets, {container_total} containers, {trial_total} trials,
	{result_total} results, {protocol_total} protocols, and {package_total} packages.'''

first_name = 'Benjamin'
last_name = 'Haibe-Kains'
indiv_publication_total = 25
indiv_code_total= 25
indiv_dataset_total= 25
indiv_container_total= 25
indiv_trial_total= 25
indiv_result_total= 25
indiv_protocol_total= 25
indiv_package_total= 25

section2 = f'''Congratulations to {first_name} {last_name} for being the PM Science Portal standout of the
    quarter with {indiv_publication_total} new publications sharing {indiv_code_total} code repositories,
    {indiv_dataset_total} datasets, {indiv_container_total} containers, {indiv_trial_total} trials, {indiv_result_total}
    results, {indiv_protocol_total} protocols, and {indiv_package_total} packages!'''

message = Mail(
    from_email=os.getenv('FROM_EMAIL'),
    to_emails=['matthew.boccalon@uhn.ca', 'benjamin.haibe-kains@uhn.ca'],
    subject='Sendgrid Email',
    html_content='<strong>News Letter</strong>')

message.dynamic_template_data = {
	'section1': section1,
    
	'section2': section2,
    
	# 'general_extra_text': 'We hope you are enjoying the Science Portal thus far!',
    
	'update1_date': 'August, 2025',
    'update1_heading': 'End of Summer Update',
    'update1_text': 'We are releasing our new feature for adding new publications to ',
    
	'update2_date': 'Fall, 2025',
    'update2_heading': 'Fall Update',
    'update2_text': 'We are planning on adding our new database update'
}

message.template_id = 'd-4a92dc1d5b664df0968761762003df3d'

try:
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e)