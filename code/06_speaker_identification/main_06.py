from loguru import logger
import yaml
import time
import pvporcupine
import pyaudio
import struct
import os
import sys
from vosk import Model, SpkModel, KaldiRecognizer
import json

import tinydb
import numpy as np
from usermgmt import UserMgmt

from TTS import Voice
from GMAILFUNC import GMAILFUNC
import multiprocessing

CONFIG_FILE = "config.yml"

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
		language = self.cfg['assistant']['language']
		if not language:
			language = "de"
		logger.info("Verwende Sprache {}", language)
			
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
		voices = self.tts.get_voice_keys_by_language(language)
		if len(voices) > 0:
			logger.info('Stimme {} gesetzt.', voices[0])
			self.tts.set_voice(voices[0])
		else:
			logger.warning("Es wurden keine Stimmen gefunden.")
		self.tts.say("Initialisierung abgeschlossen")
		logger.debug("Sprachausgabe initialisiert")
		
		logger.info("Initialisiere Spracherkennung...")
		stt_model = Model('./vosk-model-de-0.21')
		speaker_model = SpkModel('./vosk-model-spk-0.4')
		self.rec = KaldiRecognizer(stt_model, 16000, speaker_model)
		self.is_listening = False
		logger.info("Initialisierung der Spracherkennung abgeschlossen.")
		
		# Initialisiere die Benutzerverwaltung
		logger.info("Initialisiere Benutzerverwaltung...")
		self.user_management = UserMgmt(init_dummies=True)
		self.allow_only_known_speakers = self.cfg["assistant"]["allow_only_known_speakers"]
		logger.info("Benutzerverwaltung initialisiert")
	
	# Finde den besten Sprecher aus der Liste aller bekannter Sprecher aus dem User Management
	def __detectSpeaker__(self, input):
		bestSpeaker = None
		bestCosDist = 100
		for speaker in self.user_management.speaker_table.all():
			# Die Cosinus-Ähnlichkeit interpretiert das Muster des gespeicherten Sprechers
			# und des aktuellen Sprechers als Vektor und berechnet deren Distanz über
			# den Cosinus-Winkel zwischen den Vektoren. Je kleiner der Winkel, desto ähnlicher
			# sind die beiden Stimmen. Der Wert liegt immer zwischen 0.0 und 1.0 wobei 0.0 eine
			# absolute Ähnlichkeit bedeutet. Wir setzen 0.3 als Schwelle für die Ähnlichkeit
			# gemäß MUP (Methode des unbekümmerten Probierens).
			nx = np.array(speaker.get('voice'))
			ny = np.array(input)
			cosDist = 1 - np.dot(nx, ny) / np.linalg.norm(nx) / np.linalg.norm(ny)
			if (cosDist < bestCosDist):
				if (cosDist < 0.3):
					bestCosDist = cosDist
					bestSpeaker = speaker.get('name')
		return bestSpeaker		
			
	def run(self):
		check_mail = True
		logger.info("VoiceAssistant Instanz wurde gestartet.")
		try:
			while True:
				if check_mail:
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
					check_mail = False
			
				pcm = self.audio_stream.read(self.porcupine.frame_length)
				pcm_unpacked = struct.unpack_from("h" * self.porcupine.frame_length, pcm)		
				keyword_index = self.porcupine.process(pcm_unpacked)
				if keyword_index >= 0:
					logger.info("Wake Word {} wurde verstanden.", self.wake_words[keyword_index])
					self.is_listening = True
					
				# Spracherkennung
				if self.is_listening:
					if self.rec.AcceptWaveform(pcm):
						recResult = json.loads(self.rec.Result())
						
						# Hole den Namen des Sprechers falls bekannt.
						speaker = self.__detectSpeaker__(recResult['spk'])
						
						# Zeige den "Fingerabdruck" deiner Stimme. Speichere diesen und füge
						# ihn mit einer neuen ID in users.json ein, die nach dem ersten Aufruf
						# im Projektverzeichnis erstellt wird.
						logger.debug('Deine Stimme sieht so aus {}', recResult['spk'])
						
						# Sind nur bekannte sprecher erlaubt?
						if (speaker == None) and (self.allow_only_known_speakers == True):
							logger.info("Ich kenne deine Stimme nicht und darf damit keine Befehle von dir entgegen nehmen.")
							self.current_speaker = None
						else:
							if speaker:
								logger.debug("Sprecher ist {}", speaker)
							self.current_speaker = speaker
							self.current_speaker_fingerprint = recResult['spk']
							sentence = recResult['text']
							logger.debug('Ich habe verstanden "{}"', sentence)
							self.is_listening = False
							self.current_speaker = None
					
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