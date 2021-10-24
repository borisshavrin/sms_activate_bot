from cryptography.fernet import Fernet

from sms_activate_bot.settings import BASE_DIR


def write_key():
    """Создание ключа и сохранение в файл"""
    key = Fernet.generate_key()
    with open(f'{BASE_DIR}/crypto/crypto.key', 'wb') as key_file:
        key_file.write(key)


def load_key():
    return open(f'{BASE_DIR}/crypto/crypto.key', 'rb').read()


def encrypt(text):
    key = load_key()
    cipher = Fernet(key)
    encrypted_text = cipher.encrypt(text)
    return encrypted_text


def decrypt(encrypted_text):
    key = load_key()
    cipher = Fernet(key)
    decrypted_text = cipher.decrypt(encrypted_text)
    return decrypted_text
