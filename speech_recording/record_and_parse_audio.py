import subprocess
from pathlib import Path

from speech_recording.split_transcript import split_transcript
from speech_recording.transcribe_and_summarize import summary_chain, summarize, transcribe
import time
import threading
import numpy as np
from queue import Queue



class FFmpegRecorder:
    def __init__(self):
        self.process = None
        self.transcription = ''
        self.ffmpeg = Path(
            r"C:\ffmpeg\ffmpeg-9.0-essentials_build\bin\ffmpeg.exe"
        )
        # self.output_dir = Path("recordings")
        # self.output_dir.mkdir(exist_ok=True)
        # self.thread = None
        self.segment_queue = Queue()
        self.thread1 = None
        self.thread2 = None
        self.transcript_complete = False
        self.audio_mode = None
        self.summary_complete = False
        self.language = 'en'


    def update_transcript(self, language = 'en'):
        while True:
            print('Updating transcript')
            buffer = self.segment_queue.get()
            if buffer is None:
                self.transcript_complete = True
                break
            transcript = transcribe(buffer, language)
            self.transcription += " " + transcript

    def extract_audio_chunks(self):
        while self.process:
            print('Start chunking')
            current_segment = bytearray()
            if self.audio_mode == 'System Sound':
                THRESHOLD = 200
            elif self.audio_mode == 'Mic':
                THRESHOLD = 50
            while self.process:
                print('start reading audio bytes')
                if self.process is not None:
                    pcm = self.process.stdout.read(3200)
                    if not pcm:
                        break
                    current_segment.extend(pcm)

                    seconds = len(current_segment) / 32000
                    print('Check if 3 seconds has crossed')
                    if seconds > 3:
                        print('3 seconds crossed')
                        # Detect silence
                        samples = np.frombuffer(pcm, dtype=np.int16)
                        rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
                        print(f'RMS of current sample: {rms}')
                        if rms < THRESHOLD:
                            print('Current sample is silent')
                            #Silent
                            full_samples = np.frombuffer(current_segment, dtype=np.int16).copy()
                            entire_rms = np.sqrt(np.mean(full_samples.astype(np.float32) ** 2))
                            print('Check if full segment was silent')
                            if entire_rms < THRESHOLD:
                                print('full segment was silent')
                                print('re-initializing current segment')
                                current_segment = bytearray()
                                print('continuing the current loop')
                                continue
                            else:
                                print('Full segment NOT silent')
                                print('Push current segment to queue')
                                audio_chunk = full_samples.astype(np.float32) / 32768.0
                                self.segment_queue.put(audio_chunk)
                                print('Re-initializing current segment and continue loop')
                                current_segment = bytearray()
                                continue
                        else:
                            print('Current sample was NOT silent, Continue loop')
                            continue
                    else:
                        print('3 seconds mark has not crossed, continue')
                        continue

            if len(current_segment) > 0:
                full_samples = np.frombuffer(
                    current_segment,
                    dtype=np.int16
                ).copy()

                audio_chunk = full_samples.astype(np.float32) / 32768.0

                self.segment_queue.put(audio_chunk)
            self.segment_queue.put(None)
            break

    def start(self, audio_mode, language_selected):
        if self.process:
            yield ("Already recording", '', '')
            return

        self.transcription = ""
        self.transcript_complete = False
        self.segment_queue = Queue()

        self.audio_mode = audio_mode
        print(f'Selected audio mode: {self.audio_mode}')


        language = 'en'
        if language_selected == 'English':
            language = 'en'
        elif language_selected == 'Kannada':
            language = 'kn'
        elif language_selected == 'Telugu':
            language = 'te'
        elif language_selected == 'Hindi':
            language = 'hi'



        if audio_mode == 'System Sound':
            self.process = subprocess.Popen(
                [
                    str(self.ffmpeg),

                    "-f", "dshow",
                    "-i", "audio=CABLE Output (VB-Audio Virtual Cable)",

                    # Output format
                    "-f", "s16le",  # Signed 16-bit PCM
                    "-ac", "1",  # Mono
                    "-ar", "16000",  # 16 kHz sample rate

                    "-"  # "-" means stdout
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        elif audio_mode == 'Mic':
            self.process = subprocess.Popen(
                [
                    str(self.ffmpeg),

                    "-f", "dshow",
                    "-i", "audio=Microphone Array (Qualcomm(R) Aqstic(TM) ACX Static Endpoints Audio Device)",

                    # Output format
                    "-f", "s16le",  # Signed 16-bit PCM
                    "-ac", "1",  # Mono
                    "-ar", "16000",  # 16 kHz sample rate

                    "-"  # "-" means stdout
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )

        self.thread1 = threading.Thread(
            target=self.extract_audio_chunks,
            daemon=True
        )
        self.thread1.start()

        self.thread2 = threading.Thread(
            target=self.update_transcript,
            args=(self.language,),
            daemon=True
        )
        self.thread2.start()

        last_transcript = ""

        while not self.transcript_complete:

            if self.transcription != last_transcript:
                last_transcript = self.transcription

                yield (
                    "Recording and transcribing...",
                    self.transcription,
                    ""
                )

            time.sleep(0.2)

        return (
            "Recording and transcribing completed",
            self.transcription,
            ""
        )



    def stop(self):
        # self.segment_queue.put(None)
        if self.process:
            self.process.stdin.write(b"q\n")
            self.process.stdin.flush()
            self.process.wait()
            self.process = None

        if self.thread2:
            self.thread2.join()

        if self.thread1:
            self.thread1.join()

        self.segment_queue = Queue()





recorder = FFmpegRecorder()



def stop_recording():
    print("Stop clicked")
    recorder.stop()
    return ("Transcripting complete", "Click the 'Generate Summary' button to generate Summary")

def generate_summary(transcript):
    if not recorder.summary_complete:
        yield ("Generating summary...", "Generating summary...")

        full_summary = ""

        for transcript_chunk in split_transcript(transcript):
            for output_chunk in summarize(transcript_chunk):
                full_summary += output_chunk
                yield ("Generating summary...", full_summary)

        print(f'Full Summary: \n {full_summary}')
        recorder.transcript_complete = True
        recorder.transcription = ''
        yield ("Summarizing Completed.", full_summary)



