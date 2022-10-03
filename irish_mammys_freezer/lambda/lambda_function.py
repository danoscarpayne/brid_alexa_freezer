# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils

import os
import boto3

from datetime import datetime

from utils import create_presigned_url, speech_output_generator_drawer

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.ui import StandardCard, SimpleCard, Image

from ask_sdk_model import Response, DialogState, Intent
from ask_sdk_model.dialog import ElicitSlotDirective
from ask_sdk_model.dialog.delegate_directive import DelegateDirective

import pandas as pd
import pickle 



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')


ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(table_name=ddb_table_name, create_table=False, dynamodb_resource=ddb_resource)

image_url = create_presigned_url("Media/freezer_images/brid_freezer_icon.png")


# mapping for drawers
drawer_map = {1 : 'the top drawer',
             2 : 'the second from top drawer',
             3 : 'the third from top drawer',
             4 : 'big box 1',
             5 : 'big box 2',
             6 : 'the second from bottom drawer',
             7 : 'bottom drawer'}


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome to your freezer!"
        
        image_url = create_presigned_url("Media/freezer_images/brid_freezer_icon.png")
        

        return (
            handler_input.response_builder
                .speak(speak_output).set_card(
             StandardCard(title='', text=speak_output, image=Image(
                    small_image_url=image_url, large_image_url=image_url)))
                .response)


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hello World!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response)
        
class ResetIntentHandler(AbstractRequestHandler):
    
    """Handler for Locate Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("InitialFreezer")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response  
        
        speak_output = 'Woo hoo you will go back to initial food'
        
        pickle_url = create_presigned_url("Media/freezer_data/brid_freezer.csv")
        
        # Load pickle file 
        new_freezer = pd.read_csv(pickle_url)
        
        print(new_freezer.shape)
        
        new_freezer.drawer_no = new_freezer.drawer_no.astype(str)
        new_freezer.item_qty = new_freezer.item_qty.astype(str)
        new_freezer.food_type = new_freezer.food_type.fillna('')
        
        # extract persistent attributes, if they exist
        full_attributes = handler_input.attributes_manager.persistent_attributes
        
        full_attributes['content'] = new_freezer.to_dict(orient = 'records')
                    
        attributes_manager = handler_input.attributes_manager
        attributes_manager.persistent_attributes = full_attributes
        attributes_manager.save_persistent_attributes()
        
        return (
            handler_input.response_builder
                .speak(speak_output).set_card(
             StandardCard(title='', text=speak_output, image=Image(
                    small_image_url=image_url, large_image_url=image_url)))
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response)
                
class AddFoodItemIntentHandler(AbstractRequestHandler):
    
    """Handler for Locate Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("add_food_item")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        # output container
        output_container = []
        
        # extract persistent attributes, if they exist
        full_attributes = handler_input.attributes_manager.persistent_attributes
        #print(full_attributes['content'])
        
        # Get slots
        input_slots = handler_input.request_envelope.request.intent.slots
        
        print(input_slots)
        
        # needed variables
        food_name = input_slots['food_item'].value
        item_qty = input_slots['item_qty'].value
        item_qty = '1' if item_qty == None else item_qty
        
        no_units = input_slots['no_overall_items'].value
        no_units = '1' if no_units == None else no_units
        
        food_type = input_slots['type'].value
        
        
        if ('quorn' in food_name.lower()) or ('vegetarian' in food_name.lower()) or ('corn' in food_name.lower()):
            food_type = 'v'
            
        elif food_type == None:
            
            food_type = ''
        else:
            food_type = food_type
        
        #food_type = '' if food_type == None else food_type
        
        freezer_drawer = input_slots['freezer_drawer'].value
        drawer_id = input_slots['freezer_drawer'].resolutions.resolutions_per_authority[0].values[0].value.id
        
        # Loop through
        for i in range(int(no_units)):
            
            # time of entry
            dt_info = datetime.now().isoformat()
            
            # dict to add to output container
            f_dict = {'food_name' : food_name,
                        'item_qty' : item_qty,
                        'food_type' : food_type,
                        'datetime' : dt_info,
                        'drawer_no' : drawer_id}
                        
            print(f_dict)
                        
            # add to output_container
            output_container.append(f_dict)
                        
        
         # build Response
        speak_output = "The food you wish to add is {} to {}".format(food_name, freezer_drawer)
        
        dt_info = datetime.now().isoformat()
        
        if 'content' in full_attributes.keys():
            
        
            full_attributes['content'] += output_container
        
        else:
            
            full_attributes['content'] = output_container
        
        
        
        attributes_manager = handler_input.attributes_manager
        attributes_manager.persistent_attributes = full_attributes
        attributes_manager.save_persistent_attributes()
        
        card_title = "You have added the following to {}".format(freezer_drawer)
        card_text = "{}".format(food_name)
        
        #image_url = 'https://freezerbucket.s3.eu-west-1.amazonaws.com/brid_freezer_icon.png'
        
        return (
            handler_input.response_builder
                .speak(speak_output).set_card(
            StandardCard(title=card_title, text=card_text, image=Image(
                    small_image_url=image_url, large_image_url=image_url)))
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response)
                
