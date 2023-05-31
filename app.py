import os
import secrets
import requests
import pytz

from datetime import datetime, date
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateTimeField, IntegerField, \
    DateTimeLocalField, SelectField, DateField
from wtforms.validators import DataRequired, Email
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_mail import Mail, Message
from email_validator import validate_email, EmailNotValidError
from zoomus import ZoomClient

# Configure the Flask app and set a secret key for flask_session management
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'b3sit0sgiftsh0p@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'b3sit0sgiftsh0p@gmail.com'
app.config['MAIL_USE_TLS'] = True

# Zoom API Creds
API_SECRET = os.getenv('ZOOM_SECRET')
API_KEY = os.getenv('ZOOM_KEY')

# to send emails
mail = Mail(app)

# Fields
select_field_choices = ['08:00:00', '08:30:00', '09:00:00', '09:30:00', '10:00:00', '10:30:00', '11:00:00',
                        '11:30:00', '12:00:00', '12:30:00', '13:00:00', '13:30:00', '14:00:00', '14:30:00',
                        '15:00:00', '15:30:00', '16:00:00', '16:30:00', '17:00:00', '17:30:00', '18:00:00',
                        '18:30:00', '19:00:00', '19:30:00', '20:00:00', '20:30:00']


# class for form
class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Email')


class ZoomForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    # start_time = DateTimeLocalField('Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    start_time = SelectField('Start Time', validators=[DataRequired()], choices=select_field_choices)
    date = DateField('Date', validators=[DataRequired()])
    duration = 30  # 30 minutes meeting
    agenda = TextAreaField('Agenda', validators=[DataRequired()])
    timezone = 'America/New_York'
    submit = SubmitField('Send Email')


@app.route('/')
def index():  # the home page
    return render_template('home.html', title="Home")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # Get the user's input from the contact form
        name = form.name.data
        email = form.email.data
        subject = form.subject.data
        message = form.message.data

        # Validate the email using the email_validator library
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            return redirect(url_for('contact'))

        # send email
        message = Message(subject=f"{name}: {subject}", recipients=['b3sit0sgiftsh0p@gmail.com'],
                          body=f'From: {email} \n{message}', sender=email)
        mail.send(message)

        # send confirmation email
        conf_message = f"Dear {name}, \n\nThank you for choosing Besitos Gift Shop! We have received your message and will be " \
                       "in contact with you shortly! Have a great day! \n\nXOXO -Monica (980)-327-8979"
        conf_subject = 'Besitos Gift Shop Confirmation'
        confirmation = Message(sender='b3sit0sgiftsh0p@gmail.com', recipients=[email], subject=conf_subject,
                               body=conf_message)
        mail.send(confirmation)

        # Redirect the user to a success page
        return render_template('submitForm.html')

    # Render the contact form page
    return render_template('contact.html', form=form)


@app.route('/about')
def about():
    return render_template('about.html', title='About')


@app.route('/schedule-meeting', methods=['POST', 'GET'])
def schedule_meeting():
    form = ZoomForm()
    # user cannot select dates in the past (i.e. yesterday and so on)
    today = datetime.today().date()
    today_string = today.strftime("%Y-%m-%d")

    current_time = datetime.now()
    curr_timezone = current_time.astimezone().tzinfo

    # populate list of unavailable times
    # GET ACCESS TOKEN
    # Set the API endpoint
    oauth_url = 'https://zoom.us/oauth/token'

    # Set the request parameters
    data = {
        'grant_type': 'account_credentials',
        'client_id': os.getenv("ZOOM_ID"),
        'client_secret': os.getenv('ZOOM_SECRET'),
        'account_id': os.getenv('ACCOUNT_ID')
    }

    # Make the request
    oauth_response = requests.post(oauth_url, data=data)

    # Parse the response
    if oauth_response.status_code == 200:
        # access token used to make request
        access_token = oauth_response.json()['access_token']

        url = 'https://api.zoom.us/v2/users/{userId}/meetings'
        headers = {'Authorization': 'Bearer %s' % access_token, 'Content-Type': 'application/json'}

        meetings_list_response = requests.get(url.format(userId='me'), headers=headers)
        unavailable_times = []
        # build meetings list
        for meeting in meetings_list_response.json()['meetings']:
            # remove the Z and add to unavailable times list
            unavailable_times.append(meeting['start_time'].replace('Z', ''))

        if form.validate_on_submit():
            name = form.name.data
            duration = form.duration
            agenda = form.agenda.data
            timezone = form.timezone
            time = form.start_time.data
            date = form.date.data

            # combine the start time and date into one string
            start_time = str(date) + f'T{time}'

            # convert starttime to gmt for comparison
            est_time = start_time
            est_timezone = pytz.timezone('US/Eastern')
            gmt_timezone = pytz.timezone('GMT')

            est_localized = est_timezone.localize(datetime.strptime(est_time, '%Y-%m-%dT%H:%M:%S'))
            gmt_localized = est_localized.astimezone(gmt_timezone)
            gmt_time_string = gmt_localized.strftime('%Y-%m-%dT%H:%M:%S')

            # check if the user selected a booked time
            if gmt_time_string in unavailable_times:
                error = 'The selected time has already been booked. Please select another time.'
                return render_template('zoomForm.html', error_msg=error, form=form, today_string=today_string,
                                       current_time=current_time)
            else:
                # make the request
                # Set up the API request

                data = {
                    'topic': f'Consultation for {name}',
                    'start_time': start_time,
                    'duration': 30,
                    'agenda': agenda,
                    'timezone': str(curr_timezone),
                    'settings': {
                        'join_before_host': False,
                        'mute_upon_entry': True,
                        'auto_recording': 'none'
                    }
                }

                # create the meeting
                response = requests.post(url.format(userId='me'), headers=headers, json=data)

                # send email to user and besitos

                return response.json()  # reroute to page saying meeting scheduled check email or something

    return render_template('zoomForm.html', form=form, error_msg=None, today_string=today_string,
                           current_time=current_time)


if __name__ == "__main__":
    app.run(debug=False, port=5000)
