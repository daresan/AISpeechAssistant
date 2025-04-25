from loguru import logger
import yaml
import time
import sys
#import sounddevice as sd
import pvporcupine
import pyaudio
import struct
import os


from TTS import Voice
import multiprocessing

CONFIG_FILE = "config.yml"

class VoiceAssistant():

	def __init__(self):
		logger.info("Initialisiere VoiceAssistant...")
		
		# Lese Konfigurationsdatei
		logger.debug("Lese Konfiguration...")
		
		# Verweise lokal auf den globalen Kontext und hole die Variable CONFIG_FILE
		global CONFIG_FILE
		with open(CONFIG_FILE, "r", encoding='utf8') as ymlfile:
			# Lade die Konfiguration im YAML-Format
			self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
		if self.cfg:
			logger.debug("Konfiguration gelesen.")
		else:
			# Konnto keine Konfiguration gefunden werden? Dann beende die Anwendung
			logger.debug("Konfiguration konnte nicht gelesen werden.")
			sys.exit(1)
		language = self.cfg['assistant']['language']
		if not language:
			language = "de"
		logger.info("Verwende Sprache {}", language)
			
		# Initialisiere Wake Word Detection
		logger.debug("Initialisiere Wake Word Erkennung...")
		
		# Lies alle wake words aus der Konfigurationsdatei
		self.wake_words = self.cfg['assistant']['wakewords']
		
		# Wird keins gefunden, nimm 'bumblebee'
		if not self.wake_words:
			self.wake_words = ['bumblebee']
		logger.debug("Wake Words sind {}", ','.join(self.wake_words))
		self.porcupine = pvporcupine.create(keywords=self.wake_words)
		# Sensitivities (sensitivities=[0.6, 0.35]) erweitert oder schränkt
		# den Spielraum bei der Intepretation der Wake Words ein
		logger.debug("Wake Word Erkennung wurde initialisiert.")
		
		# Initialisiere Audio stream
		logger.debug("Initialisiere Audioeingabe...")
		self.pa = pyaudio.PyAudio()
		
		# Liste alle Audio Devices auf
		for i in range(self.pa.get_device_count()):
			logger.debug('id: {}, name: {}', self.pa.get_device_info_by_index(i).get('index'),
				self.pa.get_device_info_by_index(i).get('name'))
		
		# Initialisiere TTS
		logger.info("Initialisiere Sprachausgabe...")
		self.tts = Voice()
		# self.tts.set_voice('Daniel-germanvoice-DE-de')
		voices = self.tts.get_voice_keys_by_language(language)
		if len(voices) > 0:
			logger.info('Stimme {} gesetzt.', voices)
			self.tts.set_voice(voices[0])
		else:
			logger.warning("Es wurden keine Stimmen gefunden.")
		# 
		# self.tts.say("Die Initialisierung ist abgeschlossen.")
		logger.debug("Sprachausgabe initialisiert")
		
		# Wir öffnen einen (mono) Audio-Stream, der Audiodaten einer bestimmten Länge
		# von einem bestimmten Device einliest.
		self.audio_stream = self.pa.open(
			rate=self.porcupine.sample_rate,
			channels=1,
			format=pyaudio.paInt16,
			input=True,
			frames_per_buffer=self.porcupine.frame_length,
			input_device_index=0)
		logger.debug("Audiostream geöffnet.")
		
	def run(self):
		logger.info("Anwendung wurde gestartet. Warte auf Eingabe.")
		language = self.cfg['assistant']['language']
		# Versuche folgenden Code auszuführen. Sollte eine Ausnahme auftreten, wird der except Block behandelt.
		try:
			while True:
				pcm = self.audio_stream.read(self.porcupine.frame_length)
				pcm_unpacked = struct.unpack_from("h" * self.porcupine.frame_length, pcm)		
				keyword_index = self.porcupine.process(pcm_unpacked)
				if keyword_index >= 0:
					info = "Das Aufweckwort " + self.wake_words[keyword_index] + " wurde erkannt."
					#logger.info("Wake Word {} wurde erkannt.", self.wake_words[keyword_index])
					# Initialisiere TTS
					#logger.info("Initialisiere Sprachausgabe...")
					self.tts = Voice()
					# self.tts.set_voice('Daniel-germanvoice-DE-de')
					voices = self.tts.get_voice_keys_by_language(language)
					if len(voices) > 0:
						logger.info('Stimme {} gesetzt.', voices)
						self.tts.set_voice(voices[0])
					else:
						logger.warning("Es wurden keine Stimmen gefunden.")
					self.tts.say(info)
					logger.info(info)
					logger.info("Bereit für Eingabe.")
					#logger.debug("Sprachausgabe initialisiert")
					
					
		# Der Except Block ist hier in seiner Behandlung eingeschränkt auf den Typ KeyboardInterrupt,
		# also falls der Benutzer die Ausführung des Programms mit STRG+C unterbricht.
		except KeyboardInterrupt:
			logger.debug("Per Keyboard beendet")
		# Egal ob erfolgreicher Durchlauf oder Exception: Finally wird am Ende dieses Blocks ausgeführt.
		# Das erlaubt uns die Fehlerbehandlung und das Aufräumen von Ressourcen.
		finally:
			logger.debug('Beginne Aufräumarbeiten...')
			if self.porcupine:
				self.porcupine.delete()
				
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

	# VoiceAssistant muss außerhalb des try-except-finally Blocks initialisiert werden,
	# da die Instanz sonst nicht in finally bekannt ist.
	va = VoiceAssistant()
	va.run()