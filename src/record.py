#!/usr/bin/env python

# Copyright (c) 2016 PAL Robotics SL. All Rights Reserved
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all
# copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
# Author:
#   * Sammy Pfeiffer

import sys
import rospy
from actionlib import SimpleActionClient
import requests
import json
import speech_recognition as sr
import re
# To get the type of msg we will need if we have the robot running:
#   rostopic type /tts/goal
#   pal_interaction_msgs/TtsActionGoal
# Action servers always have a type XXXXAction
# and the goals are always XXXXGoal
from pal_interaction_msgs.msg import TtsAction, TtsGoal

# To test your client you can use
# rosrun actionlib axserver.py /tts pal_interaction_msgs/TtsAction
# Which will trigger a little GUI faking the action server

# The goal is just a topic so you can actually just publish on it
# but it's discouraged, it would look like (remember to press TAB to get autocompletions)
# 
# rostopic pub /tts/goal pal_interaction_msgs/TtsActionGoal "header:
#   seq: 0
#   stamp:
#     secs: 0
#     nsecs: 0
#   frame_id: ''
# goal_id:
#   stamp:
#     secs: 0
#     nsecs: 0
#   id: ''
# goal:
#   text:
#     section: ''
#     key: ''
#     lang_id: ''
#     arguments:
#     - section: ''
#       key: ''
#       expanded: ''
#   rawtext:
#     text: 'I like talking to people'
#     lang_id: 'en_GB'
#   speakerName: ''
#   wait_before_speaking: 0.0"

# extract the json string from the response
def extract_between_braces(input_string):
    start = input_string.find('{')
    end = input_string.find('}', start) + 1
    if start > 0 and end > start:
        return input_string[start:end]
    else:
        return None
 
def agent(text, url, llm_model):
   
            prompt = text
            # setup the payload for http request of llm
            payload = {
                "model": llm_model,
                "prompt": prompt,
                "stream": False,
            }
 
            # Perform the POST request with data
            response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
            
            # Check if the request was successful
            if response.status_code == 200:
                try:
                    # Attempt to parse the JSON response
                    response = response.json()
                    response = response['response']
                    return response
                except requests.exceptions.JSONDecodeError as e:
                    return e
            else:
                print("Error:", response.status_code, response.text)
                return ""

def remove_symbols_except_punctuation(text):
    # Define a regular expression pattern that matches any character that is not a period, comma, or alphanumeric
    pattern = r'[^a-zA-Z0-9.,+\-/=() ]'
    
    # Use re.sub to replace all matched characters with an empty string
    cleaned_text = re.sub(pattern, '', text)
    
    return cleaned_text

if __name__ == '__main__':
    rospy.init_node('say_something')
    # Initialize the rate object with desired frequency (Hz)
    #rate = rospy.Rate(10)  # 10 Hz

    # Define the URL of OLLAMA (VLM and LLM)
    url = "http://130.225.39.157:11434/api/generate"
 
    # Define the LLM models
    llm_model = ['llama3.1:8b', 'phi3:3.8b']
    if len(sys.argv) > 1:
            message = ""
            for arg in sys.argv[1:]:
                message += arg + " "
    # If not, just say a sentence
    else:
        message = ""
    recognizer = sr.Recognizer()
    
    mic_index = 5

    microphone = sr.Microphone(device_index=mic_index)
    # Connect to the text-to-speech action server
    client = SimpleActionClient('/tts', TtsAction)
    client.wait_for_server()
    while True: 
        # call main function
        #message = raw_input("User: ")
        if message != "":
            message = message + ". Do not answer with more than 10 words and answer as you are a Tiago robot which is used for development on a project \
            including AI llm and vlm to help people. You will in the future be able to interact with people and object. For example handing items to people."
            print(message)
            response = agent(message, url, llm_model[0])
            
            response = remove_symbols_except_punctuation(response)
            rospy.loginfo("I'll say: " + response)

            # Create a goal to say our sentence
            goal = TtsGoal()
            goal.rawtext.text = response
            goal.rawtext.lang_id = "en_GB"
            # Send the goal and wait
            client.send_goal_and_wait(goal)
            #client.send_goal(goal)
        with microphone as source:
            print("Listening...")
            try:
                # Listen for audio
                audio = recognizer.listen(source, timeout=2)
                
                # Recognize speech using Google Speech Recognition
                message = recognizer.recognize_google(audio)
                
                # Log recognized text
                rospy.loginfo("Google Speech Recognition thinks you said: %s", message)
                
            except sr.UnknownValueError:
                rospy.logwarn("Google Speech Recognition could not understand audio")
                message = ""
                
            except sr.RequestError as e:
                rospy.logwarn("Could not request results from Google Speech Recognition service: %s", e)
                message = ""
                
            except Exception as e:
                rospy.logerr("An error occurred: %s", e)
                message = ""
            
            #rate.sleep()  # Sleep to maintain the loop rate
        