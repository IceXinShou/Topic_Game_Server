import os
import xml.etree.ElementTree as ETree
from base64 import b64encode

from Crypto import Random
from Crypto.PublicKey import RSA

rsa: RSA
pwd = 'xs'

if not (os.path.exists('../../../private_key.pem') and
        os.path.exists('../../../public_key.pem')):
    # 檔案不完整，重新生成 RSA 金耀

    # 寫入私鑰
    with open('../../../private_key.pem', 'wb') as f:
        rsa = RSA.generate(4096, Random.new().read)
        rsa.public_key()
        f.write(rsa.exportKey('PEM', pwd))
        f.close()

    # 寫入公鑰
    with open('../../../public_key.pem', "wb") as f:
        f.write(rsa.public_key().exportKey('PEM'))
        f.close()

else:
    # 檔案完整，讀取私鑰
    with open('../../../private_key.pem', "rb") as f:
        rsa = RSA.importKey(f.read(), pwd)


def getPublicKey() -> bytes:
    f"""
    以 XML 格式生成 RSA 公鑰
    
    Returns:
        bytes: RSA 公鑰 (bytes)
    """

    # Create the XML structure for the RSA public key
    rsa_key_xml = ETree.Element('RSAKeyValue')

    # Add modulus
    modulus_xml = ETree.SubElement(rsa_key_xml, 'Modulus')
    modulus_xml.text = b64encode(
        rsa.n.to_bytes(512, byteorder='big')).decode('utf-8')

    # Add exponent
    exponent_xml = ETree.SubElement(rsa_key_xml, 'Exponent')
    exponent_xml.text = b64encode(
        rsa.e.to_bytes(3, byteorder='big')).decode('utf-8')

    # Convert XML to bytes and return
    return ETree.tostring(rsa_key_xml, encoding='utf-8')
