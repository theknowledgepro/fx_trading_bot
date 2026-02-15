from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path
from getpass import getpass

def load_key():
    key_path = Path("secret.key")
    if not key_path.exists():
        key = Fernet.generate_key()
        key_path.write_bytes(key)
        print("[+] Secret key generated: secret.key")
    else:
        key = key_path.read_bytes()
        print("[i] Secret key already exists: secret.key (will reuse)")
    return key

def decrypt_secret(enc_key: bytes | str | None) -> str:
    try:
        if not enc_key:
            return ""

        # ensure bytes
        if isinstance(enc_key, str):
            enc_key = enc_key.encode()

        key = load_key()
        fernet = Fernet(key)

        return fernet.decrypt(enc_key).decode()

    except (InvalidToken, ValueError, TypeError):
        # wrong key, corrupted token, bad input
        return ""
    except Exception:
        # absolutely never let this crash the bot
        return ""


def generate_env_file():
    """
    One-click setup for MT5 credentials:
    - Generates secret.key if missing
    - Encrypts login/password/alert email & password
    - Writes encrypted values and server to .env
    """
    print("=== MT5 Credentials Encryption & .env Setup ===\n")

    

    # ---- Step 1: Generate secret.key if not exists ----
    key = load_key()
    fernet = Fernet(key)

    # ---- Step 2: Ask user for credentials ----
    login = input("Enter MT5 login: ")
    password = getpass("Enter MT5 password: ")
    server = input("Enter MT5 server: ")
    alert_email = input("Enter alert email address: ")
    alert_email_password = getpass("Enter alert email address password: ")
    alert_to = input("Enter email alerts recipient email address: ")

    # ---- Step 3: Encrypt login & password ----
    enc_login = fernet.encrypt(login.encode()).decode()
    enc_password = fernet.encrypt(password.encode()).decode()
    enc_alert_email = fernet.encrypt(alert_email.encode()).decode()
    enc_alert_email_password = fernet.encrypt(alert_email_password.encode()).decode()

    # ---- Step 4: Write to .env ----
    env_path = Path(".env")
    env_content = (
        f"MT5_LOGIN_ENC={enc_login}\n"
        f"MT5_PASSWORD_ENC={enc_password}\n"
        f"MT5_SERVER={server}\n"
        f"ALERT_EMAIL_ENC={enc_alert_email}\n"
        f"ALERT_EMAIL_PASSWORD_ENC={enc_alert_email_password}\n"
        f"ALERT_EMAIL_TO={alert_to}\n"
    )
    env_path.write_text(env_content)
    print("[+] .env file created with encrypted credentials!\n")
    print("[✓] Setup complete. You can now run your bot securely.")

if __name__ == "__main__":
    generate_env_file()
