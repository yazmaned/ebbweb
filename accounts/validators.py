from django.core.exceptions import ValidationError


class MinimumLengthValidator:
    def __init__(self, min_length=4):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                f"Parolanız en az {self.min_length} karakter olmalıdır.",
                code='password_too_short',
            )

    def get_help_text(self):
        return f"En az {self.min_length} karakter"