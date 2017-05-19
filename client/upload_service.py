import boto
from boto.s3.key import Key
from service_config import s3Config, flaskConfig

def s3_download_file(bucketName, srcFileName, destFileName):
    conn = boto.connect_s3(
            s3Config["keyId"], s3Config["sKeyId"],
            # 's3-eu-west-1.amazonaws.com',
            # calling_format = boto.s3.connection.OrdinaryCallingFormat()
    )
    bucket = conn.get_bucket(bucketName)

    #Get the Key object of the given key, in the bucket
    k = Key(bucket, srcFileName.split('/').pop())

    #Get the contents of the key into a file 
    k.get_contents_to_filename(destFileName)

    return destFileName


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in flaskConfig["allowedExtensions"]