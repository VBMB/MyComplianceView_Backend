from werkzeug.security import generate_password_hash

pwd = "mypassword123"
hashed = generate_password_hash(pwd, method='pbkdf2:sha256', salt_length=16)
print(hashed)