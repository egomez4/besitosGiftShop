import os
import secrets
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for
from flask_mail import Mail, Message
from email_validator import validate_email, EmailNotValidError

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

# to send emails
mail = Mail(app)

# Fields
# select_field_choices = ['08:00:00', '08:30:00', '09:00:00', '09:30:00', '10:00:00', '10:30:00', '11:00:00',
#                        '11:30:00', '12:00:00', '12:30:00', '13:00:00', '13:30:00', '14:00:00', '14:30:00',
#                        '15:00:00', '15:30:00', '16:00:00', '16:30:00', '17:00:00', '17:30:00', '18:00:00',
#                        '18:30:00', '19:00:00', '19:30:00', '20:00:00', '20:30:00']


# class for form
class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')


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
        conf_message = f"Dear {name}, \n\nThank you for choosing Besitos Gift Shop! We have received your message" \
                       " and will be in contact with you shortly! Have a great day! \n\nBesitos Gift Shop (" \
                       "980)-443-0214 "
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


if __name__ == "__main__":
    app.run(debug=False, port=5000)
