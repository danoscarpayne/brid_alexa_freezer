import logging
import os
import boto3
from botocore.exceptions import ClientError


def create_presigned_url(object_name):
    """Generate a presigned URL to share an S3 object with a capped expiration of 60 seconds

    :param object_name: string
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3',
                             region_name=os.environ.get('S3_PERSISTENCE_REGION'),
                             config=boto3.session.Config(signature_version='s3v4',s3={'addressing_style': 'path'}))
    try:
        bucket_name = os.environ.get('S3_PERSISTENCE_BUCKET')
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=60*1)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response
    
def speech_output_generator_drawer(df):
    
    # initialise speech output
    speech_output = "you have \n"
    
    final_idx = df.index.max()
    
    frame_length = len(df)
    
    # Loop through the df
    for i, row in df.iterrows():
        
        # conditions
        if row.units == 1:
            
            unit_speech = ''
        
        else:
            
            unit_speech = row.units
            
        # item qty conditions
        if row.item_qty == '1':
            
            item_speech = ''
            
        else:
            
            item_speech = row.item_qty
            
        # Now deal with food
        if row.food_name.endswith('s') or row.food_name.endswith('i') or (row.item_qty != '1'):
            
            if (i == final_idx) and (frame_length > 1):
                
                speech_output += 'and '
            
            # check units
            if unit_speech == '':
                
                speech_output += 'a packet of {} {}, \n'.format(item_speech, row.food_name)
                
            else:
                
                speech_output += '{} packets of {} {}, \n'.format(unit_speech, item_speech, row.food_name)
                
        else:
            
            if 'cream' in row.food_name:
                
                speech_output += '{} tubs of {},\n'.format(unit_speech, row.food_name)
                
            else:
            
                speech_output += '{} {},\n'.format(unit_speech, row.food_name)
            
    speech_output = speech_output[:-1]
            
    return speech_output