class CheckVegetarianFoodIntentHandler(AbstractRequestHandler):
    
    
    """Handler for Locate Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CheckVegetarian")(handler_input) 
        
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        
        # extract persistent attributes, if they exist
        full_attributes = handler_input.attributes_manager.persistent_attributes
        
        df_freezer = pd.DataFrame(full_attributes['content'])
        
        veg_df = df_freezer.loc[df_freezer.food_type == 'v']
        
        speak_output = ' '
                
        for drawer in veg_df.drawer_no.unique():
            
        
            # reduce to drawer contents 
            drawer_df = veg_df.loc[veg_df.drawer_no == drawer]
            
            speak_output += 'in {} '.format(drawer_map.get(int(drawer)))
    
    
            grp_df = drawer_df.groupby(['food_name', 'food_type', 'item_qty'], as_index = False).count().rename(columns = {'drawer_no' : 'units'})
    
            d_output = speech_output_generator_drawer(grp_df)
            
            speak_output += d_output
            
        return (
            handler_input.response_builder
                .speak(speak_output).set_card(
             StandardCard(title='', text=speak_output, image=Image(
                    small_image_url=image_url, large_image_url=image_url)))
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response)
                
class CheckFoodItemIntentHandler(AbstractRequestHandler):
    
    """Handler for Locate Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("check_food_item")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        food_name = ask_utils.request_util.get_slot(handler_input, "food_item").value
        
        
        # extract persistent attributes, if they exist
        full_attributes = handler_input.attributes_manager.persistent_attributes
        
        if 'content' in full_attributes.keys():
            
            df_freezer = pd.DataFrame(full_attributes['content'])
            
            df_freezer['item_qty'] = df_freezer['item_qty'].map(lambda x: x if x.isnumeric() else '1')
            
            print('I am performing Check Food Item')
            
            print(df_freezer)
            
            selected_food_df = df_freezer.loc[df_freezer.food_name.str.lower().str.contains(food_name.lower())]
            
            if selected_food_df.empty:
                
                # build Response
                speak_output = "I cannot find {} in your freezer".format(food_name)
                
            elif len(selected_food_df) == 1:
                
                found_food, drawer, qty = selected_food_df[['food_name', 'drawer_no', 'item_qty']].values[0]
                
                qty_statement = ''
                
                if int(qty) > 1:
                    
                    qty_statement = 'a packet of {} '.format(qty)
                
                speak_output = "you have {}{} in {}".format(qty_statement, found_food, drawer_map.get(int(drawer)))
                
            else:
                
                speak_output = ' '
                
                for drawer in selected_food_df.drawer_no.unique():
                    
                
                    # reduce to drawer contents 
                    drawer_df = selected_food_df.loc[selected_food_df.drawer_no == drawer]
                    
                    speak_output += 'in {} '.format(drawer_map.get(int(drawer)))
            
            
                    grp_df = drawer_df.groupby(['food_name', 'food_type', 'item_qty'], as_index = False).count().rename(columns = {'drawer_no' : 'units'})
            
                    d_output = speech_output_generator_drawer(grp_df)
                    
                    speak_output += d_output
                
                    '''speak_output = 'you have \n'
                    
                    for found_food, drawer, qty in selected_food_df[['food_name', 'drawer_no', 'item_qty']].values[:-1]:
                        
                        qty_statement = ''
                    
                        if int(qty) > 1:
                            
                            qty_statement = 'a packet of {} '.format(qty)
                        
                        speak_output += '{}{} in {}\n '.format(qty_statement, found_food, drawer_map.get(int(drawer)))
                        
                    found_food, drawer, qty = selected_food_df[['food_name', 'drawer_no', 'item_qty']].values[-1]
                    
                    qty_statement = ''
                    
                    if int(qty) > 1:
                        
                        qty_statement = 'a packet of {} '.format(qty)
                    
                    speak_output += 'and {}{} in {}'.format(qty_statement, found_food, drawer_map.get(int(drawer)))'''
            
        
        
        
        return (
            handler_input.response_builder
                .speak(speak_output).set_card(
             StandardCard(title='', text=speak_output, image=Image(
                    small_image_url=image_url, large_image_url=image_url)))
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response)
                
