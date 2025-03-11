from wtforms import Form, StringField, PasswordField, TextAreaField, validators


class RegistrationForm(Form):
    username = StringField(
        "Username", [validators.Length(min=4, max=25), validators.DataRequired()]
    )
    email = StringField(
        "Email",
        [
            validators.Length(min=6, max=50),
            validators.Email(),
            validators.DataRequired(),
        ],
    )
    password1 = PasswordField(
        "Password",
        [
            validators.DataRequired(),
            validators.Length(min=6),
            validators.EqualTo("password2", message="Passwords must match"),
        ],
    )
    password2 = PasswordField("Confirm Password")


class LoginForm(Form):
    username = StringField("Username", [validators.DataRequired()])
    password = PasswordField("Password", [validators.DataRequired()])


class ProfileUpdateForm(Form):
    username = StringField(
        "Username", [validators.Length(min=4, max=25), validators.DataRequired()]
    )
    email = StringField(
        "Email",
        [
            validators.Length(min=6, max=50),
            validators.Email(),
            validators.DataRequired(),
        ],
    )
    bio = TextAreaField("Bio", [validators.Optional()])


class PostForm(Form):
    title = StringField("Title", [validators.Optional(), validators.Length(max=100)])
    content = TextAreaField("Content", [validators.DataRequired()])
