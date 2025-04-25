from loguru import logger
import yaml
import time
import pyaudio
import pvporcupine
import struct
import os
import sys

from vosk import Model, SpkModel, KaldiRecognizer
import json
import text2numde 

from TTS import Voice
from Imagine import ImagineVideo
from GMAILFUNC import GMAILFUNC
import multiprocessing

CONFIG_FILE = "config.yml"

sys.path.append(os.path.dirname(__file__))
print(os.path.dirname(__file__))

SAMPLE_RATE = 16000
FRAME_LENGTH = 512

class VoiceAssistant():

	def __init__(self):
		logger.info("Inititalisiere Gmail")
		self.gmail = GMAILFUNC()
		
		logger.info("Initialisiere VoiceAssistant...")
		
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
			logger.info('Stimme {} gesetzt.', voices)
			self.tts.set_voice(voices[0])
		else:
			logger.warning("Es wurden keine Stimmen gefunden.")
		# self.tts.say("Initialisierung abgeschlossen")
		logger.debug("Sprachausgabe initialisiert")
		
		# Initialisiere Imagination
		logger.info("Initialisiere Imagination...")
		print(ImagineVideo)
		self.ttv = ImagineVideo()
		self.imagined = True

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
		logger.info("Initialisierung der Spracherkennung abgeschlossen.")
		self.tts.say("Die Initialisierung ist abgeschlossen.")
			
	def run(self):
		logger.info("VoiceAssistant Instanz wurde gestartet.")
		
		try:
			while True:
				if self.check_mail:
					# get the Gmail API service
					service = self.gmail.gmail_authenticate()
					# test send email
					self.gmail.send_message(service, "daresan21@gmail.com", "Message from Roy Batty Assistant.", 
								"Hello Daniel! This is your AI Assistant Roy Batty. Have a nice day! Yours, Roy", ["TTS.py", "main_06.py"])
				
					# get emails that match the query you specify
					results = self.gmail.search_messages(service, "Simsalabim")
					print(f"Found {len(results)} results.")
					# for each email matched, read it (output plain/text to console & save HTML and attachments)
					for msg in results:
						self.gmail.read_message(service, msg)
					self.check_mail = False
			
				pcm = self.audio_stream.read(self.porcupine.frame_length)
				pcm_unpacked = struct.unpack_from("h" * self.porcupine.frame_length, pcm)		
				keyword_index = self.porcupine.process(pcm_unpacked)
				if keyword_index >= 0:
					logger.info("Wake Word {} wurde verstanden.", self.wake_words[keyword_index])
					self.is_listening = True
					self.imagined = False
				
				# Spracherkennung
				if self.is_listening:
						logger.info("Initialisiere Sprachausgabe...")
						self.tts = Voice()
						voices = self.tts.get_voice_keys_by_language(self.language)
						if len(voices) > 0:
							logger.info('Stimme {} gesetzt.', voices)
							self.tts.set_voice(voices[0])
						else:
							logger.warning("Es wurden keine Stimmen gefunden.")
				
				if self.rec.AcceptWaveform(pcm):
					recResult = json.loads(self.rec.Result())
						
					# Hole das Resultat aus dem JSON Objekt
					sentence = recResult['text']			
					if sentence.lower().startswith("kalliope"):
						sentence = sentence [8:] # Schneide Kalliope am Anfang des Satzes weg
						sentence = sentence.strip() # Entferne Leerzeichen am Anfang und Ende des Satzes
						logger.info("Befehl Kalliope verstanden. Dein Satz: {}.", sentence)
						self.imagined = True
						#logger.debug('Ich habe verstanden "{}"', sentence)
						
					if self.imagined:
						print("Jetzt stelle ich es mir vor...")
						self.ttv = ImagineVideo()
						self.ttv.imagine(sentence)
						self.imagined = False
						self.tts.say("Ich habe mir '" + sentence + "' vorgestellt.")
					else:
						logger.debug('Ich habe verstanden "{}"', sentence)
					
					self.is_listening = False
					
		except KeyboardInterrupt:
			logger.debug("Per Keyboard beendet")
		finally:
			logger.debug('Beginne Aufräumarbeiten...')
				
			if self.audio_stream is not None:
				self.audio_stream.close()
				
			if self.pa is not None:
				self.pa.terminate()
			
			if self.tts is not None:
				self.tts.stop()

if __name__ == '__main__':
	multiprocessing.freeze_support()
	sys.stdout = open('x.out', 'a')
	sys.stderr = open('x.err', 'a')
	multiprocessing.set_start_method('spawn')

	va = VoiceAssistant()
	logger.info("Anwendung wurde gestartet")
	va.run()				