class CheckDrawersIntentHandler(AbstractRequestHandler):
    
    """Handler for Locate Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("check_drawer_contents")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        # Get slots
        input_slots = handler_input.request_envelope.request.intent.slots
        
        # freezer_drawer        
        freezer_drawer = input_slots['freezer_drawer'].resolutions.resolutions_per_authority[0].values[0].value.id
        
        print('I am performing Check Drawer Items')
        
        
        # extract persistent attributes, if they exist
        full_attributes = handler_input.attributes_manager.persistent_attributes
        
        if 'content' in full_attributes.keys():
            
            df_freezer = pd.DataFrame(full_attributes['content'])
            
            df_freezer['item_qty'] = df_freezer['item_qty'].map(lambda x: x if x.isnumeric() else '1')
            
            # reduce to drawer contents 
            drawer_df = df_freezer.loc[df_freezer.drawer_no == freezer_drawer]
            
            
            grp_df = drawer_df.groupby(['food_name', 'food_type', 'item_qty'], as_index = False).count().rename(columns = {'drawer_no' : 'units'})
            
            speak_output = speech_output_generator_drawer(grp_df)
            
        else:
            
            speak_output = 'Please add food to your freezer to do this'
        
        
        return (
            handler_input.response_builder
                .speak(speak_output).set_card(
             StandardCard(title='', text=speak_output, image=Image(
                    small_image_url=image_url, large_image_url=image_url)))
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response)
                
class UpdateFoodItemIntentHandler(AbstractRequestHandler):
    
    """Handler for Locate Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("update_food_item")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        # Get slots
        input_slots = handler_input.request_envelope.request.intent.slots
        
        # needed variables
        food_name = input_slots['food_item'].value
        freezer_drawer = input_slots['freezer_drawer'].resolutions.resolutions_per_authority[0].values[0].value.id
        item_qty = input_slots['item_qty'].value
        
        
        # extract persistent attributes, if they exist
        full_attributes = handler_input.attributes_manager.persistent_attributes
        
        if 'content' in full_attributes.keys():
            
            df_freezer = pd.DataFrame(full_attributes['content'])
            
            
            selected_food_df = df_freezer.loc[df_freezer.food_name.str.lower().str.contains(food_name.lower())]
            
            if selected_food_df.empty:
                
                # build Response
                speak_output = "I cannot find {} in your freezer".format(food_name)
                
                return (
                        handler_input.response_builder
                            .speak(speak_output).set_card(
                         StandardCard(title='', text=speak_output, image=Image(
                                small_image_url=image_url, large_image_url=image_url)))
                            # .ask("add a reprompt if you want to keep the session open for the user to respond")
                            .response)
                
            else:
                
                update_df = selected_food_df.loc[selected_food_df.drawer_no == freezer_drawer]
                
                
                
                # Check if food present
                if update_df.empty:
                    
                    speak_output = 'I don\'t have it in that location. I have'
                    
                    for i, row in selected_food_df[['food_name', 'drawer_no']].iterrows():
                        
                        if i >= 1:
                            
                            speak_output += ' and'
                        
                        speak_output += ' {} in location {}'.format(row.food_name, drawer_map.get(int(row.drawer_no)))
                        
                    speak_output += '\n If you  want to update one of these items, say update {} from {} to {}'.format(found_food, drawer_map.get(int(drawer)), item_qty)
                    
                    return (
                        handler_input.response_builder
                            .speak(speak_output).set_card(
                         StandardCard(title='', text=speak_output, image=Image(
                                small_image_url=image_url, large_image_url=image_url)))
                            # .ask("add a reprompt if you want to keep the session open for the user to respond")
                            .response)
                
                elif len(update_df) == 1:
                    
                    # get index
                    idx_update = update_df.index
                    
                    if int(item_qty) > 0:
                
                        # update item qty
                        df_freezer.loc[idx_update, 'item_qty'] = item_qty
                        
                        speak_output = 'I have updated {} in {} to {}'.format(food_name, drawer_map.get(int(freezer_drawer)),item_qty)
                        
                    else:
                        
                        df_freezer = df_freezer.drop(idx_update)
                        
                        speak_output = 'I have removed {} in {}'.format(food_name, location)
                    
                    
                    full_attributes['content'] = df_freezer.to_dict(orient = 'records')
                    
                    attributes_manager = handler_input.attributes_manager
                    attributes_manager.persistent_attributes = full_attributes
                    attributes_manager.save_persistent_attributes()
                    
                    return (
                    handler_input.response_builder
                        .speak(speak_output).set_card(
                     StandardCard(title='', text=speak_output, image=Image(
                            small_image_url=image_url, large_image_url=image_url)))
                        # .ask("add a reprompt if you want to keep the session open for the user to respond")
                        .response)
                    
                    
                else:
                    # Access session attributes
                    # Get any existing attributes from the incoming request
                    session_attr = handler_input.attributes_manager.session_attributes
                
                    session_attr["item_qty"] = item_qty
                    
                    # initiate dictionary
                    opt_dict  = {}
                    
                    counter = 1
                    
                    for i, row in update_df.iterrows():
                        
                        opt_dict[str(counter)] = {'name' : row['food_name'], 'i.d.' : i, 'location' : drawer_map[int(row['drawer_no'])], 'initial_qty' : row['item_qty']}
                        
                        counter += 1
                        
                    #str_dict = json.dumps(opt_dict)
                        
                    session_attr["update_options"] = opt_dict
                    
                    speak_output = 'This is ambiguous I have too many items. please select an option. '
                    
                    for options in session_attr["update_options"].keys():
                        
                        speak_output += ' option {}, {} in {}'.format(options, session_attr["update_options"][options]['name'], session_attr["update_options"][options]['location'])
                        
                        if int(session_attr["update_options"][options]['initial_qty']) > 1:
                            
                            speak_output += ' with {} in the packet'.format(session_attr["update_options"][options]['initial_qty'])
                    
                    speak_output += ' please select an option'
                    
                    reprompt = 'please select an option'
        
                    return (
                        handler_input.response_builder.speak(speak_output).ask(reprompt).set_card(
                     StandardCard(title='', text=speak_output, image=Image(
                            small_image_url=image_url, large_image_url=image_url))).add_directive(ElicitSlotDirective(
                                updated_intent=Intent(
                                    name="selectFoodItem"), 
                                slot_to_elicit="food_option")).response)
                    
        else:
            
            speak_output = 'you have no food in your freezer.  Please add food to do this operation'
                
                
            
        #image_url = 'https://freezerbucket.s3.eu-west-1.amazonaws.com/brid_freezer_icon.png'
        #image_url = 'arn:aws:s3:::freezerbucket/brid_freezer_icon.png'
        
        
        return (
            handler_input.response_builder
                .speak(speak_output).set_card(
             StandardCard(title='', text=speak_output, image=Image(
                    small_image_url=image_url, large_image_url=image_url)))
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response)
                
