from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Custom S3 Storage for user-uploaded media files (videos, PDFs, images).
    All files will be stored inside the 'media/' folder in the S3 bucket.
    """
    location = 'media'
    file_overwrite = False
