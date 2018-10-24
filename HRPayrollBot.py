# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 19:16:37 2018

@author: Denesh_Mani
"""

import os
import sys
import datetime
import django
import pandas as pd
import logging
import logging.config
import xml.etree.ElementTree as ET
import html2text


basedir = os.path.dirname(os.path.abspath(__file__))
os.chdir(basedir)
sys.path.append("../")

BASENAME = os.path.basename(__file__)
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(BASENAME)
filename = 'configuration.yaml'

# loading django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrpayroll.settings")
django.setup()

from customnlp import email_classifcation_predict
from emailutils import talon_email_parser
from emailutils import office365
from database.models import Email
from database.models import Nia_Incident
from database.models import Converter
from database.operations import EmailOps
from database.operations import NiaIncidentOps
from database.operations import MoveEmailOps
from database.operations import HRPayrollResponseOps
from database.operations import TsomIncidentOpertions
from database.operations import AssigmentFolderOps
from itsmutils import tsom
from hrpayroll.templateutils import Templates


# instantiating operations implementations
incident_ops = NiaIncidentOps()
email_ops = EmailOps()
moveemail_ops = MoveEmailOps()
tsom_ops = TsomIncidentOpertions()
AssigmentFolder_instance = AssigmentFolderOps()
o365_instance = office365.O365Client(filename)

'''
@name: load
@description: loads bot configurations from YAML file
@parameters: filename - qualified path of .yaml file
@returns: bot configuration parameters as a dictionary
'''
def load_conf(filename):
    if not os.path.isfile(filename):
        raise FileNotFoundError('.yaml file not found at the given location ' + filename)            
    from yaml import load
    import io
    configuration_key = 'hrpayrollbot_conf'
    data = None
    with io.FileIO(filename, 'r') as fYaml:
        data = load(fYaml)
    if not configuration_key in data:
        raise ValueError("Expected key {} is missing the given properties file {}".format(configuration_key, filename))
    return data[configuration_key]

# load configuration
configuration = load_conf(filename)

'''
@name: main
@description: orchestrates the monitor_mailbox flow
'''
def main(incident_id):
    try:        
        logger.info('need more details, fetching incident details')
        _incs = incident_ops.get_incident_by_id(incident_id)
        if len(_incs) == 0:
            raise Exception('Oops! This incident is not found in HRPayroll automation DB')
        incident = _incs.first() #' considering the first incident and incident id is unique
        logger.info('all good but need more details, fetching email details')
        if incident.Email == None:
            raise ValueError('Oops! Something wrong, Email object not in the current incident')
        logger.info('checking if email is a new message through conversation reference id')
        # finding the latest email after folder movement
        new_message_id = moveemail_ops.get_lasted_message_id(incident.Email)
        __email_data = email_ops.get_message_with_body(new_message_id)
        # type casting for further operations
        current_email = email_ops.cast_as_email_object(__email_data)
        # To View user request mail on console
        request_mail_log(incident, current_email)
        if email_ops.is_new_message(incident.Email.MessageId, incident.Email.ConversationId):
            logger.info('all good, conversation id is not found. Seems to be a new message')
            logger.info('Okay, lets start processing the email..')
            as_new_request(incident, current_email) #' calling function
        else:
            logger.info('Mmm, conversation id is found. Lets check if I have already processed this conversation')
            parent_email = email_ops.find_parent_message(incident.Email.MessageId, incident.Email.ConversationId)
            if parent_email != None: # parent email found
                process_response_email(incident, parent_email, current_email)
            else:
                #raise NotImplementedError('when parent email is not found')
                #logger.info("I guess it is not 1st or 2nd thread, So i am unable to find parent email with condition AttachmentRequired in find_parent_message method")
                logger.info("It is not first thread, So i am unable to find parent email with condition AttachmentRequired in find_parent_message method")
                #tsom_object = tsom_ops.get_tsom_new_incident(incident.Email)
                #tsom_object=0
                #if len(tsom_object) > 0:
                #logger.info('Okay, Hope this is final request thread from user. So, updating ticket as HR manual intervention required')
                # update tsom ticket                
                #update_tsom_ticket(parent_email, current_email, configuration['tsom_short_desc_hr_picked'], configuration['tsom_hr_support_group'])
                #else:
                parent_email = email_ops.parent_message_validation(incident.Email.MessageId, incident.Email.ConversationId)
                if parent_email != None: # parent email found (check without any conditions to get parent id to avoid new ticket creation for already processed thread)
                    if parent_email.Status == 'ResponseRequired':
                        process_response_email(incident, parent_email, current_email)
                        logger.info("Hey, I found parent email id without anyconditions!! So, updating ticket as HR manual intervention required - Resposne")
                    else:
                        logger.info("Hey, I found parent email id without any conditions!! So, updating ticket as HR manual intervention required - Request")
                        #update_tsom_ticket(parent_email, current_email, configuration['tsom_short_desc_hr_picked'], configuration['tsom_hr_support_group'])
                        add_assignee_folder_in_db(incident, current_email)
                        round_robin_movement(incident, current_email)
                    logger.info("Okay, Hope this is final request thread from user")
                else:
                    logger.info('Okay, Hope this is final request thread from user. So, creating ticket as HR manual intervention required')
                    #logger.debug('Caution : it may create new ticket if for old thread because parent id not found')                    
                    intent = "UNKOWN-"  # No intend ??
                    manual_intervention(incident, current_email, intent)                                     
        
        logger.info('Process completed. Hope, I served my purpose')
        print("botstatus=success")        
    except Exception as eor:
        logger.error(eor)
        raise eor

'''
@name: as_new_request
@description: taking steps to process a new service request
'''
def as_new_request(incident, current_email):
    try:               
        sender = current_email.Sender['EmailAddress']['Address']
        logger.info('so far so good, lets classify the email')
        intent = predict_intent(sender, current_email.Subject, current_email.Body)
        if intent != 'UNKNOWN':
            logger.info('identified intent is {}. Taking appropriate action'.format(intent))
            #' get matching response
            response = HRPayrollResponseOps.find_response(intent)
            if len(response) > 0:
                execute_intent(incident, current_email, response[0], intent)
            else:
                logger.error('No mapped response found for the intent {}'.format(intent))
                #raise NotImplementedError('Missing implementation when mapped response is not found')
                # create a tsom ticket
                manual_intervention(incident, current_email, intent)                              
        else:
            logger.warn('Sorry, I am not design to handle this request (Intent UNKNOWN). ')
            manual_intervention(incident, current_email, intent)
    except Exception as eor:
        logger.error(eor)
        raise eor

'''
@name: process_response_email
@description: identified response email will be processed accordingly
'''
def process_response_email(incident, parent_email, current_email):
    try:
        logger.info('Response received from the user for the incident ' + incident.Id)
        # update tsom ticket                
        #update_tsom_ticket(parent_email, current_email, configuration['tsom_short_desc_bot_picked'], configuration['tsom_hr_support_group'])        
        # update parent email status
        email_ops.update_status(parent_email, Email.ProcessStatus.WaitingForManualAction)
        add_assignee_folder_in_db(incident, current_email)        
        # getting SNOW Ticket ID
        #snow_ticket_id = get_snow_ticket_id(parent_email)        
        snow_ticket_id = 'INC0000XXX'
        logger.info('SNOW Ticket {} is updated with the response'.format(snow_ticket_id))
        response = {'ResponseContent' : configuration['user_response_received'], 'snow': snow_ticket_id }                
        send_incident_response(incident, current_email, configuration['tsom_hr_support_group'], response, attach_files= False) 
        logger.info('Response sent to the user')
        # closing the current email when appended with parent email
        email_ops.update_status(incident.Email, Email.ProcessStatus.ReponseAppended)
        logger.info('This email is successfully appended to the parent email')
    except Exception as eor:
        logger.error(eor)
        raise eor

def manual_intervention(incident, current_email, intent):
    try:
        logger.info('Creating SNOW ticket for manual intervention')
        #create_tsom_ticket(incident.Email, current_email, configuration['tsom_short_desc_hr_picked'], intent, configuration['tsom_hr_support_group'])
        # getting SNOW Ticket ID
        #snow_ticket_id = get_snow_ticket_id(incident.Email)
        add_assignee_folder_in_db(incident, current_email)        
        snow_ticket_id = 'INC0000XXX'
        logger.info('Created SNOW ticket ' + snow_ticket_id)
        email_ops.update_status(incident.Email, Email.ProcessStatus.WaitingForManualAction)
        response = {'ResponseContent' : configuration['unknown_intent'], 'snow': snow_ticket_id }
        send_incident_response(incident, current_email, configuration['tsom_hr_support_group'], response, attach_files= False) #when inputs found        
        logger.info('Send user notification')
    except Exception as eor:
        logger.error(eor)
        raise eor

'''
@name: execute_intent
@description: takes appropriate action for the current matched intent
'''
def execute_intent(incident, email, response, intent):
    if email == None or response == None:
        raise ValueError('email and response cannot be None')   
    logger.info('lets start executing configured intent action') 
    if response['ExpectsReponse']: # when attachment expected from User
        logger.info('seems this intent expects inputs from the user')
        if email.HasAttachments: # when attachment is already found
            logger.info('Cool, good user has already provided inputs')
            email_ops.update_status(incident.Email, Email.ProcessStatus.UserInputFound)            
            #create_tsom_ticket(incident.Email, email, configuration['tsom_short_desc_bot_picked'], intent, configuration['tsom_bot_support_group'])
            # getting SNOW Ticket ID
            #snow_ticket_id = get_snow_ticket_id(incident.Email)
            snow_ticket_id = 'INC0000XXX'
            logger.info('Created SNOW ticket ' + snow_ticket_id)
            email_ops.update_status(incident.Email, Email.ProcessStatus.WaitingForManualAction)
            response['ResponseContent'] = configuration['snow_created']
            response['snow'] = snow_ticket_id
            logger.info('Sending user response')
            send_incident_response(incident, email, configuration['tsom_bot_support_group'], response, attach_files= False) #when inputs found
        else:            
            #create_tsom_ticket(incident.Email, email, configuration['tsom_short_desc_bot_picked'], intent, configuration['tsom_hr_support_group'])
            # getting SNOW Ticket ID
            #snow_ticket_id = get_snow_ticket_id(incident.Email)            
            snow_ticket_id = 'INC0000XXX'
            logger.info('Created SNOW ticket ' + snow_ticket_id)
            email_ops.update_status(incident.Email, Email.ProcessStatus.AttachmentRequired)            
            #response['snow'] = snow_ticket_id
            response['snow'] = 'firstthread' # To avoid ticket details for 1st thread resposne to end user print("input" + response.get('snow'))
            logger.info('Let me ask the user to send required inputs')
            logger.info('Sending response email with attachments')
            send_incident_response(incident, email, configuration['tsom_hr_support_group'], response, attach_files= True) #when inputs found                        
    else:
        logger.info('Seems, this intent has default response')
        #create_tsom_ticket(incident.Email, email, configuration['tsom_short_desc_bot_picked'], intent, configuration['tsom_bot_support_group'])        
        # getting SNOW Ticket ID
        #snow_ticket_id = get_snow_ticket_id(incident.Email)
        snow_ticket_id = 'INC0000XXX'
        logger.info('Created SNOW ticket ' + snow_ticket_id)
        email_ops.update_status(incident.Email, Email.ProcessStatus.SNOWTicketCreated)
        if 'incident' in intent:
            response['ResponseContent'] = response['ResponseContent'].replace('$INCIDENT_NO', snow_ticket_id)
        else:
            response['snow'] = 'firstthread' # To avoid ticket details for 1st thread resposne to end user print("input" + response.get('snow'))
        logger.info('Sending user response')        
        send_incident_response(incident, email, configuration['tsom_bot_support_group'], response, is_default = True, attach_files= False) #default response
        logger.info('Default response sent to the user')
        if 'response' in intent:
            email_ops.update_status(incident.Email, Email.ProcessStatus.ResponseRequired)
        else:
            email_ops.update_status(incident.Email, Email.ProcessStatus.ResolvedByRobot)

def get_snow_ticket_id(email):
    tsom_object = tsom_ops.get_tsom_new_incident(email)
    if len(tsom_object) > 0:
        return tsom_object.first().SnowIncidentID
    raise ValueError('Missing TSOM data')

'''
@name: send_incident_response
@description: sends email response when incident is created
@parameter: email - full email object
            response  - mapped intent response object
            attach_files - when True avaliable attachments will be added in the response
'''
def send_incident_response(incident, email, support_group, response,is_default = False, attach_files = False):
    values = get_template_values(email, response)            
    message = None
    if email.Body['ContentType'] == 'HTML':
        message = Templates.gen_request_response_html(values)
    else:
        message = Templates.gen_request_response_text(values)
    logger.debug("Hey, before sending the response to user i will get parent id to update ticket")   
    parent_email = email_ops.parent_message_validation(incident.Email.MessageId, incident.Email.ConversationId)
    if parent_email != None: # parent email found
        logger.info("Wow, Parent email Found !! Everything going smooth. so, intiating update ticket")
        #update_tsom_ticket_before_send_resposne(parent_email, email, configuration['tsom_short_desc_bot_picked'], support_group, message)
    else:
        logger.error('Oops, Parent Email_id Not found to update a ticket.. please Contact the team')       
    attachments = []
    if attach_files:
        attachments = response['Attachments'].split(',') if response['Attachments'] != None else []
    o365_instance.reply_to(email.MessageId, message, is_default = is_default, attachments = attachments)
    round_robin_movement(incident, email)

'''
@name: get_template_values
@description: extracts template values from email and response objects
'''
def get_template_values(email, response):
    output = {}
    if email != None:
        output['sender'] = subnodes(email.Sender,'EmailAddress.Name')
        output['subject'] = email.Subject
        _,text,signature = talon_email_parser.extract_text_signature(
            email_message = subnodes(email.Body,'Content'),
            sender = subnodes(email.Sender,'EmailAddress.Address'),
            content_type=subnodes(email.Body,'ContentType'),
        )
        output['message'] = text
        output['attachments'] = 'No attachments found' if email.HasAttachments == False else 'Attachment(s) found, please check the email in outlook'
    
    if response != None and isinstance(response, dict) and len(response) > 0 :
        output['response'] = response.get('ResponseContent')
        if response.get('snow') != None:
            if response.get('snow') != "firstthread":
                #output['snow'] = 'ServiceNow ticket has been raised to serve your request and reference Id is {} ServiceNow Link : https://sparknz.service-now.com/navpage.do'.format(response.get('snow'))
                output['snow'] = ''
            else:
                output['snow'] = ''
        else:
            output['snow'] = ''
    return output

'''
@name: subnodes
@description: reads value from hierarchical dict
'''
def subnodes(data, name):
    names = name.split('.')
    for n in names:
        data = data.get(n)
        if data == None:
            return None
    return data

'''
@name: create_tsom_ticket
@parameter: incident_email - first or parent email for which the incident is created
            current_email - could be first or response email
'''
def create_tsom_ticket(incident_email, current_email, short_description, intent, support_group):    
    values = get_template_values(current_email, None)
    #print(values.get('message'))
    short_description = intent + " : " + values.get('subject').replace('&', 'and').replace('"', '\"').replace('“', '\"').replace("’","'").replace('”','\"').replace("‘","'").replace('<[', ' ').replace('](', ' ').replace(')>', ' ')
    description = Templates.gen_ticket_description(values)
    email_last_message_without_response = description.split("Request Message:",1)[1]
    email_last_message_without_response = email_last_message_without_response.replace('&', 'and').replace('"', '\"').replace('“', '\"').replace("’","'").replace('”','\"').replace("‘","'").replace('<[', ' ').replace('](', ' ').replace(')>', ' ').replace('Mayank Bansal | Test Lead | Spark Connect','')
    #info = (email_last_message_without_response[:150] + '..') if len(email_last_message_without_response) > 150 else email_last_message_without_response
    tsom_instance = tsom.TSOMclient()
    tsom_instance.createticketTSOM(email_last_message_without_response, incident_email, short_description, support_group)
    email_ops.update_status(incident_email, Email.ProcessStatus.SNOWTicketCreated)

'''
@name: update_tsom_ticket
@parameter: incident_email - first or parent email for which the incident is created
            current_email - could be first or response email
'''
def update_tsom_ticket(incident_email, current_email, short_description, support_group):    
    values = get_template_values(current_email, None)
    description = Templates.gen_ticket_description(values)
    email_last_message = description.split("**Sent:**",1)[0]    # To get last thread from mail conversation
    email_last_message = email_last_message.replace('&', 'and').replace('"', '\"').replace('“', '\"').replace("’","'").replace('”','\"').replace("‘","'").replace('<[', ' ').replace('](', ' ').replace(')>', ' ')    
    tsom_instance = tsom.TSOMclient()
    tsom_instance.updateticketTSOM('OPEN', email_last_message, incident_email, short_description, support_group)
    email_ops.update_status(incident_email, Email.ProcessStatus.UpdatedSNOWTicket)

'''
@name: update_tsom_ticket_before_send_resposne
@parameter: incident_email - first or parent email for which the incident is created
            current_email - could be first or response email
'''
def update_tsom_ticket_before_send_resposne(incident_email, current_email, short_description, support_group, send_respose):    
    description = html2text.html2text(send_respose)
    #values = get_template_values(current_email, None)
    #description = Templates.gen_ticket_description(values)
    email_last_message = description.split("**Sent:**",1)[0]    # To get last thread from mail conversation
    email_last_message = email_last_message.replace('&', 'and').replace('“', '\"').replace("’","'").replace('”','\"').replace("‘","'").replace('<[', ' ').replace('](', ' ').replace(')>', ' ')  
    tsom_instance = tsom.TSOMclient()
    tsom_instance.updateticketTSOM('OPEN', email_last_message, incident_email, short_description, support_group)
    #email_ops.update_status(incident_email, Email.ProcessStatus.UpdatedSNOWTicket)

'''
@name: send_user_response
@description: sends the appropriate response through email
@parameter: email - full email content
            response - mapped response for the identified intent
            inputs_found - True when expected inputs found
'''
def send_user_response(email, response, inputs_found):
    values = get_template_values(None, response)
    
    user_response = None
    if email.Body['ContentType'] == 'HTML':
        user_response = Templates.gen_request_response_html(values)
    else:
        user_response = Templates.gen_request_response_text(values)
    if user_response == None or len(user_response) == 0: # when invalid user_response generated
        raise ValueError('Invalid user_response generated. Check Templates.gen_requrest_response_text')
    attachments = []
    if response['HasAttachments']:
        attachments = response.get('Attachments').split(',') if response.get('Attachments') != None else []
    o365_instance.reply_to(email.MessageId, user_response, attachments=attachments)

'''
@name: predict_intent
@description: classifies the given email under HR Payroll service category
'''
def predict_intent(sender, subject, raw_message):
    subject = str(subject).lower()    
    content_type = raw_message['ContentType']
    message = raw_message['Content']
    reply, text, signature = talon_email_parser.extract_text_signature(
                    email_message = message,
                    sender = sender,
                    content_type= 'text/html' if content_type == 'HTML' else 'text/plain'
                )
    df_input = pd.DataFrame({'Subject': [subject], 'Message': [text]}) #' passing the parsed text 
    predicted = email_classifcation_predict.predict(df_input) # (intent,prediction_probability)
    if len(predicted) == 0:
        raise ValueError('could not predict the service category')
    threshold = float(configuration['min_prediction_threshold'])
    return predicted[0] if predicted[1] >= threshold else 'UNKNOWN'

def round_robin_movement(incident, current_email):
    #destFoldersList, destFolderDict = o365_instance.folders_list_with_msg_count(configuration.get('user_assign_parent_folder_id'))
    AssigmentFolder_obj = AssigmentFolder_instance.find_conversationid_in_db(incident.Email.ConversationId)
    if len(AssigmentFolder_obj) != 0:
        ConversationId = AssigmentFolder_obj.first().ConversationId
        AssigmentFolderId = AssigmentFolder_obj.first().FolderId
        AssigmentFolderName = AssigmentFolder_obj.first().FolderName
        if(ConversationId == incident.Email.ConversationId):
            logger.info('ConversationId matches with existing record! So Moving the message to HR folder : {} '.format(configuration['user_assign_parent_folder_name']))
            #' move folder to dyanamic hr archive folders
            _, destinationId, newMessageId = o365_instance.move_message_dynamic(current_email.MessageId,configuration['user_assign_parent_folder_name'])        
        else:
            logger.warn('ConversationId not matched with record in database_assignment_folder table')
            raise NotImplementedError('Missing implementation when mapped response is not found')            
    else:
        logger.info("Assignee folder is not mapped to this conversation id in database_assignment_folder table - So it is first thread")
        
def add_assignee_folder_in_db(incident, current_email):
        #destFoldersList, destFolderDict = o365_instance.folders_list_with_msg_count(configuration.get('user_assign_parent_folder_id'))
        destFolderDict = { 'DisplayName' : configuration['user_assign_parent_folder_name'],
            'Id' : ' '
        }
        logger.info("This folderID is {} mapped  to conversationID {}".format(destFolderDict['DisplayName'], incident.Email.ConversationId))
        insertionAssigmentFolder = AssigmentFolder_instance.add_coversation_id(incident.Email.ConversationId, destFolderDict)
        logger.debug('AssigmentFolder Insertion status . ' + str(insertionAssigmentFolder))   

# Log on console
def request_mail_log(incident_email, current_email):    
    values = get_template_values(current_email, None)
    #print(values.get('message'))
    description = Templates.gen_ticket_description(values)
    email_last_message_without_response = description.split("Request Message:",1)[1]
    email_last_message_without_response = email_last_message_without_response.replace('&', 'and').replace('"', '\"').replace('“', '\"').replace("’","'").replace('”','\"').replace("‘","'").replace('<[', ' ').replace('](', ' ').replace(')>', ' ').replace('Mayank Bansal | Test Lead | Spark Connect','')
    logger.info('User Request mail ' + email_last_message_without_response)

if __name__ == '__main__':
    logger.info('Hi there! I am {}, lets start..'.format(BASENAME))
    import argparse
    # Read the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--incident_id", type=str, help='NIA Incident ID created for HR Payroll service request', required=True)
    args = parser.parse_args()
    logger.info('I am going to working on the incident ' + args.incident_id)
    
    # executing hr payroll automation flow
    main(args.incident_id)
