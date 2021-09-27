from re import match


def is_phone_number(phone_number: str, phone_codes: list):
    return bool(match(
        '+7[{}'.format(
            '|'.join(phone_codes)
        ), phone_number
    ))


def is_sms_code(code: str):
    return len(code) == 5 and code.isdigit()
