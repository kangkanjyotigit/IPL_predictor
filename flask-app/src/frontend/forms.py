"""Forms for the frontend blueprint"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, HiddenField, FloatField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
from src.models.user import User
from src.utils.constants import TeamStrategies, CaptainPreferences, MAX_PLAYERS_FROM_TEAM

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Validate that username is unique"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Validate that email is unique"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

class ProfileForm(FlaskForm):
    """Form for user profile update"""
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    bio = StringField('Bio', validators=[Length(max=500)])
    submit = SubmitField('Update Profile')

class MatchFilterForm(FlaskForm):
    """Form for filtering matches"""
    status = SelectField('Status', choices=[
        ('all', 'All Matches'),
        ('upcoming', 'Upcoming Matches'),
        ('live', 'Live Matches'),
        ('completed', 'Completed Matches')
    ], default='all')
    team = StringField('Team Name')
    venue = StringField('Venue')
    submit = SubmitField('Filter')

class TeamBuilderForm(FlaskForm):
    """Form for building a team"""
    team_name = StringField('Team Name', validators=[DataRequired(), Length(min=3, max=100)])
    match_id = HiddenField('Match ID', validators=[DataRequired()])
    captain_id = HiddenField('Captain ID')
    vice_captain_id = HiddenField('Vice Captain ID')
    player_ids = HiddenField('Player IDs')
    submit = SubmitField('Save Team')

class AutoGenerateTeamForm(FlaskForm):
    """Form for auto-generating teams"""
    team_name = StringField('Team Name', validators=[
            Length(min=3, max=100, message="Team name must be between 3 and 100 characters"),
            Optional()  # Make it optional, we'll generate a default if not provided
        ])
    strategy = SelectField('Team Strategy', choices=TeamStrategies.STRATEGY_CHOICES, default=TeamStrategies.BALANCED, validators=[
            DataRequired(message="Please select a team strategy")
        ])
    max_players_from_team = IntegerField('Max Players From One Team', validators=[
            DataRequired(message="Please specify the maximum number of players from one team"),
            NumberRange(min=1, max=MAX_PLAYERS_FROM_TEAM, message=f"Value must be between 1 and {MAX_PLAYERS_FROM_TEAM} players")
        ], default=7)
    form_weight = FloatField('Form Weight', validators=[
            DataRequired(message="Please specify the weight for player form"),
            NumberRange(min=0, max=1, message="Value must be between 0 and 1")
        ], default=0.6)
    credit_weight = FloatField('Credit Weight', validators=[
            DataRequired(message="Please specify the weight for player credits"),
            NumberRange(min=0, max=1, message="Value must be between 0 and 1")
        ], default=0.4)
    captain_preference = SelectField('Captain Preference', choices=CaptainPreferences.CAPTAIN_CHOICES, default=CaptainPreferences.HIGHEST_POINTS, validators=[
            DataRequired(message="Please select a captain preference")
        ])
    vice_captain_preference = SelectField('Vice-Captain Preference', choices=CaptainPreferences.VICE_CAPTAIN_CHOICES, default=CaptainPreferences.SECOND_HIGHEST_POINTS, validators=[
            DataRequired(message="Please select a vice-captain preference")
        ])
    consider_opposition = BooleanField('Consider Opposition', default=True)
    apply_budget_optimization = BooleanField('Apply Budget Optimization', default=True)
    submit = SubmitField('Generate Team')
    
    def validate_form_weight(self, field):
        """Ensure form_weight and credit_weight sum to 1.0"""
        if hasattr(self, 'credit_weight') and self.credit_weight.data is not None:
            total = field.data + self.credit_weight.data
            if abs(total - 1.0) > 0.01:
                # Auto-adjust to make them sum to 1.0 instead of raising an error
                if total > 0:
                    field.data = field.data / total
                    self.credit_weight.data = self.credit_weight.data / total
                else:
                    field.data = 0.5
                    self.credit_weight.data = 0.5
    
    def validate_credit_weight(self, field):
        """Ensure form_weight and credit_weight sum to 1.0"""
        if hasattr(self, 'form_weight') and self.form_weight.data is not None:
            total = field.data + self.form_weight.data
            if abs(total - 1.0) > 0.01:
                # Already handled in validate_form_weight, just skip
                pass
    
    def validate(self, extra_validators=None):
        """Custom validation to ensure all fields are properly processed
        
        Args:
            extra_validators: Optional additional validators passed by Flask-WTF
        """
        if not super().validate(extra_validators=extra_validators):
            return False
            
        # Handle type conversion issues
        try:
            if self.max_players_from_team.data is not None:
                self.max_players_from_team.data = int(self.max_players_from_team.data)
                
            if self.form_weight.data is not None:
                self.form_weight.data = float(self.form_weight.data)
                
            if self.credit_weight.data is not None:
                self.credit_weight.data = float(self.credit_weight.data)
                
            # Ensure boolean fields are properly converted
            self.consider_opposition.data = bool(self.consider_opposition.data)
            self.apply_budget_optimization.data = bool(self.apply_budget_optimization.data)
            
        except (ValueError, TypeError) as e:
            self.submit.errors.append(f"Invalid data type in form: {str(e)}")
            return False
            
        return True

class VenueForm(FlaskForm):
    """Form for venue management"""
    name = StringField('Venue Name', validators=[DataRequired(), Length(min=3, max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(min=3, max=100)])
    capacity = IntegerField('Capacity', validators=[Optional(), NumberRange(min=1000)])
    submit = SubmitField('Save Venue')
