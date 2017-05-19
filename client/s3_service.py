import boto
from boto.s3.key import key
from service_config import s3Config

def s3_download_file(bucketName, srcFileName, destFileName):
    conn = boto.connect_s3(s3Config.keyId, s3Config.sKeyId)
    bucket = conn.get_bucket(bucketName)

    #Get the Key object of the given key, in the bucket
    k = Key(bucket,srcFileName)

    #Get the contents of the key into a file 
    k.get_contents_to_filename(destFileName)

    return destFileName