class MoveFoodItemIntentHandler(AbstractRequestHandler):
    
    """Handler for Locate Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("move_food_item")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        # Get slots
        input_slots = handler_input.request_envelope.request.intent.slots
        
        # needed variables
        food_name = input_slots['food_item'].value
        from_location = input_slots['from_location'].resolutions.resolutions_per_authority[0].values[0].value.id
        to_location = input_slots['to_location'].resolutions.resolutions_per_authority[0].values[0].value.id
        
        
        # extract persistent attributes, if they exist
        full_attributes = handler_input.attributes_manager.persistent_attributes
        
        if 'content' in full_attributes.keys():
            
            df_freezer = pd.DataFrame(full_attributes['content'])
            
            
            selected_food_df = df_freezer.loc[df_freezer.food_name.str.lower().str.contains(food_name.lower())]
            
            if selected_food_df.empty:
                
                # build Response
                speak_output = "I cannot find {} in your freezer".format(food_name)
                
                return (
                        handler_input.response_builder
                            .speak(speak_output).set_card(
                         StandardCard(title='', text=speak_output, image=Image(
                                small_image_url=image_url, large_image_url=image_url)))
                            # .ask("add a reprompt if you want to keep the session open for the user to respond")
                            .response)
                
            else:
                
                move_df = selected_food_df.loc[selected_food_df.drawer_no == from_location]
                
                
                
                # Check if food present
                if move_df.empty:
                    
                    speak_output = 'I don\'t have it in that location. I have'
                    
                    for i, row in selected_food_df[['food_name', 'drawer_no']].iterrows():
                        
                        if i >= 1:
                            
                            speak_output += ' and'
                        
                        speak_output += ' {} in location {}'.format(row.food_name, drawer_map.get(int(row.drawer_no)))
                        
                    speak_output += '\n If you  want to move one of these items, say move {} from {} to {}'.format(row.food_name, drawer_map.get(int(row.drawer_no)), drawer_map.get(int(to_location)))
                    
                    return (
                        handler_input.response_builder
                            .speak(speak_output).set_card(
                         StandardCard(title='', text=speak_output, image=Image(
                                small_image_url=image_url, large_image_url=image_url)))
                            # .ask("add a reprompt if you want to keep the session open for the user to respond")
                            .response)
                
                elif len(move_df) == 1:
                    
                    # get index
                    idx_move = move_df.index
                
                    # update item qty
                    df_freezer.loc[idx_move, 'drawer_no'] = to_location
                    
                    speak_output = 'I have moved {} in {} to {}'.format(food_name, drawer_map.get(int(from_location)),drawer_map.get(int(to_location)))
                    
                    
                    full_attributes['content'] = df_freezer.to_dict(orient = 'records')
                    
                    attributes_manager = handler_input.attributes_manager
                    attributes_manager.persistent_attributes = full_attributes
                    attributes_manager.save_persistent_attributes()
                    
                    return (
                    handler_input.response_builder
                        .speak(speak_output).set_card(
                     StandardCard(title='', text=speak_output, image=Image(
                            small_image_url=image_url, large_image_url=image_url)))
                        # .ask("add a reprompt if you want to keep the session open for the user to respond")
                        .response)
                    
                    
                else:
                    # Access session attributes
                    # Get any existing attributes from the incoming request
                    session_attr = handler_input.attributes_manager.session_attributes
                
                    session_attr["to_location"] = to_location
                    
                    # initiate dictionary
                    opt_dict  = {}
                    
                    counter = 1
                    
                    for i, row in move_df.iterrows():
                        
                        opt_dict[str(counter)] = {'name' : row['food_name'], 'i.d.' : i, 'location' : row['drawer_no'], 'initial_qty' : row['item_qty']}
                        
                        counter += 1
                        
                    #str_dict = json.dumps(opt_dict)
                        
                    session_attr["move_options"] = opt_dict
                    
                    speak_output = 'This is ambiguous I have too many items. please select an option. '
                    
                    for options in session_attr["move_options"].keys():
                        
                        speak_output += ' option {}, {} in {}'.format(options, session_attr["move_options"][options]['name'], drawer_map.get(int(session_attr["move_options"][options]['location'])))
                        
                        if int(session_attr["move_options"][options]['initial_qty']) > 1:
                            
                            speak_output += ' with {} in the packet'.format(session_attr["move_options"][options]['initial_qty'])
                    
                    speak_output += ' please select an option'
                    
                    reprompt = 'please select an option'
        
                    return (
                        handler_input.response_builder.speak(speak_output).ask(reprompt).set_card(
                     StandardCard(title='', text=speak_output, image=Image(
                            small_image_url=image_url, large_image_url=image_url))).add_directive(ElicitSlotDirective(
                                updated_intent=Intent(
                                    name="selectFoodItem"), 
                                slot_to_elicit="food_option")).response)
                    
        else:
            
            speak_output = 'you have no food in your freezer.  Please add food to do this operation'
                
                
            
        #image_url = 'https://freezerbucket.s3.eu-west-1.amazonaws.com/brid_freezer_icon.png'
        #image_url = 'arn:aws:s3:::freezerbucket/brid_freezer_icon.png'
        
        
        return (
            handler_input.response_builder
                .speak(speak_output).set_card(
             StandardCard(title='', text=speak_output, image=Image(
                    small_image_url=image_url, large_image_url=image_url)))
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response)
                
class DeleteFoodItemIntentHandler(AbstractRequestHandler):
    
    """Handler for Locate Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("delete_food_item")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        # Get slots
        input_slots = handler_input.request_envelope.request.intent.slots
        
        # needed variables
        food_name = input_slots['food_item'].value
        freezer_drawer = input_slots['freezer_drawer'].resolutions.resolutions_per_authority[0].values[0].value.id
        
        
        
        # extract persistent attributes, if they exist
        full_attributes = handler_input.attributes_manager.persistent_attributes
        
        if 'content' in full_attributes.keys():
            
            df_freezer = pd.DataFrame(full_attributes['content'])
            
            
            selected_food_df = df_freezer.loc[df_freezer.food_name.str.lower().str.contains(food_name.lower())]
            
            if selected_food_df.empty:
                
                # build Response
                speak_output = "I cannot find {} in your freezer".format(food_name)
                
                return (
                        handler_input.response_builder
                            .speak(speak_output).set_card(
                         StandardCard(title='', text=speak_output, image=Image(
                                small_image_url=image_url, large_image_url=image_url)))
                            # .ask("add a reprompt if you want to keep the session open for the user to respond")
                            .response)
                
            else:
                
                delete_df = selected_food_df.loc[selected_food_df.drawer_no == freezer_drawer]
                
                
                
                # Check if food present
                if delete_df.empty:
                    
                    speak_output = 'I don\'t have it in that location. I have'
                    
                    for i, row in selected_food_df[['food_name', 'drawer_no']].iterrows():
                        
                        if i >= 1:
                            
                            speak_output += ' and'
                        
                        speak_output += ' {} in location {}'.format(row.food_name, drawer_map.get(int(row.drawer_no)))
                        
                    speak_output += '\n If you  want to delete one of these items, say remove {} from {}'.format(row.food_name, drawer_map.get(int(row.drawer_no)))
                    
                    return (
                        handler_input.response_builder
                            .speak(speak_output).set_card(
                         StandardCard(title='', text=speak_output, image=Image(
                                small_image_url=image_url, large_image_url=image_url)))
                            # .ask("add a reprompt if you want to keep the session open for the user to respond")
                            .response)
                
                elif len(delete_df) == 1:
                    
                    # get index
                    idx_del = delete_df.index
                
                    # update item qty
                    df_freezer = df_freezer.drop(idx_del)
                    
                    speak_output = 'I have removed {} in {}'.format(food_name, drawer_map.get(int(freezer_drawer)))
                    
                    
                    full_attributes['content'] = df_freezer.to_dict(orient = 'records')
                    
                    attributes_manager = handler_input.attributes_manager
                    attributes_manager.persistent_attributes = full_attributes
                    attributes_manager.save_persistent_attributes()
                    
                    return (
                    handler_input.response_builder
                        .speak(speak_output).set_card(
                     StandardCard(title='', text=speak_output, image=Image(
                            small_image_url=image_url, large_image_url=image_url)))
                        # .ask("add a reprompt if you want to keep the session open for the user to respond")
                        .response)
                    
                    
                else:
                    # Access session attributes
                    # Get any existing attributes from the incoming request
                    session_attr = handler_input.attributes_manager.session_attributes
                
                    session_attr["freezer_drawer"] = freezer_drawer
                    
                    # initiate dictionary
                    opt_dict  = {}
                    
                    counter = 1
                    
                    for i, row in delete_df.iterrows():
                        
                        opt_dict[str(counter)] = {'name' : row['food_name'], 'i.d.' : i, 'location' : row['drawer_no'], 'initial_qty' : row['item_qty']}
                        
                        counter += 1
                        
                    #str_dict = json.dumps(opt_dict)
                        
                    session_attr["delete_options"] = opt_dict
                    
                    speak_output = 'This is ambiguous I have too many items. please select an option. '
                    
                    for options in session_attr["delete_options"].keys():
                        
                        speak_output += ' option {}, {} in {}'.format(options, session_attr["delete_options"][options]['name'], drawer_map.get(int(session_attr["delete_options"][options]['location'])))
                        
                        if int(session_attr["delete_options"][options]['initial_qty']) > 1:
                            
                            speak_output += ' with {} in the packet'.format(session_attr["delete_options"][options]['initial_qty'])
                    
                    speak_output += ' please select an option'
                    
                    reprompt = 'please select an option'
        
                    return (
                        handler_input.response_builder.speak(speak_output).ask(reprompt).set_card(
                     StandardCard(title='', text=speak_output, image=Image(
                            small_image_url=image_url, large_image_url=image_url))).add_directive(ElicitSlotDirective(
                                updated_intent=Intent(
                                    name="selectFoodItem"), 
                                slot_to_elicit="food_option")).response)
                    
        else:
            
            speak_output = 'you have no food in your freezer.  Please add food to do this operation'
                
                
            
        #image_url = 'https://freezerbucket.s3.eu-west-1.amazonaws.com/brid_freezer_icon.png'
        #image_url = 'arn:aws:s3:::freezerbucket/brid_freezer_icon.png'
        
        
        return (
            handler_input.response_builder
                .speak(speak_output).set_card(
             StandardCard(title='', text=speak_output, image=Image(
                    small_image_url=image_url, large_image_url=image_url)))
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response)

