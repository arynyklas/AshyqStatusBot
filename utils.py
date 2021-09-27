from re import match
from string import ascii_uppercase, ascii_lowercase, digits
from random import choice


chars = ascii_uppercase + ascii_lowercase + digits


def is_phone_number(phone_number: str) -> bool:
    return len(phone_number) == 12 and bool(match(
        r'\+7(700|701|702|703|704|705|706|707|708|709|747|750|751|760|761|762|763|764|771|775|776|777|778)\d{7}', phone_number
    ))

def is_sms_code(code: str) -> bool:
    return len(code) == 4 and code.isdigit()


def random_string(length: int) -> str:
    return ''.join(choice(chars) for _ in range(length))
