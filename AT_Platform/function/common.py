import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, PKCS1_v1_5
from base64 import b64encode, b64decode
import string, random


def get_env_data(env=None,vend=None):
    url = "https://{service-domain}/env-url?password={password}"
    if env :
        url += f"&env={env}"
        if vend :
            url += f"&vend={vend}"

    r = requests.get(url)
    return r.json()

def get_currency(api_url:str,platform_url:str):
    header = {
                'Content-Type': 'application/json',
                'origin': platform_url,
                'referer': platform_url
            }
    r = requests.get(url=api_url+"/platform/user/tiger-system/config?terminal=1",headers=header)
    return r.json()['data']['currencies']
    
Pk1 = 'MIICdQIBADANBgkqhkiG9w0BAQEFAASCAl8wggJbAgEAAoGBAIdBzuXIwtMAsuaBgGYrxXf3DMEKB1jvsZHmMpCZHkl1iMrv1ktWZ94AHA0Qxq/GQ0GHOf6hYJgqCSLybgANfRdBjxC6pj9DbWbWNUfopdvxUhJ2z1E1BDNdZZOh9LAVEyF92sH0GThWSxQykVP+SfUBCEVaoURrC2HYSEZk56S3AgMBAAECgYBzO1OjXKjuzxebXhUf9oajr+xDweGEmaD0pePKYUj2WJYUHsS5JoITFpDPaM19DzJZb3WvQ5lhyd5C0bt5fARnNOL65U5GHjMwZCYrgY7fnDE5d//r6Eb6QNPvpiK8RJ+R8bcD8OI2lN/BbM55bWGmwCJv1/YWYz4vkyYOZ0+lsQJBAPRWnP5/X3TG3i+Q5m8xYA0Oxn0xslXB64F5W1aATRzXirdzhTgeEFbBWhT49XpMA1xncvrXs2PwE8cjwHaNYiMCQQCNtmmqOm1rALychmV0mjHpfGjKd1YK8OA2BHtMxfrRvNjk72LrNxpuQ8Ib+1Jwdsk9qVvzULaEmJUQgKEMvepdAkActhTKnwMDgN7Y7gj15fJodmUCjxVqmFfpJe6Csp7dFcLaHbv4xSecWioQrtSBo279q7ZKHZCZ3LsmOmBCTgjLAkBhBGf0nYl5PwjhU/UzTbkr8vs+2VIzrVKiSJEtL0EWw+XtXaHoDFJw+Lx0MavvyLLfHwoPWsuJnXg30wfu1DoVAkBlDUUVnjMnHoi8smEiL6yqp+bDJJ4tHnlInNhiDPT19uBpmLa1CGSNr4joxjmccmdeprtSa0tXRBa8s7WVZxVw'
Pk2 = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCHQc7lyMLTALLmgYBmK8V39wzBCgdY77GR5jKQmR5JdYjK79ZLVmfeABwNEMavxkNBhzn+oWCYKgki8m4ADX0XQY8QuqY/Q21m1jVH6KXb8VISds9RNQQzXWWTofSwFRMhfdrB9Bk4VksUMpFT/kn1AQhFWqFEawth2EhGZOektwIDAQAB'

private_key = '-----BEGIN RSA PRIVATE KEY-----\n{}\n-----END RSA PRIVATE KEY-----'.format(Pk1)
public_key = '-----BEGIN PUBLIC KEY-----\n{}\n-----END PUBLIC KEY-----'.format(Pk2)

def login_pw_encrypt(text):
    s = str.encode(text)
    rsa_public_key = RSA.importKey(public_key)
    rsa_public_key = PKCS1_v1_5.new(rsa_public_key)
    encrypted_text = rsa_public_key.encrypt(s)
    encrypted_text = b64encode(encrypted_text)
    return encrypted_text

def login_pw_decrypt(text):
    rsa_private_key = RSA.importKey(private_key)
    rsa_private_key = PKCS1_v1_5.new(rsa_private_key)
    decrypted_text = rsa_private_key.decrypt(b64decode(text), 0)
    return decrypted_text