class SelectFoodIntentHandler(AbstractRequestHandler):
    """Handler for FavoriteColorIntent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("selectFoodItem")(
            handler_input) and ask_utils.get_dialog_state(
            handler_input=handler_input) == DialogState.COMPLETED
 
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
 
        # Get any existing attributes from the incoming request
        session_attr = handler_input.attributes_manager.session_attributes
        
        
        check_slots = handler_input.request_envelope.request.intent.slots
        print(check_slots)
 
        # Get the slot value from the request and add it to the session 
        # attributes dictionary. Because of the dialog model and dialog 
        # delegation, this code only ever runs when the favoriteColor slot 
        # contains a value, so a null check is not necessary.
        food_option = ask_utils.request_util.get_slot(handler_input, "food_option")
        
        
        if not food_option:
            
            speech_text = "I am sorry, i did not get an option"
            
            return handler_input.response_builder.speak(speech_text).response
             
        else:
            
            if session_attr.get("move_options", None):
            
                move_options = session_attr["move_options"]
                #move_options = json.loads(session_attr["move_options"])
                
                food_id = move_options[food_option.value]['i.d.']
                food_name = move_options[food_option.value]['name']
                to_location = session_attr["to_location"]
                
                print(food_name, food_id)
                
                
               # extract persistent attributes, if they exist
                full_attributes = handler_input.attributes_manager.persistent_attributes
                
                # Make df_freezer
                df_freezer = pd.DataFrame(full_attributes.get('content', []))
                
                # update item qty
                df_freezer.loc[food_id, 'drawer_no'] = to_location
                
                speak_output = 'I have moved {} to {}'.format(food_name, drawer_map.get(int(to_location)))
                
                full_attributes['content'] = df_freezer.to_dict(orient = 'records')
                    
                attributes_manager = handler_input.attributes_manager
                attributes_manager.persistent_attributes = full_attributes
                attributes_manager.save_persistent_attributes()
                
                session_attr["move_options"] = None
                session_attr["to_location"] = None
                    
                return (
                handler_input.response_builder
                    .speak(speak_output).set_card(
                        StandardCard(title='', text=speak_output, image=Image(
                        small_image_url=image_url, large_image_url=image_url)))
                    # .ask("add a reprompt if you want to keep the session open for the user to respond")
                        .response)
                    
                    
            elif session_attr.get("delete_options"):
                
                delete_options = session_attr["delete_options"]
                #move_options = json.loads(session_attr["move_options"])
                
                food_id = delete_options[food_option.value]['i.d.']
                food_name = delete_options[food_option.value]['name']
                freezer_drawer = session_attr["freezer_drawer"]
                
                print(food_name, food_id)
                
                
                # extract persistent attributes, if they exist
                full_attributes = handler_input.attributes_manager.persistent_attributes
                
                # Make df_freezer
                df_freezer = pd.DataFrame(full_attributes.get('content', []))
                
                df_freezer = df_freezer.drop(food_id)
                
                full_attributes['content'] = df_freezer.to_dict(orient = 'records')
                
                attributes_manager = handler_input.attributes_manager
                attributes_manager.persistent_attributes = full_attributes
                attributes_manager.save_persistent_attributes()
                
                session_attr["delete_options"] = None
                session_attr["freezer_drawer"] = None
                
                speak_output = 'I have removed {} in {}'.format(food_name, drawer_map.get(int(freezer_drawer)))
                    
                return (
                handler_input.response_builder
                    .speak(speak_output).set_card(
                        StandardCard(title='', text=speak_output, image=Image(
                        small_image_url=image_url, large_image_url=image_url)))
                    # .ask("add a reprompt if you want to keep the session open for the user to respond")
                    .response)
                    
            elif session_attr.get("update_options"):
                
                update_options = session_attr["update_options"]
                #move_options = json.loads(session_attr["move_options"])
                
                food_id = update_options[food_option.value]['i.d.']
                food_name = update_options[food_option.value]['name']
                location = update_options[food_option.value]['location']
                item_qty = session_attr["item_qty"]
                
                print(food_name, food_id)
                
                # extract persistent attributes, if they exist
                full_attributes = handler_input.attributes_manager.persistent_attributes
                
                # Make df_freezer
                df_freezer = pd.DataFrame(full_attributes.get('content', []))
                
                if int(item_qty) > 0:
                
                    # update item qty
                    df_freezer.loc[food_id, 'item_qty'] = item_qty
                    
                    speak_output = 'I have updated {} in {} to {}'.format(food_name, location,item_qty)
                    
                else:
                    
                    df_freezer = df_freezer.drop(food_id)
                    
                    speak_output = 'I have removed {} in {}'.format(food_name, location)
                
                full_attributes['content'] = df_freezer.to_dict(orient = 'records')
                    
                attributes_manager = handler_input.attributes_manager
                attributes_manager.persistent_attributes = full_attributes
                attributes_manager.save_persistent_attributes()
                    
                session_attr["update_options"] = None
                session_attr["item_qty"] = None
            
                
                    
                
                    
                return (
                    handler_input.response_builder
                        .speak(speak_output).set_card(
                        StandardCard(title='', text=speak_output, image=Image(
                        small_image_url=image_url, large_image_url=image_url)))
                    # .ask("add a reprompt if you want to keep the session open for the user to respond")
                        .response)
                    
                    
            else:
                
                speak_output = 'I encountered a problem please try again'.format(food_name)
                    
                return (
                handler_input.response_builder
                    .speak(speak_output)
                    # .ask("add a reprompt if you want to keep the session open for the user to respond")
                    .response)

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = CustomSkillBuilder(persistence_adapter = dynamodb_adapter)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(ResetIntentHandler())
sb.add_request_handler(AddFoodItemIntentHandler())
sb.add_request_handler(CheckFoodItemIntentHandler())
sb.add_request_handler(CheckDrawersIntentHandler())
sb.add_request_handler(CheckVegetarianFoodIntentHandler())
sb.add_request_handler(UpdateFoodItemIntentHandler())
sb.add_request_handler(MoveFoodItemIntentHandler())
sb.add_request_handler(DeleteFoodItemIntentHandler())
sb.add_request_handler(SelectFoodIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()