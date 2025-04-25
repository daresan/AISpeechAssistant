from loguru import logger
import yaml
import time
import pvporcupine
import pyaudio
import struct
import os
import sys
import pyperclip

from vosk import Model, SpkModel, KaldiRecognizer
import json
import text2numde

sys.path.append(os.path.dirname(__file__))
print(os.path.dirname(__file__))

from TTS import Voice
from Imagine import ImagineVideo
from GMAILFUNC import GMAILFUNC
import conAudio

import multiprocessing
#dill.Pickler.dumps, dill.Pickler.loads = dill.dumps, dill.loads
#multiprocessing.reduction.ForkingPickler = dill.Pickler
#multiprocessing.reduction.dump = dill.dump
#multiprocessing.queues._ForkingPickler = dill.Pickler

CONFIG_FILE = "config.yml"
SAMPLE_RATE = 16000
FRAME_LENGTH = 512


class VoiceAssistant():

	def __init__(self):
		logger.info("Initialisiere VoiceAssistant...")
		self.user_profile = os.path.expanduser('~')
		logger.debug("Inititalisiere Gmail")
		self.gmail = GMAILFUNC()
				
		logger.debug("Lese Konfiguration...")
		
		global CONFIG_FILE
		with open(CONFIG_FILE, "r", encoding='utf8') as ymlfile:
			self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
		if self.cfg:
			logger.debug("Konfiguration gelesen.")
		else:
			logger.debug("Konfiguration konnte nicht gelesen werden.")
			sys.exit(1)
		self.language = self.cfg['assistant']['language']
		if not self.language:
			self.language = "de"
		logger.info("Verwende Sprache {}", self.language)
			
		logger.debug("Initialisiere Wake Word Erkennung...")
		self.wake_words = self.cfg['assistant']['wakewords']
		if not self.wake_words:
			self.wake_words = ['bumblebee']
		logger.debug("Wake Words sind {}", ','.join(self.wake_words))
		self.porcupine = pvporcupine.create(keywords=self.wake_words)
		logger.debug("Wake Word Erkennung wurde initialisiert.")
		
		logger.debug("Initialisiere Audioeingabe...")
		self.pa = pyaudio.PyAudio()
		
		self.audio_stream = self.pa.open(
			rate=self.porcupine.sample_rate,
			channels=1,
			format=pyaudio.paInt16,
			input=True,
			frames_per_buffer=self.porcupine.frame_length,
			input_device_index=0)
		logger.debug("Audiostream geöffnet.")

		logger.info("Initialisiere Sprachausgabe...")
		self.tts = Voice()
		voices = self.tts.get_voice_keys_by_language(self.language)
		if len(voices) > 0:
			logger.info('Stimme {} gesetzt.', voices[0])
			self.tts.set_voice(voices[0])
		else:
			logger.warning("Es wurden keine Stimmen gefunden.")
		logger.debug("Sprachausgabe initialisiert")
		
		logger.info("Initialisiere Imagination...")
		print(ImagineVideo)
		self.ttv = ImagineVideo()
		
		# Initialisiere Spracherkennung
		logger.info("Initialisiere Spracherkennung...")
		stt_model = Model('./vosk-model-de-0.21')
		speaker_model = SpkModel('./vosk-model-spk-0.4')
		# rec = KaldiRecognizer(model, wf.getframerate(), spk_model)
		self.rec = KaldiRecognizer(stt_model, 16000, speaker_model)
		# Hört der Assistent gerade auf einen Befehl oder wartet er auf ein Wake Word?
		self.is_listening = False
		self.imagined = True
		self.check_mail = True
		self.send_mail = False
		self.attach = []
		self.requests = []
		self.timer = 0.0
		self.record = 0
		logger.info("Initialisierung der Spracherkennung abgeschlossen.")
		self.tts.say("Die Initialisierung ist abgeschlossen.")
			
	def run(self):
		logger.info("VoiceAssistant Instanz wurde gestartet.")
		try:
			while True:
				if self.check_mail:	
					# get the Gmail API service
					self.service = self.gmail.gmail_authenticate()
					# get emails that match the query you specify
					logger.debug("Checking mails for roy.batty.assistance@gmail.com with subject 'Video Request'")
					results = self.gmail.search_messages(self.service, "Video Request")
					print(f"Found {len(results)} results.")
					# for each email matched, read it (output plain/text to console & save HTML and attachments)
					for msg in results:
						self.requests = self.gmail.read_message(self.service, msg)
					if self.requests:
						#for request in self.requests:
						logger.debug("Creating mail request:")
						print(self.requests[0][0])
						print(self.requests[1])
						interf = None
						request = self.requests[0][0].split('.')
						self.receipient = self.requests[1]
						prompt = request[0]
						for req in request:
							print(req)
						if len(request)>0:
							interf = int(request[1][0:4])
						print("Prompt: ", prompt)
						print("Requester: ", self.receipient)
						#self.service = self.gmail.gmail_authenticate()
						self.gmail.delete_messages(self.service, "Video Request")
						#self.service = None
						self.ttv = ImagineVideo()
						if interf:
							print("Interference: ", interf)
							self.vision = self.ttv.imagine(prompt, interf)
						else:
							self.vision = self.ttv.imagine(prompt)
						self.send_mail = True
						self.attach = self.vision
						self.requests = None
						request = None
						results = None
						interf = None
					self.check_mail = False
					self.timer = 0.0
					self.service = None
				else:
					self.timer+=0.001
					#print(self.timer)
				
				if self.timer>=2.0:
					self.check_mail = True
					self.timer = 0.0
					
				if self.send_mail:
					# get the Gmail API service
					self.service = self.gmail.gmail_authenticate()
					if self.receipient:
						receipient = self.receipient
					else:
						receipient = "daresan21@gmail.com"
					
					if prompt:
						subject = "AW: " + prompt
					else:
						subject = "Nachricht von Assistent Roy Batty"
					
					if self.attach:
						attach = os.path.join(self.attach)
						print("Path: ", attach)
						try:
							self.gmail.send_message(self.service, receipient, subject, 
									"Hello Daniel! Das habe ich mir vorgestellt. LG, Roy", [attach])
						except Exception as error:
							logger.debug("Ein Fehler beim Senden ist aufgetreten!", error.message, " Args: ", error.args )
							self.gmail.send_message(self.service, receipient, subject, 
								"Hello Daniel! Ich konnte das File leider nicht senden. Zum Trost sende ich Dir ein Anderes! LG, Roy", ["imagined_Video_ein_drache_0.mp4"])
						finally:
							logger.debug('Beende Versand...')
							self.attach = None
							subject = None
							self.receipient = None
							self.prompt = None
							receipient = None
					else:
						logger.debug("Nichts zu versenden!")
					self.send_mail = False
					self.service = None
					#self.check_mail = True
			
				pcm = self.audio_stream.read(self.porcupine.frame_length)
				pcm_unpacked = struct.unpack_from("h" * self.porcupine.frame_length, pcm)		
				keyword_index = self.porcupine.process(pcm_unpacked)
				if keyword_index >= 0:
					logger.info("Wake Word {} wurde verstanden.", self.wake_words[keyword_index])
					self.is_listening = True
					self.imagined = False
					
				# Spracherkennung
				if self.is_listening:
					if self.rec.AcceptWaveform(pcm):
						recResult = json.loads(self.rec.Result())
						
						# Hole das Resultat aus dem JSON Objekt
						sentence = recResult['text']

						logger.info("Initialisiere Sprachausgabe...")
						self.tts = Voice()
						voices = self.tts.get_voice_keys_by_language(self.language)
						if len(voices) > 0:
							logger.info('Stimme {} gesetzt.', voices)
							self.tts.set_voice(voices[0])
						else:
							logger.warning("Es wurden keine Stimmen gefunden.")
						
						print(sentence.lower()[0:8])
						if sentence.lower()[0:8] in ["kalliope", "calliope"]:
						#if sentence.lower().startswith("kalliope"):
							sentence = sentence [8:] # Schneide Kalliope am Anfang des Satzes weg
							sentence = sentence.strip() # Entferne Leerzeichen am Anfang und Ende des Satzes
							logger.info("Befehl Kalliope verstanden. Dein Satz: {}.", sentence)
							self.imagined = True
							#logger.debug('Ich habe verstanden "{}"', sentence)
							
						if sentence.lower()[0:8] in ["diktat", "aufnahme"]:
							logger.info("Befehl Diktat/Aufnahme verstanden. Dein Satz: {}.", sentence)
							input('Warte auf Text (Enter drücken, wenn Text in Zwischenablage)')
							text = pyperclip.paste()
							#result = self.split_text(text)
							self.record = 1
							print(text)
							#for sentence in result:
							#	sentence = sentence.strip()
							#	self.tts.say(sentence, self.record)
							self.tts.say(text, self.record)
							out_folder = "documents\\audio_output"
							folder_path = os.path.join(self.user_profile, out_folder)
							#folder_path = r"C:\Users\taffe\audio_output\"  # Replace with your actual folder path
							output_file = "concatenated_audio.wav"
							conAudio.concatenate_audio_wave(folder_path, output_file)
							self.record = 0
						
						if self.imagined:
							print("Jetzt stelle ich es mir vor...")
							self.ttv = ImagineVideo()
							self.vision = self.ttv.imagine(sentence)
							send = input("Soll ich es per Mail verschicken?")
							if send in ["y", "Y", "yes", "Yes", "YES"]:
								self.send_mail = True
								self.attach = self.vision
								logger.debug("Preparing Attachment")
								print(self.attach)
								#self.vision = None
								
							self.imagined = False
							self.tts.say("Ich habe mir '" + sentence + "' vorgestellt.")
						else:
							logger.debug('Ich habe verstanden "{}"', sentence)
						
						self.is_listening = False
					
		except KeyboardInterrupt:
			logger.debug("Per Keyboard beendet")
		finally:
			logger.debug('Beginne Aufräumarbeiten...')
			if self.porcupine:
				self.porcupine.delete()
				
			if self.audio_stream is not None:
				self.audio_stream.close()
				
			if self.pa is not None:
				self.pa.terminate()

if __name__ == '__main__':
	multiprocessing.set_start_method('spawn')

	va = VoiceAssistant()
	logger.info("Anwendung wurde gestartet")
	va.run()			