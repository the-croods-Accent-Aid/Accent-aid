import requests
import base64
import json
import time
import random
import azure.cognitiveservices.speech as speechsdk

from flask import Flask, jsonify, render_template, request, make_response

app = Flask(__name__)

subscription_key = "my_sub_key"
region = "region_name"
language = "en-US"
voice = "Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/readalong")
def readalong():
    return render_template("readalong.html")

@app.route("/gettoken", methods=["POST"])
def gettoken():
    fetch_token_url = 'https://%s.api.cognitive.microsoft.com/sts/v1.0/issueToken' %region
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key
    }
    response = requests.post(fetch_token_url, headers=headers)
    access_token = response.text
    return jsonify({"at":access_token})


@app.route("/gettonguetwister", methods=["POST"])
def gettonguetwister():
    tonguetwisters = ["Thank you for considering my application",
"I am excited about the opportunity to work with your company",
"I have extensive experience in this field",
"I am confident in my ability to contribute to the team",
"I am a quick learner and adapt well to new environments",
"I am highly motivated and results-oriented",
"I have strong problem-solving skills",
"I am proficient in the necessary software and tools",
"I am a team player and enjoy collaborating with others",
"I am comfortable working under pressure and meeting deadlines",
"I have excellent communication skills, both written and verbal",
"I am detail-oriented and strive for accuracy in my work",
"I am committed to continuous learning and professional development",
"I am familiar with industry best practices",
"I am comfortable taking on leadership roles when necessary",
"I am skilled at managing multiple projects simultaneously",
"I am experienced in working with diverse teams and cultures",
"I am passionate about delivering exceptional customer service",
"I am adept at analyzing data and making data-driven decisions",
"I am committed to maintaining confidentiality and data security",
"I am well-versed in risk management and mitigation strategies",
"I am knowledgeable in regulatory compliance requirements",
"I am experienced in developing and implementing strategies",
"I am skilled in conducting market research and competitor analysis",
"I am proficient in creating and delivering presentations",
"I am comfortable working independently with minimal supervision",
"I am experienced in managing budgets and financial resources",
"I am skilled at building and maintaining professional relationships",
"I am committed to fostering a positive and inclusive work environment",
"I am adaptable and embrace change",
"I am passionate about innovation and continuous improvement",
"I am familiar with project management methodologies",
"I am skilled at negotiating and influencing others",
"I am experienced in conducting performance evaluations",
"I am adept at conflict resolution and problem-solving",
"I am committed to meeting and exceeding targets and goals",
"I am knowledgeable in industry trends and emerging technologies",
"I am experienced in managing cross-functional teams",
"I am skilled at developing and implementing marketing strategies",
"I am comfortable working with clients and stakeholders",
"I am proficient in time management and prioritizing tasks",
"I am committed to maintaining a high level of professionalism",
"I am skilled at managing and resolving customer issues",
"I am experienced in developing and executing sales plans",
"I am knowledgeable in regulatory and legal compliance",
"I am comfortable presenting to senior management and executives",
"I am committed to fostering a culture of innovation and creativity",
"I am skilled at analyzing financial statements and making recommendations",
"I am experienced in leading and motivating teams",
"I am passionate about contributing to the success of the organization",]
    
    return jsonify({"tt":random.choice(tonguetwisters)})

@app.route("/ackaud", methods=["POST"])
def ackaud():
    f = request.files['audio_data']
    reftext = request.form.get("reftext")
    #    f.save(audio)
    #print('file uploaded successfully')

    # a generator which reads audio data chunk by chunk
    # the audio_source can be any audio input stream which provides read() method, e.g. audio file, microphone, memory stream, etc.
    def get_chunk(audio_source, chunk_size=1024):
        while True:
            #time.sleep(chunk_size / 32000) # to simulate human speaking rate
            chunk = audio_source.read(chunk_size)
            if not chunk:
                #global uploadFinishTime
                #uploadFinishTime = time.time()
                break
            yield chunk

    # build pronunciation assessment parameters
    referenceText = reftext
    pronAssessmentParamsJson = "{\"ReferenceText\":\"%s\",\"GradingSystem\":\"HundredMark\",\"Dimension\":\"Comprehensive\",\"EnableMiscue\":\"True\"}" % referenceText
    pronAssessmentParamsBase64 = base64.b64encode(bytes(pronAssessmentParamsJson, 'utf-8'))
    pronAssessmentParams = str(pronAssessmentParamsBase64, "utf-8")

    # build request
    url = "https://%s.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=%s&usePipelineVersion=0" % (region, language)
    headers = { 'Accept': 'application/json;text/xml',
                'Connection': 'Keep-Alive',
                'Content-Type': 'audio/wav; codecs=audio/pcm; samplerate=16000',
                'Ocp-Apim-Subscription-Key': subscription_key,
                'Pronunciation-Assessment': pronAssessmentParams,
                'Transfer-Encoding': 'chunked',
                'Expect': '100-continue' }

    #audioFile = open('audio.wav', 'rb')
    audioFile = f
    # send request with chunked data
    response = requests.post(url=url, data=get_chunk(audioFile), headers=headers)
    #getResponseTime = time.time()
    audioFile.close()

    #latency = getResponseTime - uploadFinishTime
    #print("Latency = %sms" % int(latency * 1000))

    return response.json()

@app.route("/gettts", methods=["POST"])
def gettts():
    reftext = request.form.get("reftext")
    # Creates an instance of a speech config with specified subscription key and service region.
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = voice

    offsets=[]

    def wordbound(evt):
        offsets.append( evt.audio_offset / 10000)

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

    speech_synthesizer.synthesis_word_boundary.connect(wordbound)

    result = speech_synthesizer.speak_text_async(reftext).get()
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data
        
        response = make_response(audio_data)
        response.headers['Content-Type'] = 'audio/wav'
        response.headers['Content-Disposition'] = 'attachment; filename=sound.wav'
        response.headers['offsets'] = offsets
        return response
        
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
        return jsonify({"success":False})

@app.route("/getttsforword", methods=["POST"])
def getttsforword():
    word = request.form.get("word")

    # Creates an instance of a speech config with specified subscription key and service region.
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = voice

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

    result = speech_synthesizer.speak_text_async(word).get()
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        #print("Speech synthesized for text [{}]".format(reftext))
        #print(offsets)
        audio_data = result.audio_data
        #print(audio_data)
        #print("{} bytes of audio data received.".format(len(audio_data)))
        
        response = make_response(audio_data)
        response.headers['Content-Type'] = 'audio/wav'
        response.headers['Content-Disposition'] = 'attachment; filename=sound.wav'
        
        return response
        
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
        return jsonify({"success":False})
